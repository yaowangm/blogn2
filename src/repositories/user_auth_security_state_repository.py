"""
用户认证安全状态仓储：按 (user_id, opt_type) 行级更新与 FOR UPDATE。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.user_auth_security_state import AuthSecurityOptType, UserAuthSecurityState


def utcnow() -> datetime:
    """UTC 当前时刻（timezone-aware），须与模型 DateTime(timezone=True) / PG TIMESTAMPTZ 一致。"""
    return datetime.now(timezone.utc)


class UserAuthSecurityStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _select_for_update(self, user_id: int, opt_type: str) -> Optional[UserAuthSecurityState]:
        stmt = (
            select(UserAuthSecurityState)
            .where(
                UserAuthSecurityState.user_id == user_id,
                UserAuthSecurityState.opt_type == opt_type,
            )
            .with_for_update()
        )
        res = await self.session.exec(stmt)
        return res.first()

    async def _ensure_row_locked(self, user_id: int, opt_type: str) -> UserAuthSecurityState:
        for _ in range(8):
            row = await self._select_for_update(user_id, opt_type)
            if row:
                return row
            now = utcnow()
            tbl = UserAuthSecurityState.__table__
            # 按列 ON CONFLICT，避免依赖唯一约束在库中的具体名称
            ins = (
                insert(tbl)
                .values(
                    user_id=user_id,
                    opt_type=opt_type,
                    fail_count=0,
                    window_start=now,
                    next_allowed_at=now,
                )
                .on_conflict_do_nothing(index_elements=["user_id", "opt_type"])
            )
            await self.session.execute(ins)
            await self.session.flush()
            row = await self._select_for_update(user_id, opt_type)
            if row:
                return row
        raise RuntimeError("user_auth_security_state: could not acquire row")

    async def apply_login_pre_check(
        self,
        user_id: int,
        min_interval_seconds: int,
        max_fail: int,
    ) -> Optional[Tuple[str, int]]:
        """
        若当前不可试，返回 ("LOCK"|"COOLDOWN", retry_after_seconds)；否则更新冷却并返回 None。
        """
        row = await self._ensure_row_locked(user_id, AuthSecurityOptType.LOGIN)
        now = utcnow()
        if row.next_allowed_at > now:
            delta = row.next_allowed_at - now
            retry_after = max(int(delta.total_seconds()), 1)
            if row.fail_count >= max_fail:
                return ("LOCK", retry_after)
            return ("COOLDOWN", retry_after)
        row.next_allowed_at = now + timedelta(seconds=min_interval_seconds)
        self.session.add(row)
        await self.session.flush()
        return None

    async def apply_login_failed(
        self,
        user_id: int,
        max_fail: int,
        fail_window_seconds: int,
        lock_seconds: int,
        min_interval_seconds: int,
    ) -> Tuple[bool, int]:
        """
        窗口滚动后 fail_count += 1；若 fail_count >= max_fail 则长锁。
        返回 (just_locked, retry_after_seconds)。
        """
        row = await self._ensure_row_locked(user_id, AuthSecurityOptType.LOGIN)
        now = utcnow()
        if row.window_start + timedelta(seconds=fail_window_seconds) <= now:
            row.fail_count = 0
            row.window_start = now
        row.fail_count += 1
        just_locked = False
        retry_after = min_interval_seconds
        if row.fail_count >= max_fail:
            lock_until = now + timedelta(seconds=lock_seconds)
            if row.next_allowed_at < lock_until:
                row.next_allowed_at = lock_until
            just_locked = True
            retry_after = max(int((row.next_allowed_at - now).total_seconds()), 1)
        else:
            cool = now + timedelta(seconds=min_interval_seconds)
            if row.next_allowed_at < cool:
                row.next_allowed_at = cool
            retry_after = max(int((row.next_allowed_at - now).total_seconds()), 1)
        self.session.add(row)
        await self.session.flush()
        return just_locked, retry_after

    async def apply_login_success(self, user_id: int) -> None:
        row = await self._select_for_update(user_id, AuthSecurityOptType.LOGIN)
        if not row:
            return
        now = utcnow()
        row.fail_count = 0
        row.window_start = now
        row.next_allowed_at = now
        self.session.add(row)
        await self.session.flush()

    async def bump_windowed_usage(
        self,
        user_id: int,
        opt_type: str,
        max_allowed: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """
        窗口内计数 +1；若 fail_count > max_allowed 则限流命中。
        返回 (blocked, retry_after_seconds)。
        """
        row = await self._ensure_row_locked(user_id, opt_type)
        now = utcnow()
        if row.window_start + timedelta(seconds=window_seconds) <= now:
            row.fail_count = 0
            row.window_start = now
        row.fail_count += 1
        blocked = row.fail_count > max_allowed
        retry_after = 1
        if blocked:
            window_end = row.window_start + timedelta(seconds=window_seconds)
            if row.next_allowed_at < window_end:
                row.next_allowed_at = window_end
            retry_after = max(int((row.next_allowed_at - now).total_seconds()), 1)
        self.session.add(row)
        await self.session.flush()
        return blocked, retry_after
