from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Dict, Any
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
    
    async def get_by_project_item_id_paginated(self, project_item_id: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """根据项目项ID获取分页评论"""
        # 计算偏移量
        offset = (page - 1) * per_page
        
        # 获取总数
        count_statement = select(func.count(Post.id)).where(Post.projectitemid == project_item_id)
        count_result = await self.session.exec(count_statement)
        total = count_result.first()
        
        # 获取分页数据
        statement = (
            select(Post)
            .where(Post.projectitemid == project_item_id)
            .order_by(Post.posttime.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.session.exec(statement)
        comments = result.all()
        
        # 计算分页信息
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "comments": comments,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages
            }
        }
    
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
    
    async def get_messages_paginated(self, limit: int = 10, offset: int = 0) -> List[dict]:
        """获取留言本分页记录"""
        statement = (
            select(Post)
            .where(Post.projectitemid == 0)  # 只获取留言本
            .where(Post.rootid == 0)  # 只获取主贴
            .order_by(Post.id.desc())  # 按id倒序排序
            .offset(offset)
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
                "post_time": message.posttime,
                "last_reply_time": message.lastreplytime,
                "status": message.status,
                "lastreplyid": message.lastreplyid,
                "replycount": message.replycount or 0,
                "author_name": author_name,
                "last_reply_author": last_reply_author,
                "reply_count": message.replycount or 0,
                "size": message.size or 0,
                "hits": message.hits or 0
            })
        
        return messages
    
    async def get_thread_messages(self, thread_id: int) -> List[dict]:
        """获取主题的所有留言（主贴+跟贴）"""
        # 获取主贴
        main_post_statement = (
            select(Post)
            .where(Post.id == thread_id)
            .where(Post.projectitemid == 0)  # 留言本
        )
        
        # 获取跟贴
        replies_statement = (
            select(Post)
            .where(Post.rootid == thread_id)
            .where(Post.projectitemid == 0)  # 留言本
            .order_by(Post.id.asc())  # 按id正序排序
        )
        
        # 执行查询
        main_result = await self.session.exec(main_post_statement)
        main_post = main_result.first()
        
        replies_result = await self.session.exec(replies_statement)
        replies = replies_result.all()
        
        messages = []
        
        # 处理主贴
        if main_post:
            author_name = await self._get_user_name(main_post.userid)
            messages.append({
                "id": main_post.id,
                "subject": main_post.subject,
                "content": main_post.content,
                "userid": main_post.userid,
                "post_time": main_post.posttime,
                "author_name": author_name,
                "is_main_post": True
            })
        
        # 处理跟贴
        for reply in replies:
            author_name = await self._get_user_name(reply.userid)
            messages.append({
                "id": reply.id,
                "subject": reply.subject,
                "content": reply.content,
                "userid": reply.userid,
                "post_time": reply.posttime,
                "author_name": author_name,
                "is_main_post": False
            })
        
        return messages
    
    async def create_message(self, subject: str, content: str, user_id: int, thread_id: int = None) -> Post:
        """创建新留言"""
        from datetime import datetime
        
        # 计算内容大小
        content_size = len(content.encode('utf-8'))
        
        # 创建留言记录
        new_message = Post(
            subject=subject,
            content=content,
            userid=user_id,
            projectitemid=0,  # 留言本
            rootid=thread_id if thread_id else 0,  # 如果有thread_id则是跟贴，否则是主贴
            size=content_size,
            status=1,  # 正常状态
            hits=0,
            posttime=datetime.now(),
            replycount=0,
            userip="127.0.0.1"  # 默认IP
        )
        
        self.session.add(new_message)
        await self.session.flush()  # 获取生成的ID
        await self.session.refresh(new_message)  # 刷新对象以获取完整数据
        
        # 如果是跟贴，更新主贴的回复数和最后回复时间
        if thread_id:
            await self._update_main_post_stats(thread_id, new_message.id, user_id)
        
        return new_message
    
    async def _get_user_name(self, user_id: int) -> str:
        """获取用户名"""
        if not user_id:
            return "用户"
        
        try:
            user_result = await self.session.exec(select(User.name).where(User.id == user_id))
            user_name = user_result.first()
            return user_name if user_name else "用户"
        except Exception:
            return "用户"
    
    async def _update_main_post_stats(self, main_post_id: int, reply_id: int, reply_user_id: int):
        """更新主贴的统计信息"""
        try:
            # 获取主贴
            main_post_result = await self.session.exec(select(Post).where(Post.id == main_post_id))
            main_post = main_post_result.first()
            
            if main_post:
                # 更新回复数和最后回复信息
                main_post.replycount = (main_post.replycount or 0) + 1
                main_post.lastreplyid = reply_user_id
                main_post.lastreplytime = datetime.now()
                
                await self.session.flush()
        except Exception as e:
            print(f"Error updating main post stats: {e}")
    
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
    
    async def create(self, post: Post) -> Post:
        """创建新的评论或留言"""
        self.session.add(post)
        await self.session.flush()  # 获取生成的ID
        await self.session.refresh(post)  # 刷新对象以获取完整数据
        return post
    
    async def delete(self, comment_id: int) -> bool:
        """删除评论"""
        statement = select(Post).where(Post.id == comment_id)
        result = await self.session.exec(statement)
        comment = result.first()
        
        if not comment:
            return False
        
        await self.session.delete(comment)
        return True 