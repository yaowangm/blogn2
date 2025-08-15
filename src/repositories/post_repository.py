from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from src.models.post import Post
from src.models.project_item import ProjectItem
from src.models.user import User

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
    
    async def get_recent_comments_by_project(self, project_id: int, limit: int = 5) -> List[dict]:
        """获取指定项目的最近评论，包含用户名和文章名"""
        # 使用JOIN查询获取评论、用户名和文章名
        statement = (
            select(Post, User.name.label("user_name"), ProjectItem.name.label("project_item_name"))
            .join(User, Post.userid == User.id)
            .join(ProjectItem, Post.projectitemid == ProjectItem.id)
            .where(ProjectItem.projectid == project_id)
            .where(Post.status == 1)  # 只获取正常状态的评论
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        comments = []
        
        for post, user_name, project_item_name in result:
            comments.append({
                "id": post.id,
                "user_name": user_name or "用户",
                "content": post.content,
                "post_time": post.posttime,
                "project_item_name": project_item_name or "文章",
                "projectitemid": post.projectitemid,
                "userid": post.userid
            })
        
        return comments
    
    async def get_recent_comments(self, limit: int = 5) -> List[dict]:
        """获取最近的评论（排除留言本）"""
        statement = (
            select(Post)
            .where(Post.projectitemid > 0)  # 排除留言本
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        comments = []
        
        for comment in result.all():
            # 获取用户名
            author_name = "用户"  # 默认值
            if comment.userid:
                try:
                    # 查询用户表获取用户名
                    user_result = await self.session.exec(select(User.name).where(User.id == comment.userid))
                    user_name = user_result.first()
                    if user_name:
                        author_name = user_name
                    else:
                        author_name = "用户"
                except Exception as e:
                    author_name = "用户"
            
            comments.append({
                "id": comment.id,
                "content": comment.content,
                "author_name": author_name,
                "projectitemid": comment.projectitemid,
                "userid": comment.userid,
                "post_time": comment.posttime,  # 改为post_time以匹配BlogService的期望
                "status": comment.status
            })
        
        return comments
    
    async def get_messages(self, limit: int = 5) -> List[dict]:
        """获取留言本记录"""
        statement = (
            select(Post)
            .where(Post.projectitemid == 0)  # 只获取留言本
            .where(Post.rootid == 0)  # 只获取主贴
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        messages = []
        
        for message in result.all():
            # 获取用户名
            author_name = "用户"  # 默认值
            if message.userid:
                try:
                    # 查询用户表获取用户名
                    user_result = await self.session.exec(select(User.name).where(User.id == message.userid))
                    user_name = user_result.first()
                    if user_name:
                        author_name = user_name
                    else:
                        author_name = "用户"
                except Exception as e:
                    author_name = "用户"
            
            # 获取最后回复用户名
            last_reply_author = None
            if message.lastreplyid and message.lastreplyid > 0:
                try:
                    # 查询用户表获取最后回复用户名
                    user_result = await self.session.exec(select(User.name).where(User.id == message.lastreplyid))
                    last_reply_user_name = user_result.first()
                    if last_reply_user_name:
                        last_reply_author = last_reply_user_name
                    else:
                        last_reply_author = "未知用户"
                except Exception as e:
                    last_reply_author = "未知用户"
            
            messages.append({
                "id": message.id,
                "subject": message.subject,
                "content": message.content,
                "userid": message.userid,
                "projectitemid": message.projectitemid,
                "rootid": message.rootid,
                "post_time": message.posttime,  # 改为post_time以匹配BlogService的期望
                "status": message.status,
                "lastreplyid": message.lastreplyid,
                "replycount": message.replycount or 0,  # None值转换为0
                "author_name": author_name,
                "last_reply_author": last_reply_author,
                "reply_count": message.replycount or 0  # 兼容测试中的字段名
            })
        
        return messages
    
    async def get_recent_messages(self, limit: int = 5) -> List[dict]:
        """获取最近的留言本记录（别名方法）"""
        return await self.get_messages(limit)
    
    async def count_comments(self) -> int:
        """统计评论数量（排除留言本）"""
        statement = select(func.count(Post.id)).where(Post.projectitemid > 0)
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def count_messages(self) -> int:
        """统计留言本数量"""
        statement = select(func.count(Post.id)).where(Post.projectitemid == 0)
        result = await self.session.exec(statement)
        return result.first() or 0 