import logging

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_async_session
from src.repositories.project_repository import ProjectRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.post_repository import PostRepository
from src.repositories.folder_repository import FolderRepository
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.folder import Folder
from src.utils.cache import (
    cache_project_detail, cache_project_posts, cache_project_comments,
    cache_project_categories, cache_project_external_links, cache_project_rss,
    cache_project_stats, cache_user_projects, invalidate_project_post_list_caches,
    invalidate_project_categories_cache, invalidate_blog_directory_caches,
)
from src.utils.auth_dependencies import get_current_user, get_optional_current_user
from src.utils.permission_manager import permission_manager
from src.services.blog_service import BlogService
from src.repositories.user_repository import UserRepository
from src.constants import ArticleStatus
from src.utils.file_utils import promote_temp_relative_path
from src.utils.time_utils import TimeUtils
from src.config.app import validate_app_config

logger = logging.getLogger(__name__)

# 创建项目API路由器
router = APIRouter()

@router.get("/projects/{project_id}", response_model=Dict[str, Any])
@cache_project_detail()  # 使用环境变量配置的缓存时间
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目信息
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 项目信息
    """
    project_repo = ProjectRepository(session)
    project = await project_repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "id": project.id,
        "name": project.name,
        "comment": project.comment,
        "recordcount": project.recordcount,
        "accesscount": project.accesscount,
        "userid": project.userid,
        "createtime": project.createtime,
        "updatetime": project.updatetime,
        "commentcount": project.commentcount
    }

@router.get("/projects/{project_id}/posts", response_model=Dict[str, Any])
@cache_project_posts()  # 使用环境变量配置的缓存时间
async def get_project_posts(
    project_id: int,
    page: int = 1,
    limit: int = 10,
    type: str = "original",
    category: Optional[str] = None,
    folderid: Optional[int] = None,
    include_deleted: bool = False,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    获取指定项目的文章列表
    
    Args:
        project_id: 项目ID
        page: 页码
        limit: 每页数量
        type: 文章类型 (original/subscription)
        category: 分类筛选
        folderid: 文件夹ID筛选
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 文章列表和总数
    """
    if type == "subscription":
        # 获取订阅文章
        from src.repositories.subscription_repository import SubscriptionRepository
        subscription_repo = SubscriptionRepository(session)
        return await subscription_repo.get_subscription_posts_by_project(project_id, page, limit)
    else:
        # 获取原创文章
        project_item_repo = ProjectItemRepository(session)
        offset = (page - 1) * limit
        is_admin = permission_manager.can_manage_system(current_user)
        should_include_deleted = include_deleted and is_admin
        posts = await project_item_repo.get_by_project_id_and_folder(project_id, folderid, limit, offset, should_include_deleted)
        
        total = await project_item_repo.count_by_project_id_and_folder(project_id, folderid)
        if folderid is not None and folderid > 0:
            folder_repo = FolderRepository(session)
            folder = await folder_repo.get_by_id(folderid)
            if folder and folder.recordcount is not None and folder.recordcount != total:
                logger.warning(
                    "folder %s recordcount stale: cached=%s live=%s",
                    folderid,
                    folder.recordcount,
                    total,
                )

        # 获取分类信息（folderid=0 表示未分类，为有效筛选值）
        category_name = "全部文章"
        if folderid is not None:
            if folderid == 0:
                category_name = "未分类"
            else:
                folder_repo = FolderRepository(session)
                try:
                    folder = await folder_repo.get_by_id(folderid)
                    if folder:
                        category_name = folder.name
                except Exception:
                    logger.exception("获取分类名称失败 folderid=%s", folderid)
        
        # 转换为字典格式
        posts_data = []
        
        # 使用统一依赖注入的BlogService用于头像检查
        from src.utils.dependencies import get_blog_service
        from fastapi import Depends
        blog_service = await get_blog_service(session)
        
        for post in posts:
            # 生成头像路径 - 使用BlogService检查头像是否存在
            avatar_path = None
            if post["userid"]:
                avatar_path = blog_service._check_avatar_exists(post["userid"])
            
            posts_data.append({
                "id": post["id"],
                "name": post["name"],
                "comment": post["comment"],
                "createtime": post["createtime"],
                "accesscount": post["accesscount"],
                "commentcount": post["commentcount"],
                "category": (post.get("category") or "未分类").strip(),
                "folderid": post.get("folderid"),
                "author_name": post["author_name"],
                "userid": post["userid"],
                "avatar": avatar_path,
                "image": f"/upload/{post['attachment']}" if post.get("attachment") else None
            })
        
        return {
            "posts": posts_data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "category": category_name,
            "folderid": folderid
        }

@router.get("/projects/{project_id}/comments/recent", response_model=List[Dict[str, Any]])
@cache_project_comments()  # 使用环境变量配置的缓存时间
async def get_project_recent_comments(
    project_id: int,
    limit: int = 5,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目的最近评论
    
    Args:
        project_id: 项目ID
        limit: 返回数量限制
        session: 数据库会话
        
    Returns:
        List[Dict[str, Any]]: 最近评论列表
    """
    post_repo = PostRepository(session)
    
    # 获取项目相关的评论（现在包含用户名和文章名）
    comments = await post_repo.get_recent_comments_by_project(project_id, limit)
    
    # 格式化评论数据
    comments_data = []
    for comment in comments:
        # 检查用户头像是否存在
        userid = comment["userid"]
        avatar_path = None
        if userid:
            # 使用统一依赖注入的BlogService来检查头像
            from src.utils.dependencies import get_blog_service
            blog_service = await get_blog_service(session)
            
            avatar_path = blog_service._check_avatar_exists(userid)
        
        comments_data.append({
            "id": comment["id"],
            "author": comment["user_name"],  # 改为author以匹配现有组件
            "content": comment["content"],
            "time": comment["post_time"],    # 改为time以匹配现有组件
            "projectitemid": comment["projectitemid"],
            "userid": comment["userid"],
            "avatar": avatar_path
        })
    
    return comments_data

@router.get("/projects/{project_id}/external-links", response_model=List[Dict[str, Any]])
@cache_project_external_links()  # 使用环境变量配置的缓存时间
async def get_project_external_links(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目的外站链接
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        List[Dict[str, Any]]: 外站链接列表
    """
    # 这里可以根据实际需求实现外站链接逻辑
    # 目前返回模拟数据
    return [
        {"id": 1, "name": "GitHub", "url": "https://github.com", "description": "代码托管平台"},
        {"id": 2, "name": "Stack Overflow", "url": "https://stackoverflow.com", "description": "程序员问答社区"},
        {"id": 3, "name": "掘金", "url": "https://juejin.cn", "description": "开发者社区"}
    ]

@router.get("/projects/{project_id}/rss")
@cache_project_rss()  # 使用环境变量配置的缓存时间
async def get_project_rss(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目的RSS订阅
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        RSS格式的响应
    """
    from fastapi.responses import Response
    
    project_repo = ProjectRepository(session)
    project = await project_repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 生成RSS内容
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>{project.name}</title>
    <description>{project.comment or '博客RSS订阅'}</description>
    <link>http://blogn2.local/blog/{project_id}</link>
    <language>zh-CN</language>
</channel>
</rss>"""
    
    return Response(content=rss_content, media_type="application/xml")

@router.get("/projects/{project_id}/stats", response_model=Dict[str, Any])
@cache_project_stats()  # 使用环境变量配置的缓存时间
async def get_project_stats(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目的统计信息（使用预存储数据，性能更优）
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 项目统计信息
    """
    from src.services.metadata_service import MetadataService
    from src.repositories.user_repository import UserRepository
    from src.repositories.project_item_repository import ProjectItemRepository
    
    user_repo = UserRepository(session)
    post_repo = ProjectItemRepository(session)
    metadata_service = MetadataService(user_repo, post_repo)
    
    try:
        stats = await metadata_service.get_project_stats_from_cache(project_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目统计信息失败: {str(e)}")


@router.get("/projects/user/{user_id}", response_model=Dict[str, Any])
@cache_user_projects()  # 使用环境变量配置的缓存时间
async def get_user_project(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    根据用户ID获取用户的博客信息
    
    Args:
        user_id: 用户ID
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户博客信息
    """
    project_repo = ProjectRepository(session)
    
    try:
        # 根据用户ID查找项目
        project = await project_repo.get_by_user_id_single(user_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="用户博客不存在")
        
        return {
            "id": project.id,
            "name": project.name,
            "comment": project.comment,
            "recordcount": project.recordcount,
            "accesscount": project.accesscount,
            "userid": project.userid,
            "createtime": project.createtime,
            "updatetime": project.updatetime,
            "commentcount": project.commentcount
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户博客信息失败: {str(e)}")

@router.post("/projects/create", response_model=Dict[str, Any])
async def create_project(
    project_data: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session)
):
    """
    创建新博客项目
    
    Args:
        project_data: 包含博客名称和描述的字典
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 新创建的博客信息
    """
    from src.repositories.user_repository import UserRepository
    
    # 验证输入数据
    if not project_data.get("name"):
        raise HTTPException(status_code=400, detail="博客名称不能为空")
    
    if len(project_data["name"]) > 100:
        raise HTTPException(status_code=400, detail="博客名称不能超过100个字符")
    
    if project_data.get("comment") and len(project_data["comment"]) > 500:
        raise HTTPException(status_code=400, detail="博客描述不能超过500个字符")
    
    # 获取当前用户ID（从请求头中的token解析）
    # 这里需要实现用户认证逻辑
    # 暂时从project_data中获取userid，实际应该从token中获取
    userid = project_data.get("userid")
    if not userid:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    try:
        # 开始事务
        async with session.begin():
            # 创建新项目
            project_repo = ProjectRepository(session)
            new_project = Project(
                name=project_data["name"],
                comment=project_data.get("comment"),
                userid=userid,
                createtime=TimeUtils.now_utc(),
                updatetime=TimeUtils.now_utc(),
                state=1,  # 正常状态
                recordcount=0,
                accesscount=0,
                commentcount=0
            )
            
            created_project = await project_repo.create(new_project)
            
            # 更新用户的projectid
            user_repo = UserRepository(session)
            await user_repo.update_projectid(userid, created_project.id)
            
            # 更新全局项目数量统计
            from src.services.global_stats_service import GlobalStatsService
            stats_service = GlobalStatsService(session)
            await stats_service.update_project_count(increment=True)

            payload = {
                "id": created_project.id,
                "name": created_project.name,
                "comment": created_project.comment,
                "userid": created_project.userid,
                "createtime": created_project.createtime,
                "updatetime": created_project.updatetime,
                "state": created_project.state,
            }
        await invalidate_blog_directory_caches(userid)
        return payload

    except Exception as e:
        # 事务会自动回滚
        raise HTTPException(status_code=500, detail=f"创建博客失败: {str(e)}")

@router.post("/projects/create-post", response_model=Dict[str, Any])
async def create_post(
    post_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    创建新的博客文章
    
    Args:
        post_data: 包含文章信息的字典
        current_user: 当前登录用户信息
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 新创建的文章信息
    """
    # 验证输入数据
    if not post_data.get("name"):
        raise HTTPException(status_code=400, detail="文章标题不能为空")
    
    if len(post_data["name"]) > 50:
        raise HTTPException(status_code=400, detail="文章标题不能超过50个字符")
    
    if not post_data.get("comment"):
        raise HTTPException(status_code=400, detail="文章内容不能为空")
    
    # 检查文章内容大小（128KB = 131072字节）
    comment_size = len(post_data["comment"].encode('utf-8'))
    if comment_size > 131072:
        raise HTTPException(status_code=400, detail="文章内容不能超过128KB")
    
    # 验证附件字段（如果提供）
    attachment = post_data.get("attachment")
    if attachment and not isinstance(attachment, str):
        raise HTTPException(status_code=400, detail="附件字段格式不正确")
    
    # 验证项目ID
    project_id = post_data.get("projectid")
    if not project_id:
        raise HTTPException(status_code=400, detail="项目ID不能为空")
    
    try:
        # 验证用户是否有权限在该项目中创建文章
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project.userid != current_user["id"]:
            raise HTTPException(status_code=403, detail="没有权限在此项目中创建文章")
        
        # 创建新文章
        project_item_repo = ProjectItemRepository(session)
        
        # 计算文章内容的字节长度
        comment_content = post_data["comment"]
        itemsize = len(comment_content.encode('utf-8'))

        published_at = TimeUtils.now_utc()
        new_post = ProjectItem(
            projectid=project_id,
            name=post_data["name"],
            comment=comment_content,
            itemtype=post_data.get("itemtype", ArticleStatus.NORMAL),
            itemsize=itemsize,  # 使用实际的文章内容长度
            attachment=attachment,  # 使用上传的图片文件名
            linkstr=None,          # 不再使用相关链接
            userid=current_user["id"],
            accesscount=0,
            commentcount=0,
            folderid=post_data.get("folderid"),
            status=post_data.get("status", 1),
            allowpost=post_data.get("allowpost", 1),
            createtime=published_at,
            updatetime=published_at,
            lastmodifytime=None,
        )
        
        config = validate_app_config()
        upload_dir = config["upload_dir"]
        
        # 处理主图片的临时文件移动
        if new_post.attachment and new_post.attachment.startswith("temp/"):
            try:
                promoted = promote_temp_relative_path(new_post.attachment, upload_dir)
                if promoted:
                    new_post.attachment = promoted
            except Exception:
                logger.exception("临时文件移动失败 attachment=%s", new_post.attachment)
                raise HTTPException(status_code=500, detail="临时文件移动失败")
        
        created_post = await project_item_repo.create(new_post)
        
        # 处理多张图片附件
        attachments_data = post_data.get("attachments", [])
        if attachments_data:
            from src.repositories.attachment_repository import AttachmentRepository
            from src.models.attachment import Attachment
            attachment_repo = AttachmentRepository(session)
            
            for attachment_data in attachments_data:
                # 处理临时文件移动
                relative_path = attachment_data.get("relative_path", "")
                if relative_path.startswith("temp/"):
                    try:
                        promoted = promote_temp_relative_path(relative_path, upload_dir)
                        if promoted:
                            relative_path = promoted
                    except Exception:
                        logger.exception("临时附件移动失败 path=%s", relative_path)
                        raise HTTPException(status_code=500, detail="临时文件移动失败")
                
                # 创建附件记录
                attachment = Attachment(
                    parentid=created_post.id,
                    amtype=1,  # 默认为正常类型
                    comment=attachment_data.get("comment", ""),
                    linkstr=relative_path,
                    createtime=TimeUtils.now_utc(),
                    updatetime=TimeUtils.now_utc()
                )
                await attachment_repo.create(attachment)
        
        # 更新项目的记录数和更新时间
        await project_repo.increment_record_count(project_id)
        
        # 更新用户积分（每发表一篇文章获得10积分，每日最多10分）
        user_repo = UserRepository(session)
        point_added = await user_repo.increment_point(current_user["id"], 10, "article_create")
        
        # 如果达到每日积分限制，记录日志但不影响文章创建
        if not point_added:
            logger.info("用户 %s 今日积分已达上限，未获得积分奖励", current_user["id"])
        
        # 更新全局项目项数量统计
        from src.services.global_stats_service import GlobalStatsService
        stats_service = GlobalStatsService(session)
        await stats_service.update_project_item_count(increment=True)
        
        # 在主事务提交前进行向量化处理
        try:
            from src.services.vectorization_update_service import get_vectorization_update_service
            vectorization_service = get_vectorization_update_service(session)
            
            # 创建向量
            await vectorization_service.update_article_vectors(
                created_post.id, created_post.name, created_post.comment
            )
            
        except Exception as e:
            logger.error("向量化创建失败: %s", e)
        
        # 提交事务（所有操作在同一个事务中）
        await session.commit()

        await invalidate_project_post_list_caches(project_id, project.userid)

        # 广播新文章给所有订阅者
        try:
            from src.services.broadcast_service import BroadcastService
            broadcast_service = BroadcastService(session)
            await broadcast_service.broadcast_new_article(project_id, created_post.id)
        except Exception as e:
            # 广播失败不影响文章创建，静默处理
            pass
        
        return {
            "id": created_post.id,
            "name": created_post.name,
            "comment": created_post.comment,
            "itemtype": created_post.itemtype,
            "itemsize": created_post.itemsize,
            "attachment": created_post.attachment,
            "linkstr": created_post.linkstr,
            "userid": created_post.userid,
            "accesscount": created_post.accesscount,
            "commentcount": created_post.commentcount,
            "folderid": created_post.folderid,
            "status": created_post.status,
            "allowpost": created_post.allowpost,
            "createtime": created_post.createtime,
            "updatetime": created_post.updatetime,
            "lastmodifytime": created_post.lastmodifytime
        }
            
    except HTTPException:
        raise
    except Exception as e:
        # 事务会自动回滚
        raise HTTPException(status_code=500, detail=f"创建文章失败: {str(e)}")

@router.put("/projects/{project_id}")
async def update_project(
    project_id: int,
    project_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    更新项目信息
    
    Args:
        project_id: 项目ID
        project_data: 项目数据
        current_user: 当前用户信息
        session: 数据库会话
        
    Returns:
        Dict: 更新后的项目信息
    """
    try:
        # 获取项目信息
        project_repo = ProjectRepository(session)
        project = await project_repo.get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查权限：只有项目所有者或管理员可以修改
        if current_user["id"] != project.userid and current_user.get("role") not in ["admin", "administrator"]:
            raise HTTPException(status_code=403, detail="没有权限修改此项目")
        
        # 更新项目信息
        update_data = {}
        if "name" in project_data:
            update_data["name"] = project_data["name"]
        if "comment" in project_data:
            update_data["comment"] = project_data["comment"]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的数据")
        
        # 更新项目（project.updatetime 表示博客内容层面的「最后更新」，由已发布文章同步）
        updated_project = await project_repo.update_project(project_id, update_data)
        
        if not updated_project:
            raise HTTPException(status_code=500, detail="更新项目失败")

        await project_repo.sync_updatetime_from_latest_published_article(project_id)
        await session.commit()
        updated_project = await project_repo.get_by_id(project_id)

        await invalidate_project_post_list_caches(project_id, project.userid)

        return {
            "id": updated_project.id,
            "name": updated_project.name,
            "comment": updated_project.comment,
            "userid": updated_project.userid,
            "createtime": updated_project.createtime,
            "updatetime": updated_project.updatetime
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新项目失败: {str(e)}")

@router.get("/projects/{project_id}/categories", response_model=List[Dict[str, Any]])
@cache_project_categories()  # 使用环境变量配置的缓存时间
async def get_project_categories(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    获取项目的分类列表
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        List[Dict]: 分类列表
    """
    try:
        folder_repo = FolderRepository(session)
        categories = await folder_repo.get_by_project_id_with_count(project_id)
        
        # 为每个分类添加颜色（可以根据需要自定义）
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#84cc16', '#f97316']
        
        result = []
        
        # 添加未分类项（folderid=0）
        from src.repositories.project_item_repository import ProjectItemRepository
        project_item_repo = ProjectItemRepository(session)
        uncategorized_count = await project_item_repo.count_by_project_id_and_folder(project_id, 0)
        
        result.append({
            "id": 0,
            "name": "未分类",
            "count": uncategorized_count,
            "color": "#6b7280"
        })
        
        # 添加其他分类
        for i, category in enumerate(categories):
            result.append({
                "id": category["id"],
                "name": category["name"],
                "count": category["recordcount"] or 0,
                "color": colors[i % len(colors)]
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")

@router.post("/projects/{project_id}/categories")
async def create_category(
    project_id: int,
    category_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    创建新分类
    
    Args:
        project_id: 项目ID
        category_data: 分类数据
        current_user: 当前用户信息
        session: 数据库会话
        
    Returns:
        Dict: 创建的分类信息
    """
    try:
        # 检查项目是否存在
        project_repo = ProjectRepository(session)
        project = await project_repo.get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查权限：只有项目所有者可以创建分类
        if current_user["id"] != project.userid:
            raise HTTPException(status_code=403, detail="没有权限创建分类")
        
        # 创建分类
        folder_repo = FolderRepository(session)
        folder = Folder(
            name=category_data["name"].strip(),
            projectid=project_id,
            recordcount=0,
            postcount=0
        )
        
        session.add(folder)
        await session.commit()
        await session.refresh(folder)

        await invalidate_project_categories_cache(project_id)

        return {
            "id": folder.id,
            "name": folder.name,
            "count": 0,
            "color": "#3b82f6"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

@router.put("/projects/{project_id}/categories/{category_id}")
async def update_category(
    project_id: int,
    category_id: int,
    category_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    更新分类
    
    Args:
        project_id: 项目ID
        category_id: 分类ID
        category_data: 分类数据
        current_user: 当前用户信息
        session: 数据库会话
        
    Returns:
        Dict: 更新后的分类信息
    """
    try:
        # 检查项目是否存在
        project_repo = ProjectRepository(session)
        project = await project_repo.get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查权限：只有项目所有者可以更新分类
        if current_user["id"] != project.userid:
            raise HTTPException(status_code=403, detail="没有权限更新分类")
        
        # 检查分类是否存在
        folder_repo = FolderRepository(session)
        folder = await folder_repo.get_by_id(category_id)
        
        if not folder or folder.projectid != project_id:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 更新分类
        folder.name = category_data["name"].strip()
        await session.commit()
        await session.refresh(folder)

        await invalidate_project_categories_cache(project_id)

        return {
            "id": folder.id,
            "name": folder.name,
            "count": folder.recordcount or 0,
            "color": "#3b82f6"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")

@router.delete("/projects/{project_id}/categories/{category_id}")
async def delete_category(
    project_id: int,
    category_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    删除分类
    
    Args:
        project_id: 项目ID
        category_id: 分类ID
        current_user: 当前用户信息
        session: 数据库会话
        
    Returns:
        Dict: 删除结果
    """
    try:
        # 检查项目是否存在
        project_repo = ProjectRepository(session)
        project = await project_repo.get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查权限：只有项目所有者可以删除分类
        if current_user["id"] != project.userid:
            raise HTTPException(status_code=403, detail="没有权限删除分类")
        
        # 检查分类是否存在
        folder_repo = FolderRepository(session)
        folder = await folder_repo.get_by_id(category_id)
        
        if not folder or folder.projectid != project_id:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 检查分类下是否有文章，如果有则设置为未分类
        from src.repositories.post_repository import PostRepository
        post_repo = PostRepository(session)
        updated_articles_count = await post_repo.update_articles_folder_to_uncategorized(category_id)
        
        # 删除分类
        session.delete(folder)
        await session.commit()

        await invalidate_project_categories_cache(project_id)
        await invalidate_project_post_list_caches(project_id, project.userid)

        # 返回删除结果，包含处理的文章数量
        message = "分类删除成功"
        if updated_articles_count > 0:
            message += f"，已将{updated_articles_count}篇文章设置为未分类"
        
        return {
            "message": message,
            "updated_articles_count": updated_articles_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")


@router.post("/admin/projects/recalculate-updatetimes", response_model=Dict[str, Any])
async def admin_recalculate_all_project_updatetimes(
    session: AsyncSession = Depends(get_async_session),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    重新计算所有博客的 project.updatetime（GREATEST(最新发文 createtime, 最新修改 lastmodifytime)，不用文章 updatetime）。
    仅管理员可调用。
    """
    if not permission_manager.can_manage_system(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    try:
        project_repo = ProjectRepository(session)
        n = await project_repo.sync_all_projects_updatetime()
        try:
            from src.utils.cache import cache_manager
            await cache_manager.clear_pattern("project:detail:*")
        except Exception:
            pass
        return {"message": "已重新计算所有博客的更新时间", "project_count": n}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"重新计算失败: {str(e)}")