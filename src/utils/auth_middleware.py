"""
认证中间件
提供JWT令牌验证和用户认证功能
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from functools import wraps

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.utils.dependencies import get_user_service

# 安全方案
security = HTTPBearer()

# 获取JWT密钥（从环境变量）
import os
JWT_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

def get_auth_service(user_service: UserService = Depends(get_user_service)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(user_service.user_repo, JWT_SECRET_KEY)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """
    获取当前登录用户
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        user_service: 用户服务实例
        
    Returns:
        Dict: 当前用户信息
        
    Raises:
        HTTPException: 当令牌无效或用户不存在时
    """
    # 验证令牌
    user_data = auth_service.get_user_from_token(credentials.credentials)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户详细信息
    user = await user_service.get_user_by_id(user_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查用户状态
    if user.state == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被冻结"
        )
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "state": user.state,
        "role": "admin" if user.state == 10 else "user",
        "lastupdate": user.lastupdate,
        "iplog": user.iplog
    }

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前活跃用户（状态为1或10的用户）
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        Dict: 当前活跃用户信息
        
    Raises:
        HTTPException: 当用户账户被冻结时
    """
    if current_user["state"] == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被冻结"
        )
    return current_user

async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前管理员用户（状态为10的用户）
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        Dict: 当前管理员用户信息
        
    Raises:
        HTTPException: 当用户不是管理员时
    """
    if current_user["state"] != 10:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Optional[Dict[str, Any]]:
    """
    获取可选的当前登录用户
    
    如果用户已登录，返回用户信息；如果未登录，返回None。
    不会抛出异常，用于需要区分登录状态的场景。
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        user_service: 用户服务实例
        
    Returns:
        Optional[Dict]: 当前用户信息，如果未登录则为None
    """
    try:
        # 验证令牌
        user_data = auth_service.get_user_from_token(credentials.credentials)
        if not user_data:
            return None
        
        # 获取用户详细信息
        user = await user_service.get_user_by_id(user_data["user_id"])
        if not user or user.state == 0:
            return None
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "state": user.state,
            "role": "admin" if user.state == 10 else "user",
            "lastupdate": user.lastupdate,
            "iplog": user.iplog
        }
    except Exception:
        # 任何错误都返回None，表示未登录
        return None

def require_auth(admin_only: bool = False):
    """
    认证装饰器
    
    Args:
        admin_only: 是否仅限管理员访问
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里可以根据需要添加认证逻辑
            # 目前主要依赖FastAPI的依赖注入系统
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 预定义的依赖项
current_user = Depends(get_current_user)
current_active_user = Depends(get_current_active_user)
current_admin_user = Depends(get_current_admin_user)
