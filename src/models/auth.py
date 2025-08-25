"""
认证相关的数据模型
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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

class LogoutResponse(BaseModel):
    """登出响应模型"""
    message: str = "登出成功"

class AuthError(BaseModel):
    """认证错误模型"""
    detail: str
    error_code: Optional[str] = None
