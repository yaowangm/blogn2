from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from typing import List, Optional
from datetime import datetime, timedelta

from src.models.post import Post
from src.models.user import User
from src.models.project_item import ProjectItem

class PostRepository:
    """Post数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_recent_comments(self, limit: int = 5) -> List[dict]:
        """获取最近的评论列表（不包括留言本）"""
        query = (
            select(Post, User.name.label("author_name"), ProjectItem.name.label("post_name"))
            .join(User, Post.userid == User.id)
            .join(ProjectItem, Post.projectitemid == ProjectItem.id)
            .where(Post.projectitemid > 0)  # 只获取博文评论，不包括留言本
            .where(Post.status == 1)  # 只获取正常状态的评论
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        comments = []
        
        for post, author_name, post_name in result:
            comments.append({
                "id": post.id,
                "content": post.content,
                "author_name": author_name,
                "post_name": post_name,
                "post_time": post.posttime,
                "projectitemid": post.projectitemid
            })
        
        return comments
    
    async def count_comments(self) -> int:
        """获取评论总数（不包括留言本）"""
        result = await self.session.exec(
            select(func.count(Post.id))
            .where(Post.projectitemid > 0)
            .where(Post.status == 1)
        )
        return result.first() or 0
    
    async def count_messages(self) -> int:
        """获取留言本总数"""
        result = await self.session.exec(
            select(func.count(Post.id))
            .where(Post.projectitemid == 0)
            .where(Post.status == 1)
        )
        return result.first() or 0 