"""
用户控制器

⚠️ 重要提醒：任何AI助手都不得在没有用户明确要求的情况下进行git commit或push操作！
请参考 DEVELOPMENT_RULES.md 了解完整的开发规则。
"""

from typing import List, Dict, Any, Optional
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import User, get_async_session
from src.models.user_response import (
    UserPublicResponse, UserPrivateResponse, UserListResponse, 
    UserSummaryResponse, UserProfileResponse,
    create_user_public_response, create_user_private_response,
    create_user_list_response, create_user_summary_response,
    create_user_profile_response
)
from src.services.user_service import UserService
from src.utils.auth_dependencies import get_optional_current_user, get_current_user
from src.utils.cache import cache_user_profile, cache_user_blogs, cache_user_summary, cache_user_count, cache_new_users
from src.utils.dependencies import get_user_service
from src.utils.error_handlers import handle_api_errors
from src.utils.permission_decorators import require_auth
from src.utils.permission_manager import permission_manager
from src.utils.permission_utils import PermissionUtils
from src.utils.response_utils import ResponseUtils

# 创建用户API路由器
router = APIRouter()

@router.get("/users/summary", response_model=Dict[str, Any])
@handle_api_errors("获取用户摘要失败")
@cache_user_summary()  # 使用默认缓存时间
async def get_user_summary(
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户统计摘要
    
    返回用户总数和最近注册的用户列表（不包含敏感信息）。
    
    Args:
        user_service: 用户服务实例
        
    Returns:
        Dict[str, Any]: 包含用户统计信息的字典
    """
    summary = await user_service.get_user_summary()
    
    # 使用安全的响应模型格式化最近用户数据
    if "recent_users" in summary:
        summary["recent_users"] = [
            create_user_summary_response(user).dict() 
            for user in summary["recent_users"]
        ]
    
    return summary

@router.get("/users/listnew", response_model=List[UserPublicResponse])
@handle_api_errors("获取最新用户失败")
@cache_new_users()  # 使用默认缓存时间
async def get_new_users(
    user_service: UserService = Depends(get_user_service)
):
    """
    获取最新注册的用户列表
    
    返回最近注册的3个用户信息（不包含敏感信息）。
    
    Args:
        user_service: 用户服务实例
        
    Returns:
        List[UserPublicResponse]: 最新用户列表（公开信息）
    """
    users = await user_service.get_top_users(3)
    
    # 使用安全的响应模型格式化用户数据
    return [
        create_user_public_response({
            "id": user.id,
            "name": user.name,
            "state": user.state,
            "regtime": user.regtime,
            "projectid": user.projectid,
            "intropiid": user.intropiid,
            "lastupdate": user.lastupdate
        })
        for user in users
    ]

@router.get("/users/count")
@handle_api_errors("获取用户总数失败")
@cache_user_count()  # 使用默认缓存时间
async def get_user_count(
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户总数
    
    Args:
        user_service: 用户服务实例
        
    Returns:
        Dict[str, int]: 包含用户总数的字典
    """
    count = await user_service.get_user_count()
    return {"count": count}

@router.get("/users/list", response_model=Dict[str, Any])
@handle_api_errors("获取用户列表失败")
@require_auth(admin_only=True)
async def get_users_list(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户列表（仅管理员可访问）
    
    支持分页和搜索功能，返回用户的基本信息包括：
    - id: 用户ID
    - name: 用户名
    - state: 用户状态
    - regtime: 注册时间
    - point: 积分
    - projectid: 项目ID（博客链接）
    - project_name: 项目名称
    
    注意：不包含密码等敏感信息
    
    Args:
        page: 页码，从1开始，默认1
        page_size: 每页大小，默认20，最大100
        search: 搜索关键词，对用户名进行模糊匹配，可选
        user_service: 用户服务实例
        current_user: 当前登录用户信息（必须是管理员）
        
    Returns:
        Dict[str, Any]: 包含用户列表和分页信息的字典
        
    Raises:
        HTTPException: 当用户不是管理员时抛出403错误
    """
    # 验证和规范化分页参数
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    
    return await user_service.get_users_paginated(page, page_size, search)

@router.get("/users/{user_id}", response_model=UserProfileResponse)
@handle_api_errors("获取用户信息失败")
# 注意：不缓存用户个人资料，因为包含敏感信息
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    根据用户ID获取用户信息
    
    权限控制：
    - 如果查看自己的资料，返回完整信息（不包含密码）
    - 如果查看其他用户的资料，返回公开信息
    - 管理员可查看任何用户的完整信息（不包含密码）
    
    安全说明：
    - 密码字段永远不会包含在API响应中
    - 此API包含敏感信息，要求不缓存以防止信息泄露
    
    Args:
        user_id: 用户ID
        user_service: 用户服务实例
        current_user: 当前登录用户信息（可选）
        
    Returns:
        UserProfileResponse: 包含用户信息和权限标记的响应模型
        
    Raises:
        HTTPException: 当用户不存在时抛出404错误
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 使用权限管理器检查是否可以查看个人资料
    if not permission_manager.can_view_profile(current_user, user_id, user.state):
        raise HTTPException(status_code=403, detail="无权限查看该用户资料")
    
    # 获取权限配置
    permissions = permission_manager.get_profile_data_permissions(current_user, user_id)
    
    # 准备用户数据（不包含密码）
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "state": user.state,
        "regtime": user.regtime,
        "iplog": user.iplog,
        "point": user.point,
        "projectid": user.projectid,
        "lastupdate": user.lastupdate,
        "intropiid": user.intropiid
        # 注意：密码字段被故意排除
    }
    
    # 使用安全的响应模型创建响应
    return create_user_profile_response(user_data, permissions)

@router.post("/users/set-intro")
@handle_api_errors("设置个人介绍失败")
@require_auth()
async def set_user_intro(
    request_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    设置用户个人介绍
    
    将指定文章设为用户的个人介绍，并复制文章的附件图片为头像
    
    Args:
        request_data: 包含文章ID的数据 {"article_id": 123}
        current_user: 当前登录用户信息
        session: 数据库会话
        
    Returns:
        Dict[str, Any]: 设置结果
        
    Raises:
        HTTPException: 当文章不存在或无权限时
    """
    from src.repositories.project_item_repository import ProjectItemRepository
    from src.repositories.user_repository import UserRepository
    from src.services.user_service import UserService
    from src.utils.image_utils import ImageProcessor
    
    article_id = request_data.get("article_id")
    if not article_id:
        raise HTTPException(status_code=400, detail="文章ID不能为空")
    
    try:
        # 获取文章信息
        project_item_repo = ProjectItemRepository(session)
        article = await project_item_repo.get_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 检查权限：只有文章作者可以设置
        if article.userid != current_user["id"]:
            raise HTTPException(status_code=403, detail="无权限设置此文章为个人介绍")
        
        # 检查文章是否有附件图片
        if not article.attachment:
            raise HTTPException(status_code=400, detail="此文章没有附件图片，无法设为个人介绍")
        
        # 更新用户的intropiid字段
        user_repo = UserRepository(session)
        update_success = await user_repo.update_intropiid(current_user["id"], article_id)
        if not update_success:
            raise HTTPException(status_code=500, detail="更新用户intropiid失败")
        
        # 处理头像图片复制和resize
        try:
            # 获取上传目录和头像目录配置
            from src.config.app import get_upload_dir, validate_app_config
            upload_dir = get_upload_dir()
            config = validate_app_config()
            avatar_dir = config["avatar_dir"]
            
            # 构建源文件路径
            source_path = os.path.join(upload_dir, article.attachment)
            
            if not os.path.exists(source_path):
                raise HTTPException(status_code=404, detail="附件图片文件不存在")
            
            # 创建头像目录（如果不存在）
            user_id = current_user["id"]
            prefix = (user_id // 10000) + 1
            avatar_user_dir = os.path.join(avatar_dir, str(prefix))
            os.makedirs(avatar_user_dir, exist_ok=True)
            
            # 创建图片处理器
            image_processor = ImageProcessor()
            
            # 创建小头像 (s_userid.jpg) - 用于列表显示
            small_avatar_filename = f"s_{user_id}.jpg"
            small_avatar_path = os.path.join(avatar_user_dir, small_avatar_filename)
            await image_processor.resize_and_save_image(
                source_path=source_path,
                target_path=small_avatar_path,
                max_size=(100, 100)  # 小头像尺寸
            )
            
            # 创建大头像 (userid.jpg) - 用于用户资料页面
            large_avatar_filename = f"{user_id}.jpg"
            large_avatar_path = os.path.join(avatar_user_dir, large_avatar_filename)
            await image_processor.resize_and_save_image(
                source_path=source_path,
                target_path=large_avatar_path,
                max_size=(200, 200)  # 大头像尺寸
            )
            
        except Exception as e:
            # 如果图片处理失败，记录错误但不影响intropiid的设置
            # 使用日志记录而不是print
            import logging
            logging.warning(f"Failed to process avatar image: {e}")
        
        return {
            "success": True,
            "message": "个人介绍设置成功",
            "article_id": article_id,
            "article_title": article.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置个人介绍失败: {str(e)}")

@router.post("/users/{user_id}/reset-password")
@handle_api_errors("重置密码失败")
@require_auth()
async def reset_user_password(
    user_id: int,
    password_data: Dict[str, str],
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    重置用户密码
    
    权限控制：
    - 管理员可以重置任何用户的密码
    - 普通用户只能重置自己的密码
    
    Args:
        user_id: 要重置密码的用户ID
        password_data: 包含新密码的数据 {"new_password": "新密码"}
        user_service: 用户服务实例
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, str]: 重置结果
        
    Raises:
        HTTPException: 当无权限或用户不存在时
    """
    # 检查目标用户是否存在
    target_user = await user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查：管理员可以重置任何用户的密码，普通用户只能重置自己的密码
    if not PermissionUtils.can_manage_resource(current_user, user_id):
        raise ResponseUtils.forbidden_response("无权限重置该用户的密码")
    
    # 验证新密码
    new_password = password_data.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6位")
    
    # 调用用户服务重置密码
    await user_service.reset_user_password(user_id, new_password)
    return {"message": "密码重置成功"}

@router.post("/users/{user_id}/update-email")
@handle_api_errors("修改邮箱失败")
@require_auth()
async def update_user_email(
    user_id: int,
    email_data: Dict[str, str],
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    修改用户邮箱
    
    权限控制：
    - 管理员可以修改任何用户的邮箱
    - 普通用户只能修改自己的邮箱
    
    Args:
        user_id: 要修改邮箱的用户ID
        email_data: 包含新邮箱的数据 {"new_email": "新邮箱"}
        user_service: 用户服务实例
        current_user: 当前登录用户信息
        
    Returns:
        Dict[str, str]: 修改结果
        
    Raises:
        HTTPException: 当无权限或用户不存在时
    """
    # 检查目标用户是否存在
    target_user = await user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查：管理员可以修改任何用户的邮箱，普通用户只能修改自己的邮箱
    if not PermissionUtils.can_manage_resource(current_user, user_id):
        raise ResponseUtils.forbidden_response("无权限修改该用户的邮箱")
    
    # 验证新邮箱
    new_email = email_data.get("new_email")
    if not new_email:
        raise HTTPException(status_code=400, detail="新邮箱不能为空")
    
    # 调用用户服务修改邮箱
    await user_service.update_user_email(user_id, new_email)
    return {"message": "邮箱修改成功"}

@router.post("/users/{user_id}/freeze")
@handle_api_errors("冻结用户失败")
@require_auth(admin_only=True)
async def freeze_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    冻结用户（仅管理员）
    
    将指定用户的状态设置为冻结（state=2），冻结后用户无法登录。
    
    Args:
        user_id: 要冻结的用户ID
        user_service: 用户服务实例
        current_user: 当前登录用户信息（必须是管理员）
        
    Returns:
        Dict[str, str]: 冻结结果
        
    Raises:
        HTTPException: 当用户不存在或已经是管理员时
    """
    # 检查目标用户是否存在
    target_user = await user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能冻结管理员
    if target_user.state == 10:
        raise HTTPException(status_code=400, detail="不能冻结管理员用户")
    
    # 调用用户服务冻结用户
    await user_service.freeze_user(user_id)
    return {"message": "用户冻结成功"}

@router.post("/users/{user_id}/restore")
@handle_api_errors("恢复用户失败")
@require_auth(admin_only=True)
async def restore_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    恢复用户（仅管理员）
    
    将指定用户的状态设置为正常（state=1），恢复后用户可以正常登录。
    
    Args:
        user_id: 要恢复的用户ID
        user_service: 用户服务实例
        current_user: 当前登录用户信息（必须是管理员）
        
    Returns:
        Dict[str, str]: 恢复结果
        
    Raises:
        HTTPException: 当用户不存在时
    """
    # 检查目标用户是否存在
    target_user = await user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 调用用户服务恢复用户
    await user_service.restore_user(user_id)
    return {"message": "用户恢复成功"}