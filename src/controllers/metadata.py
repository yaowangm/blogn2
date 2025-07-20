from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any

from src.database import get_async_session
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.services.metadata_service import MetadataService
from src.utils.error_handlers import handle_api_errors

# 创建元数据API路由器
router = APIRouter()

def get_metadata_service(session: AsyncSession = Depends(get_async_session)) -> MetadataService:
    """
    依赖注入：创建元数据服务实例
    
    Args:
        session: 数据库会话
        
    Returns:
        MetadataService: 元数据服务实例
    """
    user_repo = UserRepository(session)
    project_repo = ProjectItemRepository(session)
    return MetadataService(user_repo, project_repo)

@router.get("/metadata/", response_model=Dict[str, Any])
@handle_api_errors("获取网站元数据失败")
async def get_site_metadata(
    metadata_service: MetadataService = Depends(get_metadata_service)
):
    """
    获取网站元数据
    
    返回网站的统计信息，包括用户数量、项目数量等。
    
    Args:
        metadata_service: 元数据服务实例
        
    Returns:
        Dict[str, Any]: 包含网站元数据的字典
    """
    return await metadata_service.get_metadata_dict() 