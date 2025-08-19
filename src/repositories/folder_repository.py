from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from src.models.folder import Folder

class FolderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, folder_id: int) -> Optional[Folder]:
        """根据ID获取文件夹"""
        statement = select(Folder).where(Folder.id == folder_id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_project_id(self, project_id: int) -> List[Folder]:
        """根据项目ID获取所有文件夹"""
        statement = select(Folder).where(Folder.projectid == project_id)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_by_project_id_with_count(self, project_id: int) -> List[dict]:
        """根据项目ID获取文件夹及其文章数量"""
        # 使用folders表中的recordcount字段
        folders = await self.get_by_project_id(project_id)
        return [{"id": folder.id, "name": folder.name, "parent": folder.parent, "recordcount": folder.recordcount} for folder in folders]
    
    async def count_by_project_id(self, project_id: int) -> int:
        """统计项目下的文件夹数量"""
        statement = select(Folder).where(Folder.projectid == project_id)
        result = await self.session.exec(statement)
        return len(result.all())
