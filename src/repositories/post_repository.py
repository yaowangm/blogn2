from sqlmodel import select, func, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.constants import ArticleStatus
from src.models.post import Post
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.user import User
from src.utils.time_utils import TimeUtils

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
        # 使用JOIN查询获取评论、用户名和文章名；排除孤儿评论与已删除/下架文章上的评论
        statement = (
            select(Post, User.name.label("user_name"), ProjectItem.name.label("project_item_name"))
            .join(User, Post.userid == User.id)
            .join(ProjectItem, Post.projectitemid == ProjectItem.id)
            .join(Project, ProjectItem.projectid == Project.id)
            .where(ProjectItem.projectid == project_id)
            .where(Post.status == 1)
            .where(ProjectItem.status == 1)
            .where(or_(ProjectItem.itemtype.is_(None), ProjectItem.itemtype != ArticleStatus.DELETED))
            .where(Project.state == 1)
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        comments = []
        
        for post, user_name, project_item_name in result.all():
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
        """获取最近的评论（排除留言本）。

        必须存在对应 projectitem 且文章、博客均为有效状态，避免：
        - 文章硬删除后遗留的孤儿 post 仍出现在「最近评论」；
        - 软删除/下架文章上的评论仍被展示。
        """
        statement = (
            select(Post, User.name.label("user_name"))
            .join(ProjectItem, Post.projectitemid == ProjectItem.id)
            .join(Project, ProjectItem.projectid == Project.id)
            .outerjoin(User, Post.userid == User.id)
            .where(Post.projectitemid > 0)
            .where(Post.status == 1)
            .where(ProjectItem.status == 1)
            .where(or_(ProjectItem.itemtype.is_(None), ProjectItem.itemtype != ArticleStatus.DELETED))
            .where(Project.state == 1)
            .order_by(Post.posttime.desc())
            .limit(limit)
        )
        
        result = await self.session.exec(statement)
        comments = []
        
        for comment, user_name in result.all():
            author_name = user_name if user_name else "用户"
            
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
            if message.lastreplyid is not None and message.lastreplyid >= 0:
                if message.lastreplyid == 0:
                    last_reply_author = "匿名用户"
                else:
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
            if message.lastreplyid is not None and message.lastreplyid >= 0:
                if message.lastreplyid == 0:
                    last_reply_author = "匿名用户"
                else:
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
                "is_main_post": True,
                "lastreplyid": main_post.lastreplyid,
                "lastreplytime": main_post.lastreplytime,
                "replycount": main_post.replycount or 0
            })
        else:
            # 如果找不到主贴，抛出异常
            raise ValueError(f"主题 {thread_id} 不存在")
        
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
                main_post.lastreplyid = reply_user_id  # 存储最后回复者的用户ID
                main_post.lastreplytime = TimeUtils.now_utc()
                
                await self.session.flush()
                await self.session.commit()
        except Exception as e:
            # 统计更新失败，静默处理
            pass
    
    async def count_comments(self) -> int:
        """统计评论数量（排除留言本；与 get_recent_comments 可见性规则一致）"""
        statement = (
            select(func.count(Post.id))
            .join(ProjectItem, Post.projectitemid == ProjectItem.id)
            .join(Project, ProjectItem.projectid == Project.id)
            .where(Post.projectitemid > 0)
            .where(Post.status == 1)
            .where(ProjectItem.status == 1)
            .where(or_(ProjectItem.itemtype.is_(None), ProjectItem.itemtype != ArticleStatus.DELETED))
            .where(Project.state == 1)
        )
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def count_messages(self) -> int:
        """统计留言本主贴数量"""
        statement = select(func.count(Post.id)).where(Post.projectitemid == 0).where(Post.rootid == 0)
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def create(self, post: Post) -> Post:
        """创建新的评论或留言"""
        self.session.add(post)
        await self.session.flush()  # 获取生成的ID
        await self.session.refresh(post)  # 刷新对象以获取完整数据
        # 注意：不在这里提交事务，由调用方管理事务
        
        # 更新统计信息
        try:
            from src.services.stats_service import StatsService
            stats_service = StatsService(self.session)
            await stats_service.handle_comment_creation(post)
        except Exception as e:
            # 统计更新失败不影响评论创建，静默处理
            pass
        
        # 统一处理向量化（评论和留言都使用comment_vectors表）
        try:
            from src.services.vectorization_update_service import get_vectorization_update_service
            vectorization_service = get_vectorization_update_service(self.session)
            
            # 创建向量化数据
            await vectorization_service.update_comment_vectors(
                post.id, 
                post.subject or "", 
                post.content, 
                post.projectitemid  # 评论为article_id，留言为0
            )
            
        except Exception as e:
            # 向量化失败不影响post创建成功
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Post {post.id} 向量化失败: {e}")
        
        return post
    
    async def delete_all_posts_for_project_item(self, project_item_id: int) -> int:
        """删除指定文章（projectitem）下的所有评论 post。用于彻底删除文章，避免残留孤儿行。"""
        statement = select(Post).where(Post.projectitemid == project_item_id)
        result = await self.session.exec(statement)
        posts = list(result.all())
        for post in posts:
            await self.session.delete(post)
        if posts:
            await self.session.flush()
        return len(posts)
    
    async def delete(self, post_id: int) -> bool:
        """删除评论（简单删除，不处理统计信息）"""
        statement = select(Post).where(Post.id == post_id)
        result = await self.session.exec(statement)
        post = result.first()
        
        if not post:
            return False
        
        # 更新统计信息
        try:
            from src.services.stats_service import StatsService
            stats_service = StatsService(self.session)
            await stats_service.handle_comment_deletion(post)
        except Exception as e:
            # 统计更新失败不影响评论删除，静默处理
            pass
        
        await self.session.delete(post)
        # 注意：不在这里提交事务，由调用方管理事务
        return True
    
    async def delete_post(self, post_id: int) -> Dict[str, Any]:
        """删除帖子（留言或评论）
        
        Args:
            post_id: 帖子ID
            
        Returns:
            Dict[str, Any]: 删除结果信息
        """
        try:
            # 获取帖子信息
            statement = select(Post).where(Post.id == post_id)
            result = await self.session.exec(statement)
            post = result.first()
            
            if not post:
                return {"success": False, "message": "帖子不存在"}
            
            deleted_count = 0
            deleted_posts = []
            
            # 判断是留言本留言还是博文评论
            is_guestbook = post.projectitemid == 0
            
            if is_guestbook:
                # 留言本留言处理
                if post.rootid == 0:
                    # 删除主贴，需要同时删除所有跟贴
                    # 1. 先删除所有跟贴
                    replies_statement = select(Post).where(Post.rootid == post_id)
                    replies_result = await self.session.exec(replies_statement)
                    replies = replies_result.all()
                    
                    for reply in replies:
                        await self.session.delete(reply)
                        deleted_count += 1
                        deleted_posts.append({
                            "id": reply.id,
                            "type": "reply",
                            "subject": reply.subject or "无标题"
                        })
                    
                    # 2. 删除主贴
                    await self.session.delete(post)
                    deleted_count += 1
                    deleted_posts.append({
                        "id": post.id,
                        "type": "main_post",
                        "subject": post.subject or "无标题"
                    })
                    
                    # 3. 提交事务
                    await self.session.commit()
                    
                    return {
                        "success": True,
                        "message": f"成功删除主贴及{len(replies)}条跟贴",
                        "deleted_count": deleted_count,
                        "deleted_posts": deleted_posts,
                        "is_main_post": True,
                        "post_type": "guestbook"
                    }
                else:
                    # 删除跟贴
                    main_post_id = post.rootid
                    
                    # 1. 删除跟贴
                    await self.session.delete(post)
                    deleted_count += 1
                    deleted_posts.append({
                        "id": post.id,
                        "type": "reply",
                        "subject": post.subject or "无标题"
                    })
                    
                    # 2. 更新主贴的统计信息
                    await self._update_main_post_stats_after_delete(main_post_id)
                    
                    # 3. 提交事务
                    await self.session.commit()
                    
                    return {
                        "success": True,
                        "message": "成功删除跟贴",
                        "deleted_count": deleted_count,
                        "deleted_posts": deleted_posts,
                        "is_main_post": False,
                        "main_post_id": main_post_id,
                        "post_type": "guestbook"
                    }
            else:
                # 博文评论处理
                if post.rootid == 0:
                    # 删除主评论，需要同时删除所有回复
                    # 1. 先删除所有回复
                    replies_statement = select(Post).where(Post.rootid == post_id)
                    replies_result = await self.session.exec(replies_statement)
                    replies = replies_result.all()
                    
                    for reply in replies:
                        await self.session.delete(reply)
                        deleted_count += 1
                        deleted_posts.append({
                            "id": reply.id,
                            "type": "reply",
                            "subject": reply.subject or "无标题"
                        })
                    
                    # 2. 删除主评论
                    await self.session.delete(post)
                    deleted_count += 1
                    deleted_posts.append({
                        "id": post.id,
                        "type": "main_comment",
                        "subject": post.subject or "无标题"
                    })
                    
                    # 3. 更新博文的评论统计
                    await self._update_article_comment_stats_after_delete(post.projectitemid)
                    
                    # 4. 提交事务
                    await self.session.commit()
                    
                    return {
                        "success": True,
                        "message": f"成功删除主评论及{len(replies)}条回复",
                        "deleted_count": deleted_count,
                        "deleted_posts": deleted_posts,
                        "is_main_post": True,
                        "post_type": "comment"
                    }
                else:
                    # 删除回复
                    main_comment_id = post.rootid
                    
                    # 1. 删除回复
                    await self.session.delete(post)
                    deleted_count += 1
                    deleted_posts.append({
                        "id": post.id,
                        "type": "reply",
                        "subject": post.subject or "无标题"
                    })
                    
                    # 2. 更新主评论的统计信息
                    await self._update_main_comment_stats_after_delete(main_comment_id)
                    
                    # 3. 更新博文的评论统计
                    await self._update_article_comment_stats_after_delete(post.projectitemid)
                    
                    # 4. 提交事务
                    await self.session.commit()
                    
                    return {
                        "success": True,
                        "message": "成功删除回复",
                        "deleted_count": deleted_count,
                        "deleted_posts": deleted_posts,
                        "is_main_post": False,
                        "main_comment_id": main_comment_id,
                        "post_type": "comment"
                    }
                
        except Exception as e:
            await self.session.rollback()
            return {"success": False, "message": f"删除帖子失败: {str(e)}"}
    
    async def _update_main_post_stats_after_delete(self, main_post_id: int):
        """删除跟贴后更新主贴的统计信息"""
        try:
            # 获取主贴
            main_post_result = await self.session.exec(select(Post).where(Post.id == main_post_id))
            main_post = main_post_result.first()
            
            if main_post:
                # 重新计算回复数
                reply_count_statement = select(func.count(Post.id)).where(Post.rootid == main_post_id)
                reply_count_result = await self.session.exec(reply_count_statement)
                new_reply_count = reply_count_result.first() or 0
                
                # 更新回复数
                main_post.replycount = new_reply_count
                
                # 更新最后回复信息
                if new_reply_count > 0:
                    # 获取最新的跟贴
                    latest_reply_statement = (
                        select(Post)
                        .where(Post.rootid == main_post_id)
                        .order_by(Post.posttime.desc())
                        .limit(1)
                    )
                    latest_reply_result = await self.session.exec(latest_reply_statement)
                    latest_reply = latest_reply_result.first()
                    
                    if latest_reply:
                        main_post.lastreplyid = latest_reply.userid
                        main_post.lastreplytime = latest_reply.posttime
                else:
                    # 没有跟贴了，清空最后回复信息
                    main_post.lastreplyid = None
                    main_post.lastreplytime = None
                
                await self.session.flush()
        except Exception as e:
            # 统计更新失败，静默处理
            pass
    
    async def _update_main_comment_stats_after_delete(self, main_comment_id: int):
        """删除回复后更新主评论的统计信息"""
        try:
            # 获取主评论
            main_comment_result = await self.session.exec(select(Post).where(Post.id == main_comment_id))
            main_comment = main_comment_result.first()
            
            if main_comment:
                # 重新计算回复数
                reply_count_statement = select(func.count(Post.id)).where(Post.rootid == main_comment_id)
                reply_count_result = await self.session.exec(reply_count_statement)
                new_reply_count = reply_count_result.first() or 0
                
                # 更新回复数
                main_comment.replycount = new_reply_count
                
                # 更新最后回复信息
                if new_reply_count > 0:
                    # 获取最新的回复
                    latest_reply_statement = (
                        select(Post)
                        .where(Post.rootid == main_comment_id)
                        .order_by(Post.posttime.desc())
                        .limit(1)
                    )
                    latest_reply_result = await self.session.exec(latest_reply_statement)
                    latest_reply = latest_reply_result.first()
                    
                    if latest_reply:
                        main_comment.lastreplyid = latest_reply.userid
                        main_comment.lastreplytime = latest_reply.posttime
                else:
                    # 没有回复了，清空最后回复信息
                    main_comment.lastreplyid = None
                    main_comment.lastreplytime = None
                
                await self.session.flush()
        except Exception as e:
            # 统计更新失败，静默处理
            pass
    
    async def _update_article_comment_stats_after_delete(self, project_item_id: int):
        """删除评论后更新博文的评论统计信息"""
        try:
            from src.models.project_item import ProjectItem
            
            # 获取博文
            article_result = await self.session.exec(select(ProjectItem).where(ProjectItem.id == project_item_id))
            article = article_result.first()
            
            if article:
                # 重新计算评论数
                comment_count_statement = select(func.count(Post.id)).where(Post.projectitemid == project_item_id)
                comment_count_result = await self.session.exec(comment_count_statement)
                new_comment_count = comment_count_result.first() or 0
                
                # 更新评论数
                article.commentcount = new_comment_count
                
                await self.session.flush()
        except Exception as e:
            # 统计更新失败，静默处理
            pass
    
    async def update_articles_folder_to_uncategorized(self, folder_id: int) -> int:
        """将指定分类下的所有文章设置为未分类
        
        Args:
            folder_id: 分类ID
            
        Returns:
            int: 更新的文章数量
        """
        try:
            from src.models.project_item import ProjectItem
            
            # 查找该分类下的所有文章
            statement = select(ProjectItem).where(ProjectItem.folderid == folder_id)
            result = await self.session.exec(statement)
            articles = result.all()
            
            # 更新文章分类为未分类（0）
            updated_count = 0
            for article in articles:
                article.folderid = 0
                updated_count += 1
            
            if updated_count > 0:
                await self.session.flush()
                await self.session.commit()
            
            return updated_count
            
        except Exception as e:
            await self.session.rollback()
            return 0 