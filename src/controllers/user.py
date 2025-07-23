from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from src.services.user_service import UserService
from src.database import User
from src.utils.error_handlers import handle_api_errors
from src.utils.dependencies import get_user_service

# 创建用户API路由器
router = APIRouter()

@router.get("/users/summary", response_model=Dict[str, Any])
@handle_api_errors("获取用户摘要失败")
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

@router.get("/users/{user_id}", response_model=User)
@handle_api_errors("获取用户信息失败")
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    根据用户ID获取用户信息
    
    Args:
        user_id: 用户ID
        user_service: 用户服务实例
        
    Returns:
        User: 用户信息
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user 