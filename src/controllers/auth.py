"""
认证API控制器
提供用户登录、登出、令牌刷新等认证功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from datetime import timedelta
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest,
    TokenRefreshResponse, LogoutResponse, UserInfo,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ValidateResetTokenResponse,
)
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.password_reset_service import PasswordResetService
from src.repositories.password_reset_token_repository import PasswordResetTokenRepository
from src.utils.dependencies import get_user_service
from src.utils.error_handlers import handle_api_errors
from src.database import get_async_session

# 创建认证API路由器
router = APIRouter(prefix="/auth", tags=["认证"])

# 安全方案
security = HTTPBearer()

# 获取JWT密钥（从环境变量）
import os
JWT_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

def get_auth_service(user_service: UserService = Depends(get_user_service)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(user_service.user_repo, JWT_SECRET_KEY)


def get_password_reset_service(
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session),
) -> PasswordResetService:
    """获取密码重置服务实例"""
    token_repo = PasswordResetTokenRepository(session)
    return PasswordResetService(user_service.user_repo, token_repo, auth_service)

@router.post("/login", response_model=LoginResponse)
@handle_api_errors("登录失败")
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    http_request: Request = None
):
    """
    用户登录
    
    Args:
        request: 登录请求数据
        auth_service: 认证服务实例
        http_request: HTTP请求对象（用于获取客户端IP）
        
    Returns:
        LoginResponse: 登录成功响应，包含访问令牌和刷新令牌
        
    Raises:
        HTTPException: 当用户名/密码错误或账户被冻结时
    """
    # 获取客户端IP地址
    client_ip = http_request.client.host if http_request else "unknown"
    
    # 验证用户凭据
    user = await auth_service.authenticate_user(
        request.username_or_email, 
        request.password, 
        client_ip
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 准备用户数据
    user_data = {
        "user_id": user.id,
        "username": user.name,
        "role": "admin" if user.state == 10 else "user"
    }
    
    # 生成令牌
    access_token = auth_service.create_access_token(user_data)
    refresh_token = auth_service.create_refresh_token(user_data)
    
    # 准备用户信息
    user_info = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "state": user.state,
        "role": "admin" if user.state == 10 else "user",
        "lastupdate": user.lastupdate,
        "iplog": user.iplog,
        "avatar_url": None  # 不设置默认头像，让前端处理
    }
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user_info
    )

@router.post("/logout", response_model=LogoutResponse)
@handle_api_errors("登出失败")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登出
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        
    Returns:
        LogoutResponse: 登出成功响应
    """
    # 这里可以添加令牌黑名单逻辑
    # 目前只是简单的响应，实际应用中可能需要将令牌加入黑名单
    
    return LogoutResponse(message="登出成功")

@router.get("/me", response_model=UserInfo)
@handle_api_errors("获取用户信息失败")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取当前登录用户信息
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        user_service: 用户服务实例
        
    Returns:
        UserInfo: 当前用户信息
        
    Raises:
        HTTPException: 当令牌无效或用户不存在时
    """
    # 验证令牌
    user_data = auth_service.get_user_from_token(credentials.credentials)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    # 获取用户详细信息
    user = await user_service.get_user_by_id(user_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 生成头像URL
    avatar_url = None
    if user.id:
        from src.config.app import validate_app_config
        config = validate_app_config()
        avatar_dir = config["avatar_dir"]
        
        prefix = (user.id // 10000) + 1
        avatar_path = f"/avatar/{prefix}/s_{user.id}.jpg"
        real_path = os.path.join(avatar_dir, str(prefix), f"s_{user.id}.jpg")
        
        # 检查文件是否存在
        if os.path.exists(real_path):
            avatar_url = avatar_path
    
    return UserInfo(
        id=user.id,
        name=user.name,
        email=user.email,
        state=user.state,
        role="admin" if user.state == 10 else "user",
        lastupdate=user.lastupdate,
        iplog=user.iplog,
        avatar_url=avatar_url
    )

@router.get("/verify")
@handle_api_errors("令牌验证失败")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    验证访问令牌
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        
    Returns:
        Dict: 令牌验证结果
        
    Raises:
        HTTPException: 当令牌无效时
    """
    user_data = auth_service.get_user_from_token(credentials.credentials)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    return {
        "valid": True,
        "user_id": user_data["user_id"],
        "username": user_data["username"],
        "role": user_data["role"],
        "expires_at": user_data["exp"]
    }

@router.post("/refresh", response_model=TokenRefreshResponse)
@handle_api_errors("令牌刷新失败")
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    使用刷新令牌获取新的访问令牌
    
    Args:
        request: 令牌刷新请求数据
        auth_service: 认证服务实例
        
    Returns:
        TokenRefreshResponse: 新的访问令牌和刷新令牌
        
    Raises:
        HTTPException: 当刷新令牌无效时
    """
    # 使用刷新令牌获取新的访问令牌
    new_access_token = auth_service.refresh_access_token(request.refresh_token)
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    # 获取用户信息以创建新的刷新令牌
    user_data = auth_service.get_user_from_token(new_access_token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法获取用户信息"
        )
    
    # 创建新的刷新令牌
    new_refresh_token = auth_service.create_refresh_token(user_data)
    
    return TokenRefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60
    )

@router.get("/validate")
@handle_api_errors("令牌验证失败")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    验证访问令牌（简化版，用于前端检查）
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        
    Returns:
        Dict: 令牌验证结果
        
    Raises:
        HTTPException: 当令牌无效时
    """
    user_data = auth_service.get_user_from_token(credentials.credentials)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    return {"valid": True}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@handle_api_errors("申请重置失败")
async def forgot_password(
    request: ForgotPasswordRequest,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
):
    """
    申请重置密码：提交邮箱后，若该邮箱已注册则发送重置邮件；无论是否存在均返回相同提示（防枚举）。
    """
    await password_reset_service.request_reset(request.email)
    return ForgotPasswordResponse(message="若该邮箱已注册，将收到重置邮件")


@router.post("/reset-password", response_model=ResetPasswordResponse)
@handle_api_errors("重置密码失败")
async def reset_password(
    request: ResetPasswordRequest,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
):
    """
    执行重置密码：使用邮件中的 token 设置新密码。token 无效或过期返回 400。
    """
    try:
        await password_reset_service.reset_password(request.token, request.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResetPasswordResponse(message="密码重置成功")


@router.get("/validate-reset-token", response_model=ValidateResetTokenResponse)
@handle_api_errors("校验 token 失败")
async def validate_reset_token(
    token: str,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
):
    """
    校验重置 token 是否有效，供前端在展示重置表单前使用。
    """
    valid = await password_reset_service.is_token_valid(token)
    return ValidateResetTokenResponse(valid=valid)


