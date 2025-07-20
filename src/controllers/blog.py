from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any

from src.database import get_async_session
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.post_repository import PostRepository
from src.services.blog_service import BlogService
from src.utils.error_handlers import handle_api_errors

# 创建博客API路由器
router = APIRouter()

def get_blog_service(session: AsyncSession = Depends(get_async_session)) -> BlogService:
    """
    依赖注入：创建博客服务实例
    
    Args:
        session: 数据库会话
        
    Returns:
        BlogService: 博客服务实例
    """
    user_repo = UserRepository(session)
    project_item_repo = ProjectItemRepository(session)
    project_repo = ProjectRepository(session)
    post_repo = PostRepository(session)
    return BlogService(user_repo, project_item_repo, project_repo, post_repo)

@router.get("/blogs/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最新加入博客失败")
async def get_recent_blogs(
    limit: int = 10,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最新加入的博客列表
    
    Args:
        limit: 返回数量限制，默认5个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最新加入的博客列表
    """
    return await blog_service.get_recent_blogs(limit)

@router.get("/blogs/popular", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最热门博客失败")
async def get_popular_blogs(
    limit: int = 5,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最热门的博客列表
    
    Args:
        limit: 返回数量限制，默认5个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最热门的博客列表
    """
    return await blog_service.get_popular_blogs(limit)

@router.get("/comments/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最近评论失败")
async def get_recent_comments(
    limit: int = 5,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最近的评论列表
    
    Args:
        limit: 返回数量限制，默认5个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最近的评论列表
    """
    return await blog_service.get_recent_comments(limit)

@router.get("/blogs/about", response_model=Dict[str, Any])
@handle_api_errors("获取关于页面内容失败")
async def get_about_content(
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取关于页面的内容（来自ID为486的projectitem记录）
    
    Args:
        blog_service: 博客服务实例
        
    Returns:
        Dict[str, Any]: 关于页面的内容
    """
    return await blog_service.get_about_content()

@router.get("/blogs/messages/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最近留言失败")
async def get_recent_messages(
    limit: int = 5,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最近的留言本记录
    
    Args:
        limit: 返回数量限制，默认5个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最近的留言列表
    """
    return await blog_service.get_recent_messages(limit)

@router.get("/blogs/posts/latest", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最新博文失败")
async def get_latest_posts(
    limit: int = 10,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最新的博文记录
    
    Args:
        limit: 返回数量限制，默认10个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最新的博文列表
    """
    return await blog_service.get_latest_posts(limit) 