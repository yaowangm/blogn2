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
        """根据项目ID获取所有文件夹，按ID倒序排序"""
        statement = select(Folder).where(Folder.projectid == project_id).order_by(Folder.id.desc())
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_by_project_id_with_count(self, project_id: int) -> List[dict]:
        """根据项目ID获取文件夹及其文章数量"""
        # 使用folders表中的recordcount字段
        folders = await self.get_by_project_id(project_id)
        return [{"id": folder.id, "name": folder.name.strip() if folder.name else "", "parent": folder.parent, "recordcount": folder.recordcount} for folder in folders]
    
    async def count_by_project_id(self, project_id: int) -> int:
        """统计项目下的文件夹数量"""
        statement = select(Folder).where(Folder.projectid == project_id)
        result = await self.session.exec(statement)
        return len(result.all())
    
    async def increment_record_count(self, folder_id: int) -> bool:
        """增加分类的文章数量
        
        Args:
            folder_id: 分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            folder = await self.get_by_id(folder_id)
            if folder:
                folder.recordcount = (folder.recordcount or 0) + 1
                await self.session.commit()
                await self.session.refresh(folder)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            print(f"Error incrementing record count: {e}")
            return False
    
    async def decrement_record_count(self, folder_id: int) -> bool:
        """减少分类的文章数量
        
        Args:
            folder_id: 分类ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            folder = await self.get_by_id(folder_id)
            if folder and folder.recordcount and folder.recordcount > 0:
                folder.recordcount -= 1
                await self.session.commit()
                await self.session.refresh(folder)
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            print(f"Error decrementing record count: {e}")
            return False
