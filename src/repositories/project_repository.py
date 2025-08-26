from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from src.models.project import Project
from src.models.user import User

class ProjectRepository:
    """Project数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_popular_projects(self, limit: int = 10) -> List[dict]:
        """获取最热门的项目（按访问量排序）"""
        statement = (
            select(Project.id, Project.name, Project.accesscount, Project.userid, Project.createtime, User.name.label("author_name"))
            .join(User, Project.userid == User.id)
            .where(Project.state == 0)  # 数据库中state=0表示正常状态
            .order_by(Project.accesscount.desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        items = result.all()
        return [{"id": item[0], "name": item[1], "accesscount": item[2] or 0, "userid": item[3], "createtime": item[4], "author_name": item[5]} for item in items]
    
    async def get_recent_projects(self, limit: int = 10) -> List[dict]:
        """获取最新创建的项目（按创建时间倒序）"""
        statement = (
            select(Project.id, Project.name, Project.createtime, Project.userid, User.name.label("author_name"))
            .join(User, Project.userid == User.id)
            .where(Project.state == 0)  # 数据库中state=0表示正常状态
            .order_by(Project.createtime.desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        items = result.all()
        return [{"id": item[0], "name": item[1], "createtime": item[2], "userid": item[3], "author_name": item[4]} for item in items]
    
    async def count(self) -> int:
        """获取项目总数"""
        result = await self.session.exec(select(func.count(Project.id)))
        return result.first() or 0
    
    async def get_by_id(self, id: int) -> Optional[Project]:
        """根据ID获取项目"""
        statement = select(Project).where(Project.id == id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_user_id(self, user_id: int, limit: int = None) -> List[Project]:
        """根据用户ID获取项目列表"""
        statement = select(Project).where(Project.userid == user_id)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_by_user_id_single(self, user_id: int) -> Optional[Project]:
        """根据用户ID获取单个项目（一对一关系）"""
        statement = select(Project).where(Project.userid == user_id)
        result = await self.session.exec(statement)
        return result.first() 