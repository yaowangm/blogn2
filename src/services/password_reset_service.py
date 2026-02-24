"""
密码重置服务

处理申请重置、执行重置及邮件发送。
"""

import secrets
import logging
from datetime import datetime, timedelta

from src.repositories.user_repository import UserRepository
from src.repositories.password_reset_token_repository import PasswordResetTokenRepository
from src.services.auth_service import AuthService
from src.config.app import get_base_url, get_reset_link_expire_minutes
from src.utils.email_sender import send_password_reset_email

logger = logging.getLogger(__name__)


class PasswordResetService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: PasswordResetTokenRepository,
        auth_service: AuthService,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.auth_service = auth_service

    async def request_reset(self, email: str) -> None:
        """
        申请重置密码：若邮箱已注册则生成 token、入库、发邮件；否则直接返回（防枚举）。
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return

        expire_minutes = get_reset_link_expire_minutes()
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)

        base_url = get_base_url().rstrip("/")
        reset_link = f"{base_url}/reset-password?token={token}"

        try:
            send_password_reset_email(to_email=user.email, reset_link=reset_link, username=user.name)
        except Exception as e:
            logger.exception("Failed to send password reset email to %s: %s", email, e)
            raise
        # 仅发信成功后再持久化 token，避免发信失败留下无效 token
        await self.token_repo.create(user_id=user.id, token=token, expires_at=expires_at)

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        使用 token 重置密码：校验 token，更新密码，删除 token。
        若 token 无效或过期则抛出 ValueError。
        """
        record = await self.token_repo.get_valid_token(token)
        if not record:
            raise ValueError("链接无效或已过期，请重新申请重置密码")

        hashed = self.auth_service.hash_password(new_password)
        # 更新密码与删除 token 在同一事务中，避免密码已改但 token 未删导致可重复使用
        await self.token_repo.update_password_and_delete_token(
            user_id=record.user_id, hashed_password=hashed, token=token,
        )

    async def is_token_valid(self, token: str) -> bool:
        """检查 token 是否有效且未过期"""
        record = await self.token_repo.get_valid_token(token)
        return record is not None
