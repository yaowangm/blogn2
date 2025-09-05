"""
文章控制器
提供文章相关的API端点，包括文章详情、评论管理等
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from src.database import get_async_session
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.user_repository import UserRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.post_repository import PostRepository
from src.repositories.attachment_repository import AttachmentRepository
from src.models.post import Post
from src.utils.cache import cache_article_detail, cache_article_comments, cache_article_attachments, clear_article_detail_cache, clear_article_comments_cache

# 创建文章API路由器
router = APIRouter(tags=["文章管理"])


@router.get("/articles/{article_id}", response_model=Dict[str, Any])
@cache_article_detail(ttl=1800)  # 缓存30分钟
async def get_article_detail(
    article_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定文章的详细信息
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 文章详细信息，包括：
        - 基本信息：标题、内容、附件
        - 作者信息：用户ID、姓名
        - 项目信息：博客ID、名称
        - 统计信息：点击数、评论数、创建时间、更新时间
        - 评论列表：评论内容、用户、时间、回复数
        - 附件列表：多张图片附件信息
    """
    project_item_repo = ProjectItemRepository(session)
    user_repo = UserRepository(session)
    project_repo = ProjectRepository(session)
    post_repo = PostRepository(session)
    attachment_repo = AttachmentRepository(session)
    
    try:
        # 获取文章信息
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 获取作者信息
        author = None
        if article.userid:
            author = await user_repo.get_by_id(article.userid)
        
        # 获取项目信息
        project = None
        if article.projectid:
            project = await project_repo.get_by_id(article.projectid)
        
        # 获取分类信息
        category = None
        if article.folderid:
            from src.repositories.folder_repository import FolderRepository
            folder_repo = FolderRepository(session)
            category = await folder_repo.get_by_id(article.folderid)
        
        # 获取文章评论
        comments = await post_repo.get_by_project_item_id(article_id)
        
        # 获取文章附件图片
        attachments = await attachment_repo.get_by_project_item_id(article_id)
        
        return {
            "id": article.id,
            "title": article.name,
            "content": article.comment,
            "attachment": article.attachment,  # 单张图片附件
            "attachments": [  # 多张图片附件
                {
                    "id": attachment.id,
                    "comment": attachment.comment,
                    "linkstr": attachment.linkstr,
                    "created_at": attachment.createtime
                } for attachment in attachments
            ] if attachments else [],
            "author": {
                "id": author.id if author else None,
                "name": author.name if author else "未知作者",
                "avatar": None  # users表没有logo字段
            } if author else None,
            "project": {
                "id": project.id if project else None,
                "name": project.name if project else None
            } if project else None,
            "category": {
                "id": article.folderid,
                "name": category.name if category else "未分类"
            },
            "allowpost": article.allowpost,  # 评论设置
            "hits": article.accesscount or 0,
            "created_at": article.createtime,
            "updated_at": article.updatetime,
            "comment_count": article.commentcount or 0,
            "comments": [
                {
                    "id": comment.id,
                    "content": comment.content,
                    "user_id": comment.userid,
                    "post_time": comment.posttime,
                    "reply_count": comment.replycount or 0
                } for comment in comments
            ] if comments else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文章详情失败: {str(e)}")


@router.post("/articles/{article_id}/comments", response_model=Dict[str, Any])
async def create_article_comment(
    article_id: int,
    comment_data: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session)
):
    """
    为指定文章创建评论
    
    Args:
        article_id: 文章ID
        comment_data: 评论数据，包含：
        - content: 评论内容（必需）
        - user_id: 用户ID（必需）
        - subject: 评论主题（可选）
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 创建结果，包含：
        - success: 是否成功
        - message: 结果消息
        - comment_id: 新创建的评论ID
    """
    post_repo = PostRepository(session)
    project_item_repo = ProjectItemRepository(session)
    
    try:
        # 验证文章是否存在
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 验证评论数据
        content = comment_data.get("content")
        user_id = comment_data.get("user_id")
        
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="评论内容不能为空")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="用户ID不能为空")
        
        # 创建评论
        comment = Post(
            projectitemid=article_id,
            userid=user_id,
            subject=comment_data.get("subject", ""),
            content=content.strip(),
            posttime=datetime.now(),
            status=1  # 1表示正常状态
        )
        
        await post_repo.create(comment)
        
        # 更新文章的评论数
        await project_item_repo.increment_comment_count(article_id)
        
        # 失效相关缓存
        await clear_article_detail_cache(article_id)
        await clear_article_comments_cache(article_id)
        
        return {
            "success": True,
            "message": "评论创建成功",
            "comment_id": comment.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建评论失败: {str(e)}")


@router.get("/articles/{article_id}/comments", response_model=List[Dict[str, Any]])
@cache_article_comments(ttl=900)  # 缓存15分钟
async def get_article_comments(
    article_id: int,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定文章的评论列表（分页）
    
    Args:
        article_id: 文章ID
        page: 页码，默认1
        limit: 每页数量，默认20
        session: 数据库会话
        
    Returns:
        List[Dict[str, Any]]: 评论列表，每个评论包含：
        - id: 评论ID
        - content: 评论内容
        - user_id: 用户ID
        - post_time: 评论时间
        - reply_count: 回复数量
    """
    post_repo = PostRepository(session)
    project_item_repo = ProjectItemRepository(session)
    
    try:
        # 验证文章是否存在
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 获取评论列表
        comments = await post_repo.get_by_project_item_id(article_id)
        
        # 简单的分页处理
        start = (page - 1) * limit
        end = start + limit
        paginated_comments = comments[start:end]
        
        return [
            {
                "id": comment.id,
                "content": comment.content,
                "user_id": comment.userid,
                "post_time": comment.posttime,
                "reply_count": comment.replycount or 0
            } for comment in paginated_comments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取评论列表失败: {str(e)}")


@router.get("/articles/{article_id}/attachments", response_model=List[Dict[str, Any]])
@cache_article_attachments(ttl=3600)  # 缓存1小时
async def get_article_attachments(
    article_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定文章的所有附件
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        
    Returns:
        List[Dict[str, Any]]: 附件列表，每个附件包含：
        - id: 附件ID
        - comment: 附件注释/描述
        - linkstr: 附件链接路径
        - created_at: 创建时间
    """
    attachment_repo = AttachmentRepository(session)
    project_item_repo = ProjectItemRepository(session)
    
    try:
        # 验证文章是否存在
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 获取附件列表
        attachments = await attachment_repo.get_by_project_item_id(article_id)
        
        return [
            {
                "id": attachment.id,
                "comment": attachment.comment,
                "linkstr": attachment.linkstr,
                "created_at": attachment.createtime
            } for attachment in attachments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取附件列表失败: {str(e)}")
