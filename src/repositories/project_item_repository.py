from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from src.models.project_item import ProjectItem
from src.models.user import User

class ProjectItemRepository:
    """项目项数据访问层
    
    提供项目项数据的CRUD操作，包括查询、统计等功能。
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def count(self) -> int:
        """获取项目项总数"""
        statement = select(func.count(ProjectItem.id))
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_by_id(self, id: int) -> Optional[ProjectItem]:
        """根据ID获取项目项"""
        statement = select(ProjectItem).where(ProjectItem.id == id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_user_id(self, user_id: int, limit: int = None) -> List[ProjectItem]:
        """根据用户ID获取项目项"""
        statement = select(ProjectItem).where(ProjectItem.userid == user_id)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_by_project_id(self, project_id: int, limit: int = None) -> List[ProjectItem]:
        """根据项目ID获取项目项"""
        statement = select(ProjectItem).where(ProjectItem.projectid == project_id)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def count_by_project_id(self, project_id: int) -> int:
        """根据项目ID获取项目项总数"""
        statement = select(func.count(ProjectItem.id)).where(ProjectItem.projectid == project_id)
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_recent_items(self, limit: int = 10) -> List[ProjectItem]:
        """获取最近创建的项目项"""
        statement = select(ProjectItem).order_by(ProjectItem.createtime.desc()).limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_popular_items(self, limit: int = 10) -> List[ProjectItem]:
        """获取最受欢迎的项目项（按访问次数）"""
        statement = select(ProjectItem).order_by(ProjectItem.accesscount.desc()).limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_latest_posts(self, limit: int = 5) -> List[dict]:
        """获取最新的博文记录"""
        query = (
            select(ProjectItem, User.name.label("author_name"))
            .join(User, ProjectItem.userid == User.id)
            .where(ProjectItem.status == 1)  # 只获取正常状态的博文
            .order_by(ProjectItem.createtime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        posts = []
        
        for project_item, author_name in result:
            posts.append({
                "id": project_item.id,
                "name": project_item.name,
                "comment": project_item.comment,
                "attachment": project_item.attachment,
                "author_name": author_name,
                "createtime": project_item.createtime,
                "userid": project_item.userid
            })
        
        return posts 