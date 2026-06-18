from typing import Dict, Any
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.services.base_service import BaseService

class MetadataService(BaseService):
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
            "logo_url": "/static/favicon.svg",
            "user_count": user_count,
            "post_count": post_count
        }
        
        return metadata
    
    async def get_project_stats_from_cache(self, project_id: int) -> Dict[str, int]:
        """
        从预存储的统计字段获取项目统计信息，避免实时查询
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict[str, int]: 项目统计信息
        """
        from src.repositories.project_repository import ProjectRepository
        from src.repositories.folder_repository import FolderRepository
        
        project_repo = ProjectRepository(self.post_repo.session)
        folder_repo = FolderRepository(self.post_repo.session)
        
        # 获取项目信息
        project = await project_repo.get_by_id(project_id)
        if not project:
            return {"error": "项目不存在"}
        
        # 获取项目下的文件夹统计
        folders = await folder_repo.get_by_project_id(project_id)
        total_posts = sum(folder.recordcount or 0 for folder in folders)
        
        return {
            "project_id": project_id,
            "total_posts": total_posts,
            "comment_count": project.commentcount or 0,
            "access_count": project.accesscount or 0
        } 
