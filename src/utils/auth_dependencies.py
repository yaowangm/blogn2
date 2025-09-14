"""
认证依赖
提供独立的认证服务，不依赖auth_middleware.py
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.utils.dependencies import get_user_service

# 安全方案
security = HTTPBearer(auto_error=False)

# 获取JWT密钥（从环境变量）
import os
JWT_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")


def get_auth_service(user_service: UserService = Depends(get_user_service)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(user_service.user_repo, JWT_SECRET_KEY)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Optional[Dict[str, Any]]:
    """
    获取当前登录用户（可选）
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        user_service: 用户服务实例
        
    Returns:
        Optional[Dict]: 当前用户信息，如果未登录则返回None
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
        
        # 检查用户状态
        if user.state == 0:
            return None  # 冻结用户返回None
        
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
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """
    获取当前登录用户（必需）
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务实例
        user_service: 用户服务实例
        
    Returns:
        Dict: 当前用户信息
        
    Raises:
        HTTPException: 当令牌无效或用户不存在时
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能访问",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
