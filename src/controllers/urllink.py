from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_async_session
from src.models.urllink import UrlLink
from src.repositories.urllink_repository import UrlLinkRepository
from src.utils.auth_dependencies import get_current_user
from src.utils.cache import cache_project_friend_links, cache_all_friend_links
from src.utils.permission_decorators import require_auth
from src.utils.permission_utils import PermissionUtils
from src.utils.response_utils import ResponseUtils

router = APIRouter(tags=["友情链接"])

# Pydantic模型
class FriendLinkCreate(BaseModel):
    subject: str
    linkstr: str
    ordernum: Optional[int] = 0

class FriendLinkUpdate(BaseModel):
    subject: Optional[str] = None
    linkstr: Optional[str] = None
    ordernum: Optional[int] = None

@router.get("/projects/{project_id}/friend-links", response_model=List[UrlLink])
@cache_project_friend_links()  # 使用环境变量配置的缓存时间
async def get_project_friend_links(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目的友情链接列表
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        List[UrlLink]: 友情链接列表，按ordernum排序
    """
    try:
        repo = UrlLinkRepository(session)
        friend_links = await repo.get_friend_links_by_project(project_id)
        return friend_links
    except Exception as e:
        # 如果获取失败，返回空列表
        return []

@router.get("/friend-links", response_model=List[UrlLink])
@cache_all_friend_links()  # 使用环境变量配置的缓存时间
async def get_all_friend_links(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取所有友情链接列表
    
    Args:
        session: 数据库会话
        
    Returns:
        List[UrlLink]: 友情链接列表，按ordernum排序
    """
    try:
        repo = UrlLinkRepository(session)
        friend_links = await repo.get_all_friend_links()
        return friend_links
    except Exception as e:
        # 如果获取失败，返回空列表
        return []

@router.post("/projects/{project_id}/friend-links", response_model=UrlLink)
async def create_friend_link(
    project_id: int,
    friend_link_data: FriendLinkCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    创建友情链接
    
    Args:
        project_id: 项目ID
        friend_link_data: 友情链接数据
        current_user: 当前用户
        session: 数据库会话
        
    Returns:
        UrlLink: 创建的友情链接
    """
    try:
        # 检查权限：只有博客所有者或管理员可以创建友情链接
        if not await _check_friend_link_permission(session, project_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理该博客的友情链接"
            )
        
        # 检查友情链接数量限制（最多20个）
        repo = UrlLinkRepository(session)
        existing_links = await repo.get_friend_links_by_project(project_id)
        if len(existing_links) >= 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="友情链接数量不能超过20个"
            )
        
        # 创建友情链接
        friend_link = await repo.create_friend_link(project_id, friend_link_data)
        
        # 清除相关缓存
        from src.utils.cache import cache_manager
        await cache_manager.clear_pattern(f"project_friend_links:{project_id}")
        await cache_manager.clear_pattern("all_friend_links")
        
        return friend_link
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建友情链接失败: {str(e)}"
        )

@router.put("/friend-links/{link_id}", response_model=UrlLink)
async def update_friend_link(
    link_id: int,
    friend_link_data: FriendLinkUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    更新友情链接
    
    Args:
        link_id: 友情链接ID
        friend_link_data: 更新的友情链接数据
        current_user: 当前用户
        session: 数据库会话
        
    Returns:
        UrlLink: 更新后的友情链接
    """
    try:
        # 获取友情链接
        repo = UrlLinkRepository(session)
        friend_link = await repo.get_friend_link_by_id(link_id)
        if not friend_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="友情链接不存在"
            )
        
        # 检查权限
        if not await _check_friend_link_permission(session, friend_link.projectid, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理该博客的友情链接"
            )
        
        # 更新友情链接
        updated_link = await repo.update_friend_link(link_id, friend_link_data)
        
        # 清除相关缓存
        from src.utils.cache import cache_manager
        await cache_manager.clear_pattern(f"project_friend_links:{friend_link.projectid}")
        await cache_manager.clear_pattern("all_friend_links")
        
        return updated_link
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新友情链接失败: {str(e)}"
        )

@router.delete("/friend-links/{link_id}")
async def delete_friend_link(
    link_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    删除友情链接
    
    Args:
        link_id: 友情链接ID
        current_user: 当前用户
        session: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        # 获取友情链接
        repo = UrlLinkRepository(session)
        friend_link = await repo.get_friend_link_by_id(link_id)
        if not friend_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="友情链接不存在"
            )
        
        # 检查权限
        if not await _check_friend_link_permission(session, friend_link.projectid, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限管理该博客的友情链接"
            )
        
        # 删除友情链接
        await repo.delete_friend_link(link_id)
        
        # 清除相关缓存
        from src.utils.cache import cache_manager
        await cache_manager.clear_pattern(f"project_friend_links:{friend_link.projectid}")
        await cache_manager.clear_pattern("all_friend_links")
        
        return {"message": "友情链接删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除友情链接失败: {str(e)}"
        )

async def _check_friend_link_permission(
    session: AsyncSession, 
    project_id: int, 
    current_user: Dict[str, Any]
) -> bool:
    """
    检查用户是否有权限管理指定项目的友情链接
    
    Args:
        session: 数据库会话
        project_id: 项目ID
        current_user: 当前用户
        
    Returns:
        bool: 是否有权限
    """
    # 管理员有所有权限
    if PermissionUtils.is_admin(current_user):
        return True
    
    # 检查是否为项目所有者
    from src.repositories.project_repository import ProjectRepository
    project_repo = ProjectRepository(session)
    project = await project_repo.get_project_by_id(project_id)
    if not project:
        return False
    
    return PermissionUtils.is_owner(current_user, project.userid)
