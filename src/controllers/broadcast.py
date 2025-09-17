from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any
from src.database import get_async_session
from src.services.broadcast_service import BroadcastService
from src.utils.auth_dependencies import get_current_user
from src.utils.error_handlers import handle_api_errors

router = APIRouter(prefix="/broadcast", tags=["broadcast"])

@router.post("/article/{article_id}")
@handle_api_errors("广播文章失败")
async def broadcast_article(
    article_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    广播文章给所有订阅者
    
    Args:
        article_id: 文章ID (projectitem.id)
        current_user: 当前用户信息
        session: 数据库会话
    
    Returns:
        广播结果
    """
    # 获取用户的博客ID
    user_project_id = current_user.get("projectid")
    if not user_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您还没有创建博客"
        )
    
    # 创建广播服务
    broadcast_service = BroadcastService(session)
    
    # 执行广播
    result = await broadcast_service.broadcast_new_article(user_project_id, article_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return result

@router.get("/stats")
@handle_api_errors("获取广播统计失败")
async def get_broadcast_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    获取当前用户的广播统计信息
    
    Args:
        current_user: 当前用户信息
        session: 数据库会话
    
    Returns:
        广播统计信息
    """
    # 获取用户的博客ID
    user_project_id = current_user.get("projectid")
    if not user_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您还没有创建博客"
        )
    
    # 创建广播服务
    broadcast_service = BroadcastService(session)
    
    # 获取统计信息
    stats = await broadcast_service.get_broadcast_stats(user_project_id)
    
    return stats
