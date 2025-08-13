from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.services.metadata_service import MetadataService
from src.utils.error_handlers import handle_api_errors
from src.utils.dependencies import get_metadata_service
from src.utils.cache import cache_metadata

# 创建元数据API路由器
router = APIRouter()

@router.get("/metadata/", response_model=Dict[str, Any])
@handle_api_errors("获取网站元数据失败")
@cache_metadata()  # 使用默认缓存时间
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