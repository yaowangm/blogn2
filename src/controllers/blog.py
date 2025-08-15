from fastapi import APIRouter, Depends
from typing import List, Dict, Any, Optional

from src.services.blog_service import BlogService
from src.utils.error_handlers import handle_api_errors
from src.utils.dependencies import get_blog_service
from src.utils.cache import cache_blog_recent_list, cache_blog_popular_list, cache_blog_detail, cache_blog_comments, cache_blog_messages

# 创建博客API路由器
router = APIRouter()

@router.get("/blogs/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最新加入博客失败")
@cache_blog_recent_list()  # 使用默认缓存时间
async def get_recent_blogs(
    limit: int = 10,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最新加入的博客列表
    
    Args:
        limit: 返回数量限制，默认10个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最新加入的博客列表
    """
    return await blog_service.get_recent_blogs(limit)

@router.get("/blogs/popular", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最热门博客失败")
@cache_blog_popular_list()  # 使用默认缓存时间
async def get_popular_blogs(
    limit: int = 10,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最热门的博客列表
    
    Args:
        limit: 返回数量限制，默认10个
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最热门的博客列表
    """
    return await blog_service.get_popular_blogs(limit)

@router.get("/comments/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最近评论失败")
@cache_blog_comments()  # 使用默认缓存时间
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
@cache_blog_detail()  # 使用默认缓存时间
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
@cache_blog_messages()  # 使用默认缓存时间
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
@cache_blog_recent_list()  # 使用默认缓存时间
async def get_latest_posts(
    limit: int = 10,
    exclude: Optional[int] = None,
    blogid: Optional[int] = None,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最新的博文记录
    
    Args:
        limit: 返回数量限制，默认10个
        exclude: 要排除的博客ID
        blogid: 指定要获取的博客ID（如果提供，只返回该博客的文章）
        blog_service: 博客服务实例
        
    Returns:
        List[Dict[str, Any]]: 最新的博文列表
    """
    return await blog_service.get_latest_posts(limit, exclude, blogid) 