"""
文章控制器 (Article Controller)

提供文章相关的API端点，包括：
- 文章详情获取和缓存
- 文章评论的增删改查
- 文章附件的管理
- 文章访问统计更新
- 权限验证和错误处理

所有接口都支持缓存以提高性能。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Body, Response
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
from src.utils.cache import (
    cache_article_detail,
    cache_article_comments,
    cache_article_attachments,
    clear_article_detail_cache,
    clear_article_comments_cache,
    invalidate_project_post_list_caches,
)
from src.utils.auth_dependencies import get_current_user, get_optional_current_user
from src.utils.permission_manager import permission_manager
from src.utils.permission_decorators import require_auth
from src.utils.comment_handlers import CommentHandler
from src.utils.time_utils import TimeUtils
from src.constants import ArticleStatus, ErrorMessages
from src.utils.file_utils import get_temp_dir
from src.utils.article_hit_cookie import (
    COOKIE_NAME,
    build_cookie_value,
    cookie_max_age,
    cookie_secure,
    parse_seen_article_ids,
)

logger = logging.getLogger(__name__)

# 创建文章API路由器
router = APIRouter(tags=["文章管理"])


@router.get("/articles/{article_id}", response_model=Dict[str, Any])
@cache_article_detail(ttl=1800)  # 缓存30分钟
async def get_article_detail(
    article_id: int,
    request: Request,
    response: Response,
    page: int = 1,
    per_page: int = 10,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
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
        
        # 检查文章是否已被删除
        # 只有管理员可以访问已删除的文章
        if article.itemtype == ArticleStatus.DELETED and not permission_manager.can_manage_system(current_user):
            raise HTTPException(status_code=404, detail=ErrorMessages.ARTICLE_DELETED)
        
        # 访问计数：同浏览器、短 TTL 内同一文章只计一次（签名 Cookie，无服务端浏览状态）
        seen = parse_seen_article_ids(request.cookies.get(COOKIE_NAME))
        if seen is None:
            seen = set()
        should_count = article_id not in seen
        if should_count:
            counted_ok = False
            try:
                await project_item_repo.increment_access_count(article_id)
                if article.projectid:
                    await project_repo.increment_access_count(article.projectid)
                counted_ok = True
            except Exception:
                logger.warning(
                    "访问量递增失败 article_id=%s project_id=%s",
                    article_id,
                    article.projectid,
                    exc_info=True,
                )
            if counted_ok:
                seen.add(article_id)
                response.set_cookie(
                    key=COOKIE_NAME,
                    value=build_cookie_value(seen),
                    max_age=cookie_max_age(),
                    path="/",
                    httponly=True,
                    samesite="lax",
                    secure=cookie_secure(),
                )
                hits_display = (article.accesscount or 0) + 1
            else:
                hits_display = article.accesscount or 0
        else:
            hits_display = article.accesscount or 0
        
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
        
        # 获取文章评论（分页）
        comments_data = await post_repo.get_by_project_item_id_paginated(article_id, page, per_page)
        comments = comments_data["comments"]
        pagination = comments_data["pagination"]
        
        # 获取文章附件图片
        attachments = await attachment_repo.get_by_project_item_id(article_id)
        
        return {
            "id": article.id,
            "title": article.name,
            "content": article.comment,
            "itemtype": article.itemtype,  # 文章状态：ArticleStatus.UNKNOWN=0, ArticleStatus.NORMAL=1, ArticleStatus.DELETED=2
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
            "hits": hits_display,
            "itemsize": article.itemsize or 0,  # 文章长度（字节数）
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
            ] if comments else [],
            "comments_pagination": pagination
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文章详情失败: {str(e)}")


@router.post("/articles/{article_id}/comments", response_model=Dict[str, Any])
async def create_article_comment(
    article_id: int,
    request: Request,
    comment_data: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    为指定文章创建评论（支持匿名和登录用户）
    
    Args:
        article_id: 文章ID
        comment_data: 评论数据，包含：
        - content: 评论内容（必需）
        - subject: 评论主题（可选）
        session: 数据库会话
        current_user: 当前用户信息（可选）
        
    Returns:
        Dict[str, Any]: 创建结果，包含：
        - success: 是否成功
        - message: 结果消息
        - comment_id: 新创建的评论ID
    """
    try:
        return await CommentHandler.create_comment(
            article_id=article_id,
            comment_data=comment_data,
            request=request,
            session=session,
            current_user=current_user,
            require_auth=False
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建评论失败: {str(e)}")


@router.post("/articles/{article_id}/comments/auth", response_model=Dict[str, Any])
@require_auth()
async def create_article_comment_auth(
    article_id: int,
    request: Request,
    comment_data: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    为指定文章创建评论（仅限登录用户）
    
    Args:
        article_id: 文章ID
        comment_data: 评论数据，包含：
        - content: 评论内容（必需）
        - subject: 评论主题（可选）
        session: 数据库会话
        current_user: 当前用户信息（必需）
        
    Returns:
        Dict[str, Any]: 创建结果，包含：
        - success: 是否成功
        - message: 结果消息
        - comment_id: 新创建的评论ID
    """
    try:
        return await CommentHandler.create_comment(
            article_id=article_id,
            comment_data=comment_data,
            request=request,
            session=session,
            current_user=current_user,
            require_auth=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建评论失败: {str(e)}")


@router.delete("/articles/{article_id}/comments/{comment_id}", response_model=Dict[str, Any])
async def delete_article_comment(
    article_id: int,
    comment_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    删除指定文章的评论
    
    Args:
        article_id: 文章ID
        comment_id: 评论ID
        request: 请求对象
        session: 数据库会话
        current_user: 当前用户信息（可选）
        
    Returns:
        Dict[str, Any]: 删除结果，包含：
        - success: 是否成功
        - message: 结果消息
    """
    try:
        return await CommentHandler.delete_comment(
            article_id=article_id,
            comment_id=comment_id,
            session=session,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除评论失败: {str(e)}")


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


@router.put("/articles/{article_id}")
async def update_article(
    article_id: int,
    article_data: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新指定文章
    
    权限控制：
    - 管理员可以更新任何文章
    - 普通用户只能更新自己的文章
    
    Args:
        article_id: 文章ID
        article_data: 文章更新数据
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, str]: 更新结果
        
    Raises:
        HTTPException: 当文章不存在或无权限时
    """
    project_item_repo = ProjectItemRepository(session)
    
    try:
        # 获取文章信息
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 权限检查：管理员可以更新任何文章，普通用户只能更新自己的文章
        if not permission_manager.can_manage_system(current_user) and current_user.get("id") != article.userid:
            raise HTTPException(status_code=403, detail="无权限修改该文章")
        
        # 检查分类是否发生变化，如果变化则更新相关分类的文章数量统计
        old_folder_id = article.folderid
        new_folder_id = article_data.get("folderid")
        
        # 处理None值：如果new_folder_id是None，表示未分类（0）
        if new_folder_id is None:
            new_folder_id = 0
        
        if old_folder_id != new_folder_id:
            # 使用统计服务更新分类统计
            try:
                from src.services.stats_service import StatsService
                stats_service = StatsService(session)
                await stats_service.handle_article_folder_change(article, old_folder_id, new_folder_id)
            except Exception as e:
                # 统计更新失败不影响文章更新，静默处理
                pass
        
        # 更新文章数据
        from datetime import datetime
        import os
        from src.config.app import validate_app_config
        
        # 检查是否需要删除旧图片
        old_attachment = article.attachment
        new_attachment = article_data.get("attachment")
        
        # 获取上传目录配置
        config = validate_app_config()
        upload_dir = config["upload_dir"]
        
        # 处理临时文件移动
        if new_attachment and new_attachment.startswith("temp/"):
            try:
                # 从临时目录移动到正式目录
                temp_filename = new_attachment.replace("temp/", "")
                temp_path = os.path.join(get_temp_dir(), temp_filename)
                
                if os.path.exists(temp_path):
                    # 创建按月份命名的子目录
                    from datetime import datetime
                    current_time = TimeUtils.now_utc()
                    month_dir = current_time.strftime("%Y%m")
                    monthly_upload_path = os.path.join(upload_dir, month_dir)
                    os.makedirs(monthly_upload_path, exist_ok=True)
                    
                    # 移动到正式目录
                    final_filename = temp_filename
                    final_path = os.path.join(monthly_upload_path, final_filename)
                    os.rename(temp_path, final_path)
                    
                    # 更新attachment路径
                    new_attachment = f"{month_dir}/{final_filename}"
                    article_data["attachment"] = new_attachment
                    
                else:
                    pass  # 临时文件不存在，继续处理
            except Exception as e:
                raise HTTPException(status_code=500, detail="临时文件移动失败")
        
        # 如果旧图片存在且与新图片不同，删除旧图片
        if old_attachment and old_attachment != new_attachment:
            try:
                # 构建旧图片的完整路径
                old_image_path = os.path.join(upload_dir, old_attachment)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            except Exception as e:
                pass  # 删除旧图片失败，继续处理
        
        # 处理folderid：如果为None则设置为0（未分类）
        folderid = article_data.get("folderid")
        if folderid is None:
            folderid = 0

        eff_name = article_data["name"] if "name" in article_data else article.name
        eff_comment = article_data["comment"] if "comment" in article_data else article.comment
        itemsize = len(eff_comment.encode("utf-8")) if eff_comment else 0
        if "attachment" in article_data:
            eff_attachment = article_data["attachment"]
        else:
            eff_attachment = article.attachment

        content_changed = (
            eff_name != article.name
            or eff_comment != article.comment
            or (eff_attachment or "") != (article.attachment or "")
        )
        if "attachments" in article_data:
            from src.repositories.attachment_repository import AttachmentRepository
            att_repo_chk = AttachmentRepository(session)
            existing_atts = await att_repo_chk.get_by_project_item_id(article_id)
            old_gallery = sorted((a.linkstr or "") for a in existing_atts)
            req_list = article_data.get("attachments") or []
            new_gallery = sorted((item.get("relative_path") or "") for item in req_list)
            content_changed = content_changed or (old_gallery != new_gallery)

        update_data = {
            "name": article_data.get("name"),
            "comment": article_data.get("comment"),
            "itemtype": article_data.get("itemtype", ArticleStatus.NORMAL),
            "folderid": folderid,
            "status": article_data.get("status", 1),
            "allowpost": article_data.get("allowpost", 1),
            "attachment": article_data.get("attachment"),
            "itemsize": itemsize,
        }
        if content_changed:
            now_ts = TimeUtils.now_utc()
            update_data["updatetime"] = now_ts
            update_data["lastmodifytime"] = now_ts

        # 移除None值（但保留folderid=0）
        update_data = {k: v for k, v in update_data.items() if v is not None or k == "folderid"}
        
        updated_article = await project_item_repo.update(article_id, **update_data)
        if not updated_article:
            raise HTTPException(status_code=500, detail="更新文章失败")
        
        # 处理多张图片附件更新
        attachments_data = article_data.get("attachments", [])
        if attachments_data is not None:  # 只有当attachments字段存在时才处理
            from src.repositories.attachment_repository import AttachmentRepository
            from src.models.attachment import Attachment
            attachment_repo = AttachmentRepository(session)
            
            # 删除现有的附件记录
            await attachment_repo.delete_by_project_item_id(article_id)
            
            # 创建新的附件记录
            for attachment_data in attachments_data:
                relative_path = attachment_data.get("relative_path", "")
                
                # 处理临时文件移动
                if relative_path.startswith("temp/"):
                    try:
                        # 从临时目录移动到正式目录
                        temp_filename = relative_path.replace("temp/", "")
                        temp_path = os.path.join(get_temp_dir(), temp_filename)
                        
                        if os.path.exists(temp_path):
                            # 创建按月份命名的子目录
                            current_time = TimeUtils.now_utc()
                            month_dir = current_time.strftime("%Y%m")
                            monthly_upload_path = os.path.join(upload_dir, month_dir)
                            os.makedirs(monthly_upload_path, exist_ok=True)
                            
                            # 移动到正式目录
                            final_filename = temp_filename
                            final_path = os.path.join(monthly_upload_path, final_filename)
                            os.rename(temp_path, final_path)
                            
                            # 更新relative_path
                            relative_path = f"{month_dir}/{final_filename}"
                            
                        else:
                            pass  # 临时文件不存在，继续处理
                    except Exception as e:
                        # 继续处理，不中断整个流程
                        pass
                
                attachment = Attachment(
                    parentid=article_id,
                    amtype=1,  # 默认为正常类型
                    comment=attachment_data.get("comment", ""),
                    linkstr=relative_path,
                    createtime=TimeUtils.now_utc(),
                    updatetime=TimeUtils.now_utc()
                )
                await attachment_repo.create(attachment)
        
        # 失效相关缓存
        await clear_article_detail_cache(article_id)
        await clear_article_comments_cache(article_id)
        
        # 异步更新向量化索引
        try:
            from src.services.vectorization_update_service import get_vectorization_update_service
            vectorization_service = get_vectorization_update_service(session)
            
            # 获取更新后的文章内容
            updated_title = article_data.get("name", updated_article.name)
            updated_content = article_data.get("comment", updated_article.comment)
            
            # 异步更新向量
            await vectorization_service.update_article_vectors(
                article_id, updated_title, updated_content
            )
            
        except Exception as e:
            # 向量化更新失败不影响文章更新成功
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"向量化更新失败: {e}")
        
        if updated_article.projectid:
            project_repo = ProjectRepository(session)
            await project_repo.sync_updatetime_from_latest_published_article(updated_article.projectid)
            await session.commit()
            await invalidate_project_post_list_caches(
                updated_article.projectid, updated_article.userid
            )

        return {"message": "文章更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文章失败: {str(e)}")


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除指定文章
    
    权限控制：
    - 管理员可以删除任何文章
    - 普通用户只能删除自己的文章
    
    Args:
        article_id: 文章ID
        session: 数据库会话
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, str]: 删除结果
        
    Raises:
        HTTPException: 当文章不存在或无权限时
    """
    project_item_repo = ProjectItemRepository(session)
    
    try:
        # 获取文章信息
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 权限检查：管理员可以删除任何文章，普通用户只能删除自己的文章
        if not permission_manager.can_manage_system(current_user) and current_user.get("id") != article.userid:
            raise HTTPException(status_code=403, detail="无权限删除该文章")
        
        # 软删除文章：将itemtype设置为已删除状态
        article.itemtype = ArticleStatus.DELETED
        session.add(article)
        
        # 更新project表：减少recordcount，更新updatetime
        from src.repositories.project_repository import ProjectRepository
        project_repo = ProjectRepository(session)
        await project_repo.decrement_record_count(article.projectid)
        
        # 更新users表：减少10积分
        from src.repositories.user_repository import UserRepository
        user_repo = UserRepository(session)
        await user_repo.decrement_point(article.userid, 10)
        
        # 更新全局项目项数量统计
        from src.services.global_stats_service import GlobalStatsService
        stats_service = GlobalStatsService(session)
        await stats_service.update_project_item_count(increment=False)
        
        # 软删除时不删除向量化数据，保留用于搜索
        
        # 提交事务
        await session.commit()

        pid, uid = article.projectid, article.userid
        # 失效相关缓存
        await clear_article_detail_cache(article_id)
        await clear_article_comments_cache(article_id)
        if pid:
            await invalidate_project_post_list_caches(pid, uid)

        return {"message": "文章删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文章失败: {str(e)}")


@router.delete("/articles/{article_id}/permanent", response_model=Dict[str, Any])
async def permanently_delete_article(
    article_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    彻底删除文章（仅管理员）
    
    彻底删除文章，包括：
    1. 删除文件系统中的图片
    2. 从projectitem表中删除记录
    3. 如果文章不是已删除状态，更新相关统计信息
    
    Args:
        article_id: 文章ID
        current_user: 当前登录用户
        session: 数据库会话
        
    Returns:
        Dict: 删除结果
    """
    # 权限检查：只有管理员可以彻底删除文章
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限才能彻底删除文章")
    
    try:
        # 初始化仓库
        project_item_repo = ProjectItemRepository(session)
        
        # 获取文章信息
        article = await project_item_repo.get_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        post_project_id, post_user_id = article.projectid, article.userid

        # 记录文章状态，用于后续统计更新
        was_deleted = article.itemtype == ArticleStatus.DELETED
        
        # 硬删除时删除向量化数据
        try:
            from src.services.vectorization_update_service import get_vectorization_update_service
            vectorization_service = get_vectorization_update_service(session)
            await vectorization_service.delete_article_vectors(article_id)
        except Exception as e:
            # 向量化删除失败不影响文章删除，记录错误但继续
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"硬删除文章 {article_id} 时向量化数据删除失败: {e}")
        
        # 删除文件系统中的图片
        if article.attachment:
            await delete_article_images(article.attachment, article_id, session)
        
        # 删除该文章下所有评论，避免仅删除 projectitem 后在 post 表残留孤儿数据
        post_repo = PostRepository(session)
        await post_repo.delete_all_posts_for_project_item(article_id)
        
        # 从projectitem表中删除记录
        await project_item_repo.delete(article_id)
        
        # 如果文章不是已删除状态，需要更新相关统计信息
        if not was_deleted:
            # 更新project表：减少recordcount，更新updatetime
            from src.repositories.project_repository import ProjectRepository
            project_repo = ProjectRepository(session)
            await project_repo.decrement_record_count(article.projectid)
            
            # 更新users表：减少10积分
            from src.repositories.user_repository import UserRepository
            user_repo = UserRepository(session)
            await user_repo.decrement_point(article.userid, 10)
            
            # 更新全局项目项数量统计
            from src.services.global_stats_service import GlobalStatsService
            stats_service = GlobalStatsService(session)
            await stats_service.update_project_item_count(increment=False)
        
        # 提交事务
        await session.commit()

        # 失效相关缓存
        await clear_article_detail_cache(article_id)
        await clear_article_comments_cache(article_id)
        if post_project_id:
            await invalidate_project_post_list_caches(post_project_id, post_user_id)

        return {"message": "文章已彻底删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"彻底删除文章失败: {str(e)}")


async def delete_article_images(attachment_path: str, article_id: int, session: AsyncSession) -> None:
    """
    删除文章相关的图片文件
    
    Args:
        attachment_path: 附件路径
        article_id: 文章ID
        session: 数据库会话
    """
    import os
    
    try:
        # 获取上传目录
        from src.config.app import get_upload_dir
        upload_dir = get_upload_dir()
        
        # 删除主附件图片
        if attachment_path:
            full_path = os.path.join(upload_dir, attachment_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        # 删除其他附件图片
        from src.repositories.attachment_repository import AttachmentRepository
        attachment_repo = AttachmentRepository(session)
        attachments = await attachment_repo.get_by_project_item_id(article_id)
        
        for attachment in attachments:
            if attachment.linkstr:
                full_path = os.path.join(upload_dir, attachment.linkstr)
                if os.path.exists(full_path):
                    os.remove(full_path)
        
        # 删除附件记录（无论是否有附件都要执行删除操作）
        await attachment_repo.delete_by_project_item_id(article_id)
            
    except Exception as e:
        # 文件删除失败不应该阻止数据库删除，静默处理
        pass
