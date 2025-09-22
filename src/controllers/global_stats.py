"""
全局统计API控制器

提供全局统计数据的查看和同步功能。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any

from src.database import get_async_session
from src.services.global_stats_service import GlobalStatsService
from src.utils.auth_dependencies import get_current_user
from src.utils.permission_decorators import require_auth
from src.utils.error_handlers import handle_api_errors


# 创建全局统计API路由器
router = APIRouter(prefix="/stats", tags=["全局统计"])


@router.get("/global", response_model=Dict[str, Any])
@handle_api_errors("获取全局统计失败")
async def get_global_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取全局统计数据
    
    返回用户数量、项目数量、项目项数量等统计信息。
    
    Args:
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 全局统计信息
    """
    stats_service = GlobalStatsService(session)
    stats = await stats_service.get_all_stats()
    
    return {
        "usercount": stats.get("usercount", 0),
        "projectcount": stats.get("projectcount", 0),
        "projectitemcount": stats.get("projectitemcount", 0)
    }


@router.post("/global/sync")
@handle_api_errors("同步全局统计失败")
@require_auth(admin_only=True)
async def sync_global_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    同步全局统计数据（仅管理员）
    
    从实际数据库数据重新计算所有统计值，用于数据修复或初始化。
    
    Args:
        session: 数据库会话
        current_user: 当前登录用户信息（必须是管理员）
        
    Returns:
        Dict[str, str]: 同步结果
        
    Raises:
        HTTPException: 当用户不是管理员时抛出403错误
    """
    stats_service = GlobalStatsService(session)
    success = await stats_service.sync_stats_from_database()
    
    if success:
        # 获取同步后的统计值
        stats = await stats_service.get_all_stats()
        return {
            "message": "全局统计同步成功",
            "stats": stats
        }
    else:
        raise HTTPException(status_code=500, detail="同步全局统计失败")


@router.get("/global/detailed", response_model=Dict[str, Any])
@handle_api_errors("获取详细统计失败")
@require_auth(admin_only=True)
async def get_detailed_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取详细统计信息（仅管理员）
    
    返回更详细的统计信息，包括数据库中的实际数据。
    
    Args:
        session: 数据库会话
        current_user: 当前登录用户信息（必须是管理员）
        
    Returns:
        Dict[str, Any]: 详细统计信息
        
    Raises:
        HTTPException: 当用户不是管理员时抛出403错误
    """
    from src.models.user import User
    from src.models.project import Project
    from src.models.project_item import ProjectItem
    from sqlmodel import func, select
    
    # 获取实际数据库统计
    user_count_stmt = select(func.count(User.id))
    user_count_result = await session.exec(user_count_stmt)
    actual_user_count = user_count_result.first() or 0
    
    project_count_stmt = select(func.count(Project.id))
    project_count_result = await session.exec(project_count_stmt)
    actual_project_count = project_count_result.first() or 0
    
    project_item_count_stmt = select(func.count(ProjectItem.id))
    project_item_count_result = await session.exec(project_item_count_stmt)
    actual_project_item_count = project_item_count_result.first() or 0
    
    # 获取glovar表中的统计
    stats_service = GlobalStatsService(session)
    glovar_stats = await stats_service.get_all_stats()
    
    return {
        "actual_counts": {
            "usercount": actual_user_count,
            "projectcount": actual_project_count,
            "projectitemcount": actual_project_item_count
        },
        "glovar_counts": glovar_stats,
        "differences": {
            "usercount": actual_user_count - glovar_stats.get("usercount", 0),
            "projectcount": actual_project_count - glovar_stats.get("projectcount", 0),
            "projectitemcount": actual_project_item_count - glovar_stats.get("projectitemcount", 0)
        }
    }
