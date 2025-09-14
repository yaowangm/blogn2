from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

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
    cache_project_stats, cache_user_projects
)
from src.utils.auth_dependencies import get_current_user, get_optional_current_user
from src.utils.permission_manager import permission_manager
from src.constants import ArticleStatus
from src.utils.file_utils import get_temp_dir

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
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 检查是否为管理员，决定是否包含已删除的文章
        is_admin = permission_manager.can_manage_system(current_user)
        should_include_deleted = include_deleted and is_admin
        
        # 获取文章列表
        posts = await project_item_repo.get_by_project_id_and_folder(project_id, folderid, limit, offset, should_include_deleted)
        
        # 获取总数 - 使用预存储的recordcount字段，避免实时查询
        if folderid:
            # 如果指定了文件夹，直接从folders表获取
            folder_repo = FolderRepository(session)
            try:
                folder = await folder_repo.get_by_id(folderid)
                if folder and folder.recordcount is not None:
                    total = folder.recordcount
                else:
                    # 如果recordcount为空，回退到实时查询
                    total = await project_item_repo.count_by_project_id_and_folder(project_id, folderid)
            except:
                # 如果获取失败，回退到实时查询
                total = await project_item_repo.count_by_project_id_and_folder(project_id, folderid)
        else:
            # 如果没有指定文件夹，统计项目下所有文件夹的文章总数
            total = await project_item_repo.get_count_from_folder_recordcount(project_id)
        
        # 获取分类信息
        category_name = "全部文章"
        if folderid:
            folder_repo = FolderRepository(session)
            try:
                folder = await folder_repo.get_by_id(folderid)
                if folder:
                    category_name = folder.name
            except:
                pass
        
        # 转换为字典格式
        posts_data = []
        for post in posts:
            # 生成头像路径
            avatar_path = None
            if post["userid"]:
                prefix = (post["userid"] // 10000) + 1
                avatar_path = f"/avatar/{prefix}/s_{post['userid']}.jpg"
            
            posts_data.append({
                "id": post["id"],
                "name": post["name"],
                "comment": post["comment"],
                "createtime": post["createtime"],
                "accesscount": post["accesscount"],
                "commentcount": post["commentcount"],
                "category": category_name,
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
            prefix = (userid // 10000) + 1
            avatar_path = f"/avatar/{prefix}/s_{userid}.jpg"
        
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

@router.get("/projects/{project_id}/categories", response_model=List[Dict[str, Any]])
@cache_project_categories()  # 使用环境变量配置的缓存时间
async def get_project_categories(
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定项目的分类列表
    
    Args:
        project_id: 项目ID
        session: 数据库会话
        
    Returns:
        List[Dict[str, Any]]: 分类列表
    """
    folder_repo = FolderRepository(session)
    
    try:
        # 从数据库获取项目的文件夹列表
        folders = await folder_repo.get_by_project_id(project_id)
        
        # 转换为API响应格式
        categories = []
        for folder in folders:
            categories.append({
                "id": folder.id,
                "name": folder.name,
                "count": folder.recordcount or 0,  # 使用folders表中的recordcount字段
                "color": "#3b82f6"  # 默认颜色
            })
        
        return categories
        
    except Exception as e:
        # 如果获取失败，返回空列表
        return []

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
                createtime=datetime.now(),
                updatetime=datetime.now(),
                state=1,  # 正常状态
                recordcount=0,
                accesscount=0,
                commentcount=0
            )
            
            created_project = await project_repo.create(new_project)
            
            # 更新用户的projectid
            user_repo = UserRepository(session)
            await user_repo.update_projectid(userid, created_project.id)
            
            return {
                "id": created_project.id,
                "name": created_project.name,
                "comment": created_project.comment,
                "userid": created_project.userid,
                "createtime": created_project.createtime,
                "updatetime": created_project.updatetime,
                "state": created_project.state
            }
            
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
            createtime=datetime.now(),
            updatetime=datetime.now(),
            lastmodifytime=datetime.now()
        )
        
        # 处理临时文件移动
        import os
        from src.config.app import validate_app_config
        
        # 获取上传目录配置
        config = validate_app_config()
        upload_dir = config["upload_dir"]
        
        # 处理主图片的临时文件移动
        if new_post.attachment and new_post.attachment.startswith("temp/"):
            try:
                # 从临时目录移动到正式目录
                temp_filename = new_post.attachment.replace("temp/", "")
                temp_path = os.path.join(get_temp_dir(), temp_filename)
                
                if os.path.exists(temp_path):
                    # 创建按月份命名的子目录
                    current_time = datetime.now()
                    month_dir = current_time.strftime("%Y%m")
                    monthly_upload_path = os.path.join(upload_dir, month_dir)
                    os.makedirs(monthly_upload_path, exist_ok=True)
                    
                    # 移动到正式目录
                    final_filename = temp_filename
                    final_path = os.path.join(monthly_upload_path, final_filename)
                    os.rename(temp_path, final_path)
                    
                    # 更新attachment路径
                    new_post.attachment = f"{month_dir}/{final_filename}"
                    
                else:
                    pass  # 临时文件不存在，继续处理
            except Exception as e:
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
                        # 从临时目录移动到正式目录
                        temp_filename = relative_path.replace("temp/", "")
                        temp_path = os.path.join(get_temp_dir(), temp_filename)
                        
                        if os.path.exists(temp_path):
                            # 创建按月份命名的子目录
                            current_time = datetime.now()
                            month_dir = current_time.strftime("%Y%m")
                            monthly_upload_path = os.path.join(upload_dir, month_dir)
                            os.makedirs(monthly_upload_path, exist_ok=True)
                            
                            # 移动到正式目录
                            final_filename = temp_filename
                            final_path = os.path.join(monthly_upload_path, final_filename)
                            os.rename(temp_path, final_path)
                            
                            # 更新路径
                            relative_path = f"{month_dir}/{final_filename}"
                            
                        else:
                            pass  # 临时文件不存在，继续处理
                    except Exception as e:
                        raise HTTPException(status_code=500, detail="临时文件移动失败")
                
                # 创建附件记录
                attachment = Attachment(
                    parentid=created_post.id,
                    amtype=1,  # 默认为正常类型
                    comment=attachment_data.get("comment", ""),
                    linkstr=relative_path,
                    createtime=datetime.now(),
                    updatetime=datetime.now()
                )
                await attachment_repo.create(attachment)
        
        # 更新项目的记录数和更新时间
        await project_repo.increment_record_count(project_id)
        
        # 更新用户积分（每发表一篇文章获得10积分）
        from src.repositories.user_repository import UserRepository
        user_repo = UserRepository(session)
        await user_repo.increment_point(current_user["id"], 10)
        
        # 提交事务（所有操作在同一个事务中）
        await session.commit()
        
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