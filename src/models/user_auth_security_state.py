"""
用户认证安全状态（按 user_id + 操作类型单行聚合）

与 doc/AUTH_SECURITY_USER_STATE_DB_DESIGN.md 一致。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, ForeignKey, UniqueConstraint
from sqlmodel import Field, SQLModel


class AuthSecurityOptType:
    """与 user_auth_security_state.opt_type 取值一致"""

    LOGIN = "login"
    FORGOT_PASSWORD = "forgot_password"
    VALIDATE_RESET_TOKEN = "validate_reset_token"
    RESET_PASSWORD = "reset_password"
    REGISTER = "register"


class UserAuthSecurityState(SQLModel, table=True):
    __tablename__ = "user_auth_security_state"
    __table_args__ = (
        UniqueConstraint("user_id", "opt_type", name="uq_user_auth_security_state_user_opt"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger(),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    opt_type: str = Field(max_length=32, description="操作类型")
    fail_count: int = Field(default=0, ge=0, description="窗口内失败或广义计数")
    window_start: datetime = Field(description="当前计数窗口起点（UTC）")
    next_allowed_at: datetime = Field(description="最早允许再试（UTC）")
