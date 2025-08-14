from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from src.models.post import Post
from src.models.project_item import ProjectItem

class PostRepository:
    """评论数据访问层
    
    提供评论数据的CRUD操作，包括查询、统计等功能。
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def count(self) -> int:
        """获取评论总数"""
        statement = select(func.count(Post.id))
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_by_id(self, id: int) -> Optional[Post]:
        """根据ID获取评论"""
        statement = select(Post).where(Post.id == id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_project_item_id(self, project_item_id: int, limit: int = None) -> List[Post]:
        """根据项目项ID获取评论"""
        statement = select(Post).where(Post.projectitemid == project_item_id)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_recent_comments_by_project(self, project_id: int, limit: int = 5) -> List[Post]:
        """获取指定项目的最近评论"""
        # 先获取项目下的所有项目项ID
        project_items_query = select(ProjectItem.id).where(ProjectItem.projectid == project_id)
        project_items_result = await self.session.exec(project_items_query)
        project_item_ids = [item.id for item in project_items_result.all()]
        
        if not project_item_ids:
            return []
        
        # 获取这些项目项的评论
        statement = (
            select(Post)
            .where(Post.projectitemid.in_(project_item_ids))
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_recent_comments(self, limit: int = 5) -> List[Post]:
        """获取最近的评论（排除留言本）"""
        statement = (
            select(Post)
            .where(Post.projectitemid > 0)  # 排除留言本
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_messages(self, limit: int = 5) -> List[Post]:
        """获取留言本记录"""
        statement = (
            select(Post)
            .where(Post.projectitemid == 0)  # 只获取留言本
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        return result.all() 