from sqlmodel import select, func
from sqlalchemy import or_, update
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

from src.models.project import Project
from src.models.user import User
from src.models.project_item import ProjectItem
from src.constants import ArticleStatus


def _published_articles_max_time_expr():
    """单博客内：可见文章 per-item 取 createtime/updatetime/lastmodifytime 最晚，再 max 聚合（标量子查询，与 project 行相关）。"""
    per_item_latest = func.greatest(
        ProjectItem.createtime,
        ProjectItem.updatetime,
        ProjectItem.lastmodifytime,
    )
    return (
        select(func.max(per_item_latest))
        .where(ProjectItem.projectid == Project.id)
        .where(ProjectItem.status == 1)
        .where(
            or_(
                ProjectItem.itemtype.is_(None),
                ProjectItem.itemtype != ArticleStatus.DELETED,
            )
        )
        .scalar_subquery()
    )


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

    async def sync_updatetime_from_latest_published_article(
        self, project_id: int, project: Optional[Project] = None
    ) -> None:
        """
        一条 UPDATE：将 project.updatetime 设为可见文章时间的 max(greatest(...))，
        无文章则为该行 project.createtime。全部在数据库内完成，不用应用层聚合。
        """
        subq = _published_articles_max_time_expr()
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(updatetime=func.coalesce(subq, Project.createtime))
        )
        await self.session.execute(stmt)
        if project is not None:
            await self.session.refresh(project, attribute_names=["updatetime"])

    async def sync_all_projects_updatetime(self) -> int:
        """一条 UPDATE 重算所有博客的 updatetime，并 commit。"""
        subq = _published_articles_max_time_expr()
        stmt = update(Project).values(
            updatetime=func.coalesce(subq, Project.createtime)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount or 0
    
    async def increment_record_count(self, project_id: int) -> None:
        """增加项目的记录数"""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.exec(statement)
        project = result.first()
        
        if project:
            project.recordcount = (project.recordcount or 0) + 1
            await self.sync_updatetime_from_latest_published_article(project_id, project)
    
    async def decrement_record_count(self, project_id: int) -> None:
        """减少项目的记录数"""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.exec(statement)
        project = result.first()
        
        if project:
            project.recordcount = max((project.recordcount or 0) - 1, 0)
            await self.sync_updatetime_from_latest_published_article(project_id, project)
    
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
            return None 
    
    async def increment_access_count(self, project_id: int) -> bool:
        """
        增加项目的访问次数
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 使用SQLModel的方式更新，避免原始SQL的同步问题
            from src.utils.time_utils import TimeUtils
            
            project = await self.get_by_id(project_id)
            if project:
                project.accesscount = (project.accesscount or 0) + 1
                self.session.add(project)
                await self.session.commit()
                return True
            else:
                return False
        except Exception as e:
            return False