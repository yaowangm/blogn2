from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict, Any

from src.config.database import get_async_session
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.services.metadata_service import MetadataService

# 创建路由器
router = APIRouter()

def get_metadata_service(session: AsyncSession = Depends(get_async_session)) -> MetadataService:
    """依赖注入：创建元数据服务实例"""
    user_repo = UserRepository(session)
    post_repo = ProjectItemRepository(session)
    return MetadataService(user_repo, post_repo)

@router.get("/metadata/", response_model=Dict[str, Any])
async def get_site_metadata(
    metadata_service: MetadataService = Depends(get_metadata_service)
):
    """
    获取网站元数据 (完整MVC架构版本)
    访问地址: http://localhost:8000/api/metadata/mvc
    """
    try:
        return await metadata_service.get_metadata_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取网站元数据失败: {str(e)}"
        ) 