"""
认证API控制器
提供用户登录、登出、令牌刷新等认证功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from datetime import timedelta

from src.models.auth import (
    LoginRequest, LoginResponse, TokenRefreshRequest, 
    TokenRefreshResponse, LogoutResponse, UserInfo
)
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.utils.dependencies import get_user_service
from src.utils.error_handlers import handle_api_errors

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
        "avatar_url": f"/avatar/1/s_{user.id}.jpg"  # 添加头像路径
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
    
    return UserInfo(
        id=user.id,
        name=user.name,
        email=user.email,
        state=user.state,
        role="admin" if user.state == 10 else "user",
        lastupdate=user.lastupdate,
        iplog=user.iplog
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


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Optional[UserInfo]:
    """
    获取当前登录用户信息（可选）
    如果用户未登录或令牌无效，返回None而不是抛出异常
    
    Args:
        credentials: HTTP认证凭据（可选）
        auth_service: 认证服务实例
        user_service: 用户服务实例
        
    Returns:
        Optional[UserInfo]: 当前用户信息，如果未登录则返回None
    """
    if not credentials:
        return None
    
    try:
        # 验证令牌
        user_data = auth_service.get_user_from_token(credentials.credentials)
        if not user_data:
            return None
        
        # 获取用户详细信息
        user = await user_service.get_user_by_id(user_data["user_id"])
        if not user:
            return None
        
        return UserInfo(
            id=user.id,
            name=user.name,
            email=user.email or "",  # 处理None值
            state=user.state,
            role="user",  # 默认角色
            lastupdate=user.lastupdate,
            iplog=user.iplog,
            avatar_url=f"/avatar/1/s_{user.id}.jpg"  # 默认头像路径
        )
    except Exception:
        return None
