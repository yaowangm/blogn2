"""
权限装饰器
提供便捷的权限检查装饰器，用于API端点权限控制
"""

from functools import wraps
from typing import Callable, Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

from src.utils.permission_manager import permission_manager
from src.utils.auth_middleware import get_optional_current_user

# 安全方案
security = HTTPBearer(auto_error=False)


def require_auth(admin_only: bool = False):
    """
    认证装饰器
    
    Args:
        admin_only: 是否仅限管理员访问
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="需要登录才能访问")
            
            # 如果需要管理员权限
            if admin_only:
                if not permission_manager.can_manage_system(current_user):
                    raise HTTPException(status_code=403, detail="需要管理员权限")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_profile_access():
    """
    要求个人资料访问权限的装饰器
    
    用于需要查看用户个人资料的API端点
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和目标用户ID
            current_user = kwargs.get('current_user')
            user_id = kwargs.get('user_id')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="需要登录才能访问")
            
            if not user_id:
                raise HTTPException(status_code=400, detail="缺少用户ID参数")
            
            # 检查权限
            if not permission_manager.can_view_profile(current_user, user_id, None):
                raise HTTPException(status_code=403, detail="无权限访问该用户资料")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_sensitive_fields_access():
    """
    要求敏感字段访问权限的装饰器
    
    用于需要查看用户敏感信息的API端点
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和目标用户ID
            current_user = kwargs.get('current_user')
            user_id = kwargs.get('user_id')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="需要登录才能访问")
            
            if not user_id:
                raise HTTPException(status_code=400, detail="缺少用户ID参数")
            
            # 检查敏感字段访问权限
            if not permission_manager.can_view_sensitive_fields(current_user, user_id):
                raise HTTPException(status_code=403, detail="无权限访问敏感信息")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """
    要求管理员权限的装饰器
    
    用于仅限管理员访问的API端点
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="需要登录才能访问")
            
            # 检查管理员权限
            if not permission_manager.can_manage_system(current_user):
                raise HTTPException(status_code=403, detail="需要管理员权限")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_user_management():
    """
    要求用户管理权限的装饰器
    
    用于需要管理其他用户的API端点
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(status_code=401, detail="需要登录才能访问")
            
            # 检查用户管理权限
            if not permission_manager.can_manage_users(current_user):
                raise HTTPException(status_code=403, detail="需要用户管理权限")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 预定义的依赖项
def get_current_user_for_permission():
    """获取当前用户用于权限检查的依赖项"""
    return Depends(get_optional_current_user)


def get_current_user_required():
    """获取当前用户（必需）的依赖项"""
    return Depends(get_optional_current_user)
