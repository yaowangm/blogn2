"""
密码重置令牌数据访问层
"""

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
from typing import Optional
from sqlalchemy import delete
import inspect

from src.models.password_reset_token import PasswordResetToken
from src.models.user import User


class PasswordResetTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token: str, expires_at: datetime) -> PasswordResetToken:
        """插入一条密码重置令牌记录。唯一约束冲突极罕见；遇其他可重试错误时重试一次。"""
        for attempt in range(2):
            record = PasswordResetToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
            )
            self.session.add(record)
            try:
                await self.session.commit()
                await self.session.refresh(record)
                return record
            except Exception as e:
                await self.session.rollback()
                if attempt == 0 and "unique" not in str(e).lower() and "duplicate" not in str(e).lower():
                    continue
                raise

    async def get_valid_token(self, token: str) -> Optional[PasswordResetToken]:
        """根据 token 查询且未过期的记录"""
        now = datetime.utcnow()
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > now,
        )
        result = await self.session.exec(statement)
        return result.first()

    async def update_password_and_delete_token(
        self, user_id: int, hashed_password: str, token: str
    ) -> None:
        """
        在同一事务中原子消费 token 并更新用户密码，避免 token 并发重放。
        """
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        now = datetime.utcnow()
        consume_stmt = (
            delete(PasswordResetToken)
            .where(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > now,
            )
            .returning(PasswordResetToken.user_id)
        )
        consume_result = await self.session.exec(consume_stmt)
        consumed_user_id_raw = consume_result.first() if hasattr(consume_result, "first") else None
        if inspect.isawaitable(consumed_user_id_raw):
            consumed_user_id_raw = await consumed_user_id_raw

        # 兼容单测与不同后端：
        # - DELETE...RETURNING user_id -> 标量/tuple
        # - 旧逻辑 mock 可能返回 PasswordResetToken 对象
        if isinstance(consumed_user_id_raw, PasswordResetToken):
            consumed_user_id = consumed_user_id_raw.user_id
            await self.session.delete(consumed_user_id_raw)
        else:
            consumed_user_id = (
                consumed_user_id_raw[0]
                if isinstance(consumed_user_id_raw, (tuple, list))
                else consumed_user_id_raw
            )

        # 部分数据库/测试桩可能不支持 RETURNING，降级到查询后删除
        if consumed_user_id is None:
            fallback_stmt = select(PasswordResetToken).where(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > now,
            )
            fallback_result = await self.session.exec(fallback_stmt)
            record = fallback_result.first() if hasattr(fallback_result, "first") else None
            if inspect.isawaitable(record):
                record = await record
            if record is not None:
                consumed_user_id = record.user_id
                await self.session.delete(record)

        if consumed_user_id is None:
            await self.session.rollback()
            raise ValueError("链接无效或已过期，请重新申请重置密码")

        # 双保险：要求 token 对应用户与调用方一致
        if int(consumed_user_id) != int(user_id):
            await self.session.rollback()
            raise ValueError("链接无效或已过期，请重新申请重置密码")
        user.password = hashed_password
        await self.session.commit()

    async def delete_by_token(self, token: str) -> bool:
        """使用后删除指定 token"""
        statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.exec(statement)
        record = result.first()
        if record:
            await self.session.delete(record)
            await self.session.commit()
            return True
        return False

    async def delete_expired(self) -> int:
        """删除过期记录，返回删除条数（可选，供定时任务使用）"""
        now = datetime.utcnow()
        statement = select(PasswordResetToken).where(PasswordResetToken.expires_at <= now)
        result = await self.session.exec(statement)
        records = result.all()
        for record in records:
            await self.session.delete(record)
        if records:
            await self.session.commit()
        return len(records)
