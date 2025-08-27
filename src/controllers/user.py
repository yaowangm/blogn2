from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

from src.services.user_service import UserService
from src.database import User
from src.utils.error_handlers import handle_api_errors
from src.utils.dependencies import get_user_service
from src.utils.auth_middleware import get_optional_current_user
from src.utils.cache import cache_user_profile, cache_user_blogs, cache_user_summary, cache_user_count, cache_new_users
from src.utils.permission_manager import permission_manager

# 创建用户API路由器
router = APIRouter()

@router.get("/users/summary", response_model=Dict[str, Any])
@handle_api_errors("获取用户摘要失败")
@cache_user_summary()  # 使用默认缓存时间
async def get_user_summary(
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户统计摘要
    
    返回用户总数和最近注册的用户列表。
    
    Args:
        user_service: 用户服务实例
        
    Returns:
        Dict[str, Any]: 包含用户统计信息的字典
    """
    return await user_service.get_user_summary()

@router.get("/users/listnew", response_model=List[User])
@handle_api_errors("获取最新用户失败")
@cache_new_users()  # 使用默认缓存时间
async def get_new_users(
    user_service: UserService = Depends(get_user_service)
):
    """
    获取最新注册的用户列表
    
    返回最近注册的3个用户信息。
    
    Args:
        user_service: 用户服务实例
        
    Returns:
        List[User]: 最新用户列表
    """
    return await user_service.get_top_users(3)

@router.get("/users/count")
@handle_api_errors("获取用户总数失败")
@cache_user_count()  # 使用默认缓存时间
async def get_user_count(
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户总数
    
    Args:
        user_service: 用户服务实例
        
    Returns:
        Dict[str, int]: 包含用户总数的字典
    """
    count = await user_service.get_user_count()
    return {"count": count}

@router.get("/users/{user_id}", response_model=Dict[str, Any])
@handle_api_errors("获取用户信息失败")
# 注意：不缓存用户个人资料，因为包含敏感信息
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    根据用户ID获取用户信息
    
    权限控制：
    - 如果查看自己的资料，返回完整信息
    - 如果查看其他用户的资料，返回公开信息，敏感字段标记为"无权限查看"
    - 管理员可查看任何用户的完整信息
    
    安全说明：此API包含敏感信息，要求不缓存以防止信息泄露
    
    Args:
        user_id: 用户ID
        user_service: 用户服务实例
        current_user: 当前登录用户信息（可选）
        
    Returns:
        Dict[str, Any]: 包含用户信息和权限标记的字典
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 使用权限管理器检查是否可以查看个人资料
    if not permission_manager.can_view_profile(current_user, user_id, user.state):
        raise HTTPException(status_code=403, detail="无权限查看该用户资料")
    
    # 获取权限配置
    permissions = permission_manager.get_profile_data_permissions(current_user, user_id)
    
    # 使用权限管理器过滤数据
    filtered_data = permission_manager.filter_profile_data(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password": user.password,
            "state": user.state,
            "regtime": user.regtime,
            "iplog": user.iplog,
            "point": user.point,
            "projectid": user.projectid,
            "lastupdate": user.lastupdate,
            "intropiid": user.intropiid
        },
        permissions
    )
    
    # 添加权限信息到返回数据
    filtered_data["permissions"] = permissions
    
    return filtered_data 