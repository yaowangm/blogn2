"""
认证相关的数据模型
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

from src.utils.password_validation import validate_password as validate_password_rules

class LoginRequest(BaseModel):
    """登录请求模型"""
    username_or_email: str
    password: str

class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 访问令牌过期时间（秒，由后端计算）
    user: dict

class TokenRefreshRequest(BaseModel):
    """令牌刷新请求模型"""
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    """令牌刷新响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    name: str
    email: str
    state: int
    role: str
    lastupdate: Optional[datetime] = None
    iplog: Optional[str] = None
    avatar_url: Optional[str] = None

class LogoutResponse(BaseModel):
    """登出响应模型"""
    message: str = "登出成功"

class AuthError(BaseModel):
    """认证错误模型"""
    detail: str
    error_code: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """忘记密码（申请重置）请求"""
    email: str


class ForgotPasswordResponse(BaseModel):
    """忘记密码（申请重置）响应"""
    message: str = "若该邮箱已注册，将收到重置邮件"


class ResetPasswordRequest(BaseModel):
    """执行重置密码请求"""
    token: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v: str) -> str:
        validate_password_rules(v or "")
        return v


class ResetPasswordResponse(BaseModel):
    """执行重置密码响应"""
    message: str = "密码重置成功"


class ValidateResetTokenResponse(BaseModel):
    """校验重置 token 响应"""
    valid: bool
