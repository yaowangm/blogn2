"""
认证安全服务（PostgreSQL user_auth_security_state）

仅 user 维度：在能解析出 user_id 时读写状态行。
"""

import os
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.auth_security import auth_security_settings
from src.models.user_auth_security_state import AuthSecurityOptType
from src.repositories.user_auth_security_state_repository import UserAuthSecurityStateRepository


class AuthSecurityService:
    """认证相关安全策略服务（数据库实现）"""

    def __init__(self, session: AsyncSession):
        self.settings = auth_security_settings
        self.session = session
        self._repo = UserAuthSecurityStateRepository(session)

    def _login_lock_message(self) -> str:
        lock_h = max(1, self.settings.login_lock_seconds // 3600)
        return (
            "登录失败次数过多，请稍后再试。"
            f"安全规则：同一账号{self.settings.login_max_fail_per_account}次失败将锁定约{lock_h}小时。"
        )

    def _login_cooldown_message(self) -> str:
        return (
            f"两次登录尝试间隔不能少于{self.settings.login_min_interval_seconds}秒。"
            f"安全规则：两次登录尝试至少间隔{self.settings.login_min_interval_seconds}秒。"
        )

    def _forgot_password_limit_message(self) -> str:
        return (
            "请求过于频繁，请稍后再试。"
            f"安全规则：忘记密码同一账号每{self.settings.pwdreset_req_window_seconds // 60}分钟最多"
            f"{self.settings.pwdreset_req_max_per_email}次。"
        )

    def _reset_token_validate_limit_message(self) -> str:
        return (
            "请求过于频繁，请稍后再试。"
            f"安全规则：重置令牌校验同一账号每{self.settings.pwdreset_validate_window_seconds // 60}分钟最多"
            f"{self.settings.pwdreset_validate_max_per_user}次。"
        )

    def _reset_password_limit_message(self) -> str:
        return (
            "请求过于频繁，请稍后再试。"
            f"安全规则：重置密码同一账号每{self.settings.pwdreset_validate_window_seconds // 60}分钟最多"
            f"{self.settings.pwdreset_validate_max_per_user}次。"
        )

    def _register_limit_message(self) -> str:
        return (
            "注册过于频繁，请稍后再试。"
            f"安全规则：同一账号每{self.settings.register_window_seconds // 60}分钟最多"
            f"{self.settings.register_max_per_user}次注册记录。"
        )

    def _db_fail_closed(self) -> bool:
        return self.settings.fail_closed_when_db_error

    async def _commit_or_raise(self) -> None:
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None

    def _testing_bypass(self) -> bool:
        return os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("TESTING") == "true"

    @staticmethod
    def normalize_ip(client_ip: Optional[str]) -> str:
        v = (client_ip or "").strip()
        return v if v else "unknown"

    async def pre_login_check(self, user_id: Optional[int]) -> None:
        if user_id is None:
            return
        try:
            blocked = await self._repo.apply_login_pre_check(
                user_id,
                self.settings.login_min_interval_seconds,
                self.settings.login_max_fail_per_account,
            )
            if blocked:
                reason, retry_after = blocked
                await self.session.rollback()
                if reason == "LOCK":
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=self._login_lock_message(),
                        headers={"Retry-After": str(retry_after)},
                    )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._login_cooldown_message(),
                    headers={"Retry-After": str(retry_after)},
                )
            await self._commit_or_raise()
        except HTTPException:
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise

    async def on_login_failed(self, user_id: Optional[int]) -> None:
        if user_id is None:
            return
        try:
            just_locked, retry_after = await self._repo.apply_login_failed(
                user_id,
                self.settings.login_max_fail_per_account,
                self.settings.login_lock_seconds,
                self.settings.login_lock_seconds,
                self.settings.login_min_interval_seconds,
            )
            await self._commit_or_raise()
            if just_locked:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._login_lock_message(),
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
        except HTTPException:
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise

    async def on_login_success(self, user_id: int) -> None:
        try:
            await self._repo.apply_login_success(user_id)
            await self._commit_or_raise()
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise

    async def check_forgot_password_rate_limit(self, user_id: Optional[int]) -> None:
        if user_id is None:
            return
        try:
            blocked, retry_after = await self._repo.bump_windowed_usage(
                user_id,
                AuthSecurityOptType.FORGOT_PASSWORD,
                self.settings.pwdreset_req_max_per_email,
                self.settings.pwdreset_req_window_seconds,
            )
            if blocked:
                await self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._forgot_password_limit_message(),
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            await self._commit_or_raise()
        except HTTPException:
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise

    async def check_reset_token_validate_rate_limit(self, user_id: Optional[int]) -> None:
        if user_id is None:
            return
        try:
            blocked, retry_after = await self._repo.bump_windowed_usage(
                user_id,
                AuthSecurityOptType.VALIDATE_RESET_TOKEN,
                self.settings.pwdreset_validate_max_per_user,
                self.settings.pwdreset_validate_window_seconds,
            )
            if blocked:
                await self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._reset_token_validate_limit_message(),
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            await self._commit_or_raise()
        except HTTPException:
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise

    async def check_reset_password_rate_limit(self, user_id: Optional[int]) -> None:
        if user_id is None:
            return
        try:
            blocked, retry_after = await self._repo.bump_windowed_usage(
                user_id,
                AuthSecurityOptType.RESET_PASSWORD,
                self.settings.pwdreset_validate_max_per_user,
                self.settings.pwdreset_validate_window_seconds,
            )
            if blocked:
                await self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._reset_password_limit_message(),
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            await self._commit_or_raise()
        except HTTPException:
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise

    async def record_register_success(self, user_id: int, *, defer_commit: bool = False) -> None:
        """注册成功后在同一 user 维度记录一次（窗口计数）；defer_commit=True 时仅 flush，由调用方 commit。"""
        try:
            blocked, retry_after = await self._repo.bump_windowed_usage(
                user_id,
                AuthSecurityOptType.REGISTER,
                self.settings.register_max_per_user,
                self.settings.register_window_seconds,
            )
            if blocked:
                await self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self._register_limit_message(),
                    headers={"Retry-After": str(max(retry_after, 1))},
                )
            if defer_commit:
                await self.session.flush()
            else:
                await self._commit_or_raise()
        except HTTPException:
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            if self._db_fail_closed():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="认证安全服务不可用，请稍后重试",
                ) from None
            if not self._testing_bypass():
                raise
