from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database import get_async_session
from src.repositories.urllink_repository import UrlLinkRepository
from src.models.urllink import UrlLink
from typing import List

router = APIRouter(tags=["友情链接"])

@router.get("/projects/{project_id}/friend-links", response_model=List[UrlLink])
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
        friend_links = await UrlLinkRepository.get_friend_links_by_project(session, project_id)
        return friend_links
    except Exception as e:
        # 如果获取失败，返回空列表
        return []

@router.get("/friend-links", response_model=List[UrlLink])
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
        friend_links = await UrlLinkRepository.get_all_friend_links(session)
        return friend_links
    except Exception as e:
        # 如果获取失败，返回空列表
        return []
