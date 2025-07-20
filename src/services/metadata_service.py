from typing import Dict, Any
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository

class MetadataService:
    """网站元数据业务逻辑服务类
    
    提供网站统计信息和元数据的业务逻辑处理。
    """
    
    def __init__(self, user_repo: UserRepository, post_repo: ProjectItemRepository):
        self.user_repo = user_repo
        self.post_repo = post_repo
    
    async def get_metadata_dict(self) -> Dict[str, Any]:
        """获取网站元数据"""
        # 获取统计数据
        user_count = await self.user_repo.count()
        post_count = await self.post_repo.count()
        
        # 构建元数据
        metadata = {
            "site_name": "BlogN",
            "version": "V1",
            "logo_url": "/static/images/logo-light.svg",
            "user_count": user_count,
            "post_count": post_count
        }
        
        return metadata 