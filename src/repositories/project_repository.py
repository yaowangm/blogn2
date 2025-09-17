from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from src.models.project import Project
from src.models.user import User
from src.utils.time_utils import TimeUtils

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
    
    async def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """根据ID获取项目"""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.exec(statement)
        return result.first()
    
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
    
    async def create(self, project: Project) -> Project:
        """创建新项目"""
        self.session.add(project)
        # 不在这里commit，由外层事务管理器控制
        await self.session.flush()  # 刷新以获取生成的ID
        return project
    
    async def increment_record_count(self, project_id: int) -> None:
        """增加项目的记录数"""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.exec(statement)
        project = result.first()
        
        if project:
            project.recordcount = (project.recordcount or 0) + 1
            project.updatetime = TimeUtils.now_utc()
            self.session.add(project)
    
    async def decrement_record_count(self, project_id: int) -> None:
        """减少项目的记录数"""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.exec(statement)
        project = result.first()
        
        if project:
            project.recordcount = max((project.recordcount or 0) - 1, 0)
            project.updatetime = TimeUtils.now_utc()
            self.session.add(project)
    
    async def increment_comment_count(self, project_id: int) -> bool:
        """
        增加项目的评论数量
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        project = await self.get_by_id(project_id)
        if project:
            project.commentcount = (project.commentcount or 0) + 1
            project.updatetime = TimeUtils.now_utc()
            await self.session.commit()
            await self.session.refresh(project)
            return True
        return False
    
    async def decrement_comment_count(self, project_id: int) -> bool:
        """
        减少项目的评论数量
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        project = await self.get_by_id(project_id)
        if project and project.commentcount > 0:
            project.commentcount -= 1
            project.updatetime = TimeUtils.now_utc()
            await self.session.commit()
            await self.session.refresh(project)
            return True
        return False

    async def update_project(self, project_id: int, update_data: dict) -> Optional[Project]:
        """
        更新项目信息
        
        Args:
            project_id: 项目ID
            update_data: 要更新的数据
            
        Returns:
            Optional[Project]: 更新后的项目对象，如果失败返回None
        """
        try:
            project = await self.get_by_id(project_id)
            if not project:
                return None
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            # 保存更改
            await self.session.commit()
            await self.session.refresh(project)
            return project
            
        except Exception as e:
            await self.session.rollback()
            print(f"更新项目失败: {str(e)}")
            return None 