from sqlmodel import select, func
from sqlalchemy import or_, update
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

from src.models.project import Project
from src.models.user import User
from src.models.project_item import ProjectItem
from src.constants import ArticleStatus, ProjectStatus


def _blog_updatetime_from_articles_expr():
    """
    与当前 project 行相关：可见文章上 MAX(createtime) 与 MAX(lastmodifytime) 取 GREATEST；
    最外层 COALESCE(..., project.createtime) 用于「没有任何一条可见文章」时（空博客、或
    全部文章都不满足 status/itemtype 条件），而不是说「文章没填 createtime」。
    正常发表的文章都会带 createtime；若无可见行，两个 MAX 在 SQL 里均为 NULL，GREATEST
    亦为 NULL，此时用博客自身的创建时间作为 project.updatetime。不使用 projectitem.updatetime。
    """
    visible = (
        ProjectItem.projectid == Project.id,
        ProjectItem.status == 1,
        or_(
            ProjectItem.itemtype.is_(None),
            ProjectItem.itemtype != ArticleStatus.DELETED,
        ),
    )
    max_createtime = (
        select(func.max(ProjectItem.createtime)).where(*visible).scalar_subquery()
    )
    max_lastmodify = (
        select(func.max(ProjectItem.lastmodifytime)).where(*visible).scalar_subquery()
    )
    return func.coalesce(func.greatest(max_createtime, max_lastmodify), Project.createtime)


class ProjectRepository:
    """Project数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_popular_projects(self, limit: int = 10) -> List[dict]:
        """获取最热门的项目（按访问量排序）"""
        statement = (
            select(Project.id, Project.name, Project.accesscount, Project.userid, Project.createtime, User.name.label("author_name"))
            .join(User, Project.userid == User.id)
            .where(Project.state == ProjectStatus.ACTIVE)
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
            .where(Project.state == ProjectStatus.ACTIVE)
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
        一条 UPDATE：GREATEST(MAX(可见 createtime), MAX(可见 lastmodifytime))，再 COALESCE
        到 project.createtime（仅当该博客下没有任何「可见」文章时两个 MAX 全为 NULL）。
        不使用 projectitem.updatetime。
        """
        rhs = _blog_updatetime_from_articles_expr()
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(updatetime=rhs)
        )
        await self.session.execute(stmt)
        if project is not None:
            await self.session.refresh(project, attribute_names=["updatetime"])

    async def sync_all_projects_updatetime(self) -> int:
        """一条 UPDATE 重算所有博客的 updatetime，并 commit。"""
        stmt = update(Project).values(updatetime=_blog_updatetime_from_articles_expr())
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
        result = await self.session.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(commentcount=func.coalesce(Project.commentcount, 0) + 1)
            .execution_options(synchronize_session=False)
        )
        if (result.rowcount or 0) <= 0:
            return False
        await self.session.commit()
        return True
    
    async def decrement_comment_count(self, project_id: int) -> bool:
        """
        减少项目的评论数量
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        result = await self.session.execute(
            update(Project)
            .where(Project.id == project_id, func.coalesce(Project.commentcount, 0) > 0)
            .values(commentcount=func.greatest(func.coalesce(Project.commentcount, 0) - 1, 0))
            .execution_options(synchronize_session=False)
        )
        if (result.rowcount or 0) <= 0:
            return False
        await self.session.commit()
        return True

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
            result = await self.session.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(accesscount=func.coalesce(Project.accesscount, 0) + 1)
                .execution_options(synchronize_session=False)
            )
            if (result.rowcount or 0) <= 0:
                return False
            await self.session.commit()
            return True
        except Exception as e:
            return False
