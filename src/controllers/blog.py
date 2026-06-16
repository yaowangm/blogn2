from fastapi import APIRouter, Depends, Request, HTTPException, Body
from typing import List, Dict, Any, Optional
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.blog_service import BlogService
from src.utils.error_handlers import handle_api_errors
from src.utils.dependencies import get_blog_service
from src.utils.cache import cache_blog_recent_list, cache_blogs_joined_recent, cache_blog_popular_list, cache_blog_detail, cache_blog_comments, cache_blog_messages_recent, cache_blog_messages_list, cache_blog_message_thread, clear_blog_messages_cache
from src.utils.auth_dependencies import get_current_user, get_optional_current_user
from src.database import get_async_session
from src.services.global_stats_service import GlobalStatsService

# 创建博客API路由器
router = APIRouter()

@router.get("/blogs/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最新加入博客失败")
@cache_blogs_joined_recent()
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
@cache_blog_comments()
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

@router.post("/blogs/set-intro/{article_id}")
@handle_api_errors("设置网站介绍文章失败")
async def set_intro_article(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    设置指定文章为网站介绍文章
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, Any]: 操作结果
    """
    # 检查用户是否为管理员
    if current_user.get("state") != 10:
        raise HTTPException(status_code=403, detail="只有管理员可以设置网站介绍文章")
    
    # 验证文章是否存在
    from src.repositories.project_item_repository import ProjectItemRepository
    project_item_repo = ProjectItemRepository(session)
    article = await project_item_repo.get_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 设置intropiid
    stats_service = GlobalStatsService(session)
    success = await stats_service.set_stat_value("intropiid", article_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="设置失败")
    
    return {
        "message": "网站介绍文章设置成功",
        "article_id": article_id,
        "article_title": article.name or "无标题"
    }

@router.get("/blogs/messages/recent", response_model=List[Dict[str, Any]])
@handle_api_errors("获取最近留言失败")
@cache_blog_messages_recent(ttl=900)  # 缓存15分钟
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

@router.get("/messages", response_model=Dict[str, Any])
@handle_api_errors("获取留言本列表失败")
@cache_blog_messages_list(ttl=900)  # 缓存15分钟
async def get_messages_list(
    page: int = 1,
    limit: int = 10,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取留言本分页列表
    
    Args:
        page: 页码，默认1
        limit: 每页数量，默认10
        blog_service: 博客服务实例
        
    Returns:
        Dict[str, Any]: 留言本分页数据
    """
    return await blog_service.get_messages_list(page, limit)

@router.get("/thread/{thread_id}", response_model=Dict[str, Any])
@cache_blog_message_thread(ttl=900)  # 缓存15分钟
async def get_thread(
    thread_id: int,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取主题的所有留言
    
    Args:
        thread_id: 主题ID（主贴ID）
        blog_service: 博客服务实例
        
    Returns:
        Dict[str, Any]: 主题留言数据
    """
    try:
        return await blog_service.get_thread(thread_id)
    except ValueError as e:
        # 主题不存在，返回404
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 其他错误，返回500
        raise HTTPException(status_code=500, detail=f"获取主题失败: {str(e)}")

@router.post("/messages", response_model=Dict[str, Any])
@handle_api_errors("提交留言失败")
async def create_message(
    request: Request,
    message_data: Dict[str, Any] = Body(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    提交新留言
    
    Args:
        message_data: 留言数据
        request: 请求对象
        current_user: 当前用户
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 创建结果
    """
    from src.repositories.post_repository import PostRepository
    from src.models.post import Post
    from src.utils.time_utils import TimeUtils
    from datetime import datetime
    
    post_repo = PostRepository(session)
    
    try:
        # 验证留言数据
        subject = message_data.get("subject", "").strip()
        content = message_data.get("content", "").strip()
        thread_id = message_data.get("thread_id")
        
        # 对于跟贴，subject可以为空；对于主贴，subject不能为空
        if not thread_id and not subject:
            raise HTTPException(status_code=400, detail="留言标题不能为空")
        
        if not content:
            raise HTTPException(status_code=400, detail="留言内容不能为空")
        
        if subject and len(subject) > 200:
            raise HTTPException(status_code=400, detail="标题不能超过200个字符")
        
        # 获取用户ID
        user_id = None
        if current_user:
            user_id = current_user.get("id")
        else:
            # 对于匿名留言，要求前端提供user_id
            user_id = message_data.get("user_id", 0)
        
        if user_id is None:
            raise HTTPException(status_code=400, detail="用户ID不能为空")
        
        # 获取客户端IP地址
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # 计算内容大小（字节数）
        content_bytes = content.encode('utf-8')
        content_size = len(content_bytes)
        
        # 创建留言
        message = Post(
            folderid=0,  # 文件夹ID为0
            projectitemid=0,  # 留言本的projectitemid为0
            userid=user_id,
            subject=subject,
            content=content,
            size=content_size,  # 内容大小（字节）
            hits=0,  # 访问次数初始为0
            userip=client_ip,  # 用户IP地址
            posttime=TimeUtils.now_utc(),
            status=1,  # 1表示正常状态
            rootid=thread_id if thread_id else 0,  # 跟贴的rootid为thread_id，主贴的rootid为0
            replycount=0  # 新留言的回复数为0
        )
        
        try:
            # 创建留言（跟贴时 post_repo.create 内已通过 StatsService 更新 replycount）
            await post_repo.create(message)
            
            # 提交事务
            await session.commit()
            
            # 清除留言相关缓存
            await clear_blog_messages_cache()

            from src.utils.vectorization_tasks import schedule_comment_vectorization

            schedule_comment_vectorization(
                message.id,
                message.subject or "",
                message.content,
                message.projectitemid,
            )
            
            return {
                "success": True,
                "message": "留言创建成功",
                "message_id": message.id,
                "subject": message.subject,
                "content": message.content,
                "user_id": message.userid,
                "created_at": message.posttime
            }
            
        except Exception as e:
            # 回滚事务
            await session.rollback()
            raise e
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建留言失败: {str(e)}")

@router.delete("/messages/{message_id}", response_model=Dict[str, Any])
@handle_api_errors("删除留言失败")
async def delete_message(
    message_id: int,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    删除留言（仅管理员可操作）
    
    Args:
        message_id: 留言ID
        current_user: 当前用户
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 删除结果
    """
    from src.repositories.post_repository import PostRepository
    from src.utils.permission_manager import permission_manager
    from src.utils.time_utils import TimeUtils
    
    # 检查用户是否登录
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能删除留言")
    
    # 检查是否为管理员
    if not permission_manager.is_admin(current_user.get("state", 0)):
        raise HTTPException(status_code=403, detail="只有管理员才能删除留言")
    
    post_repo = PostRepository(session)
    
    try:
        # 执行删除操作
        result = await post_repo.delete_post(message_id)
        
        if result["success"]:
            # 清除留言相关缓存
            await clear_blog_messages_cache()
            
            return {
                "success": True,
                "message": result["message"],
                "deleted_count": result["deleted_count"],
                "deleted_messages": result.get("deleted_posts", result.get("deleted_messages", [])),
                "is_main_post": result["is_main_post"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除留言失败: {str(e)}")

@router.get("/blogs/posts/latest", response_model=Dict[str, Any])
@handle_api_errors("获取最新博文失败")
@cache_blog_recent_list()  # 使用默认缓存时间
async def get_latest_posts(
    page: int = 1,
    page_size: int = 10,
    exclude: Optional[int] = None,
    blogid: Optional[int] = None,
    blog_service: BlogService = Depends(get_blog_service)
):
    """
    获取最新的博文记录（支持分页）
    
    Args:
        page: 页码，默认1
        page_size: 每页数量，默认10
        exclude: 要排除的博客ID
        blogid: 指定要获取的博客ID（如果提供，只返回该博客的文章）
        blog_service: 博客服务实例
        
    Returns:
        Dict[str, Any]: 包含分页信息的博文列表
            {
                "posts": List[Dict[str, Any]],  # 博文列表
                "total": int,                    # 总数量
                "page": int,                     # 当前页码
                "page_size": int,                # 每页数量
                "total_pages": int               # 总页数
            }
    """
    return await blog_service.get_latest_posts(page, page_size, exclude, blogid) 