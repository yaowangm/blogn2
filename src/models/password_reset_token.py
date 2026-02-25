"""
密码重置令牌模型

用于邮件重置密码功能的一次性令牌存储。
"""

from sqlmodel import Field
from typing import Optional
from datetime import datetime

from src.models.base import BaseModel


class PasswordResetToken(BaseModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", description="用户 ID")
    token: str = Field(max_length=64, unique=True, index=True, description="一次性令牌")
    expires_at: datetime = Field(description="过期时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
