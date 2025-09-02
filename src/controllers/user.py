from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

from src.services.user_service import UserService
from src.database import User
from src.utils.error_handlers import handle_api_errors
from src.utils.dependencies import get_user_service
from src.utils.auth_middleware import get_optional_current_user, get_current_user
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

@router.get("/users/list", response_model=Dict[str, Any])
@handle_api_errors("获取用户列表失败")
async def get_users_list(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户列表（仅管理员可访问）
    
    支持分页和搜索功能，返回用户的基本信息包括：
    - id: 用户ID
    - name: 用户名
    - state: 用户状态
    - regtime: 注册时间
    - point: 积分
    - projectid: 项目ID（博客链接）
    - email: 邮箱
    
    Args:
        page: 页码，从1开始，默认1
        page_size: 每页大小，默认20，最大100
        search: 搜索关键词，对用户名进行模糊匹配，可选
        user_service: 用户服务实例
        current_user: 当前登录用户信息（必须是管理员）
        
    Returns:
        Dict[str, Any]: 包含用户列表和分页信息的字典
        
    Raises:
        HTTPException: 当用户不是管理员时抛出403错误
    """
    # 检查管理员权限
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能访问")
    
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 验证和规范化分页参数
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    
    return await user_service.get_users_paginated(page, page_size, search)

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

@router.post("/users/{user_id}/reset-password")
@handle_api_errors("重置密码失败")
async def reset_user_password(
    user_id: int,
    password_data: Dict[str, str],
    user_service: UserService = Depends(get_user_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    重置用户密码
    
    权限控制：
    - 管理员可以重置任何用户的密码
    - 普通用户只能重置自己的密码
    
    Args:
        user_id: 要重置密码的用户ID
        password_data: 包含新密码的数据 {"new_password": "新密码"}
        user_service: 用户服务实例
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, str]: 重置结果
        
    Raises:
        HTTPException: 当无权限或用户不存在时
    """
    # 检查权限
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能重置密码")
    
    # 检查目标用户是否存在
    target_user = await user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查：管理员可以重置任何用户的密码，普通用户只能重置自己的密码
    if current_user.get("state") != 10 and current_user.get("id") != user_id:
        raise HTTPException(status_code=403, detail="无权限重置该用户的密码")
    
    # 验证新密码
    new_password = password_data.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6位")
    
    # 调用用户服务重置密码
    await user_service.reset_user_password(user_id, new_password)
    return {"message": "密码重置成功"}