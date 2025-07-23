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
            select(Post, User.name.label("author_name"))
            .join(User, Post.userid == User.id)
            .where(Post.projectitemid > 0)  # 只获取博文评论，不包括留言本
            .where(Post.status == 1)  # 只获取正常状态的评论
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        comments = []
        
        for post, author_name in result:
            comments.append({
                "id": post.id,
                "content": post.content,
                "author_name": author_name,
                "post_time": post.posttime,
                "projectitemid": post.projectitemid,
                "userid": post.userid
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
    
    async def get_recent_messages(self, limit: int = 5) -> List[dict]:
        """获取最近的留言本主贴记录"""
        # 获取主贴和最后回复用户信息
        query = (
            select(
                Post,
                User.name.label("author_name"),
                User.name.label("last_reply_author_name")
            )
            .join(User, Post.userid == User.id)
            .where(Post.projectitemid == 0)  # 只获取留言本
            .where(Post.rootid == 0)  # 只获取主贴
            .where(Post.status == 1)  # 只获取正常状态的留言
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        messages = []
        
        for post, author_name, last_reply_author_name in result:
            # 如果有最后回复用户，获取回复用户名
            last_reply_author = None
            if post.lastreplyid and post.lastreplyid != 0:
                try:
                    reply_user_query = select(User.name).where(User.id == post.lastreplyid)
                    reply_result = await self.session.exec(reply_user_query)
                    last_reply_author = reply_result.first()
                except:
                    last_reply_author = None
            
            messages.append({
                "id": post.id,
                "subject": post.subject,
                "author_name": author_name,
                "post_time": post.posttime,
                "userid": post.userid,
                "last_reply_author": last_reply_author,
                "reply_count": post.replycount or 0
            })
        
        return messages 