from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any
from src.database import get_async_session
from src.services.subscription_service import SubscriptionService
from src.utils.auth_dependencies import get_optional_current_user
from src.utils.error_handlers import handle_api_errors

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.post("/subscribe/{target_project_id}")
@handle_api_errors("订阅操作失败")
async def subscribe_to_blog(
    target_project_id: int,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    订阅博客
    
    Args:
        target_project_id: 目标博客项目ID
        current_user: 当前登录用户信息
        session: 数据库会话
        
    Returns:
        Dict: 订阅结果
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能订阅博客"
        )
    
    # 获取当前用户的博客项目ID
    from src.services.user_service import UserService
    from src.repositories.user_repository import UserRepository
    user_repo = UserRepository(session)
    user_service = UserService(user_repo)
    user = await user_service.get_user_by_id(current_user["id"])
    
    if not user or not user.projectid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您还没有创建博客，无法订阅其他博客"
        )
    
    # 检查是否尝试订阅自己的博客
    if user.projectid == target_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能订阅自己的博客"
        )
    
    subscription_service = SubscriptionService(session)
    result = await subscription_service.subscribe_to_blog(user.projectid, target_project_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.delete("/unsubscribe/{target_project_id}")
@handle_api_errors("取消订阅操作失败")
async def unsubscribe_from_blog(
    target_project_id: int,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    取消订阅博客
    
    Args:
        target_project_id: 目标博客项目ID
        current_user: 当前登录用户信息
        session: 数据库会话
        
    Returns:
        Dict: 取消订阅结果
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能取消订阅"
        )
    
    # 获取当前用户的博客项目ID
    from src.services.user_service import UserService
    from src.repositories.user_repository import UserRepository
    user_repo = UserRepository(session)
    user_service = UserService(user_repo)
    user = await user_service.get_user_by_id(current_user["id"])
    
    if not user or not user.projectid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您还没有创建博客"
        )
    
    subscription_service = SubscriptionService(session)
    result = await subscription_service.unsubscribe_from_blog(user.projectid, target_project_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.get("/status/{target_project_id}")
@handle_api_errors("获取订阅状态失败")
async def get_subscription_status(
    target_project_id: int,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    获取订阅状态
    
    Args:
        target_project_id: 目标博客项目ID
        current_user: 当前登录用户信息
        session: 数据库会话
        
    Returns:
        Dict: 订阅状态信息
    """
    if not current_user:
        return {
            "is_subscribed": False,
            "can_subscribe": False,
            "message": "未登录"
        }
    
    # 获取当前用户的博客项目ID
    from src.services.user_service import UserService
    from src.repositories.user_repository import UserRepository
    user_repo = UserRepository(session)
    user_service = UserService(user_repo)
    user = await user_service.get_user_by_id(current_user["id"])
    
    if not user or not user.projectid:
        return {
            "is_subscribed": False,
            "can_subscribe": False,
            "message": "您还没有创建博客"
        }
    
    # 检查是否尝试查看自己的博客
    if user.projectid == target_project_id:
        return {
            "is_subscribed": False,
            "can_subscribe": False,
            "message": "不能订阅自己的博客"
        }
    
    subscription_service = SubscriptionService(session)
    result = await subscription_service.check_subscription_status(user.projectid, target_project_id)
    
    return {
        "is_subscribed": result["is_subscribed"],
        "can_subscribe": True,
        "subscriber_project_id": result["subscriber_project_id"],
        "target_project_id": result["target_project_id"]
    }

@router.get("/stats/{project_id}")
@handle_api_errors("获取订阅统计失败")
async def get_subscription_stats(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    获取订阅统计信息
    
    Args:
        project_id: 博客项目ID
        session: 数据库会话
        
    Returns:
        Dict: 订阅统计信息
    """
    subscription_service = SubscriptionService(session)
    stats = await subscription_service.get_subscription_count(project_id)
    
    return stats

@router.get("/blogs/{project_id}")
@handle_api_errors("获取订阅博客列表失败")
async def get_subscribed_blogs(
    project_id: int,
    page: int = 1,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    获取指定博客订阅的所有博客列表
    
    Args:
        project_id: 博客项目ID
        page: 页码
        limit: 每页数量
        session: 数据库会话
        
    Returns:
        Dict: 订阅博客列表和分页信息
    """
    subscription_service = SubscriptionService(session)
    result = await subscription_service.get_subscribed_blogs(project_id, page, limit)
    
    return result
