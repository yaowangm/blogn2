from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Dict, Any
from src.models.subscription import Subscription
from src.models.project_item import ProjectItem
from src.models.project import Project
from src.models.user import User
from src.utils.text_utils import POST_LIST_EXCERPT_MAX_LENGTH, truncate_excerpt

class SubscriptionRepository:
    """订阅数据访问层
    
    提供订阅数据的CRUD操作，包括查询订阅文章等功能。
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_subscription_posts_by_project(self, project_id: int, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """获取指定项目的订阅文章列表（按时间倒序）
        
        Args:
            project_id: 项目ID
            page: 页码
            limit: 每页数量
            
        Returns:
            Dict[str, Any]: 包含订阅文章列表和总数的字典
        """
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 通过subsc表关联查询订阅的文章
        comment_excerpt = func.substr(ProjectItem.comment, 1, POST_LIST_EXCERPT_MAX_LENGTH).label("comment")
        query = (
            select(
                ProjectItem.id,
                ProjectItem.name,
                comment_excerpt,
                ProjectItem.createtime,
                ProjectItem.accesscount,
                ProjectItem.commentcount,
                ProjectItem.projectid,
                ProjectItem.userid,
                ProjectItem.attachment,
                Project.name.label("blog_name"),
                User.name.label("author_name"),
            )
            .join(Subscription, ProjectItem.id == Subscription.piid)
            .join(Project, ProjectItem.projectid == Project.id)
            .join(User, ProjectItem.userid == User.id)
            .where(Subscription.projectid == project_id)
            .where(ProjectItem.status == 1)   # 只获取正常状态的文章
            .order_by(ProjectItem.createtime.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        posts = []
        
        for row in result:
            avatar_path = None
            if row.userid:
                import os
                from src.config.app import validate_app_config
                config = validate_app_config()
                avatar_dir = config["avatar_dir"]
                prefix = (row.userid // 10000) + 1
                real_path = os.path.join(avatar_dir, str(prefix), f"s_{row.userid}.jpg")
                if os.path.exists(real_path):
                    avatar_path = f"/avatar/{prefix}/s_{row.userid}.jpg"
            
            posts.append({
                "id": row.id,
                "name": row.name,
                "comment": truncate_excerpt(row.comment),
                "createtime": row.createtime,
                "accesscount": row.accesscount,
                "commentcount": row.commentcount,
                "blog_name": row.blog_name,
                "author_name": row.author_name,
                "blog_id": row.projectid,
                "userid": row.userid,
                "avatar": avatar_path,
                "image": f"/upload/{row.attachment}" if row.attachment else None
            })
        
        # 获取总数
        count_query = (
            select(func.count(ProjectItem.id))
            .join(Subscription, ProjectItem.id == Subscription.piid)
            .where(Subscription.projectid == project_id)
            .where(ProjectItem.status == 1)
        )
        
        total_result = await self.session.exec(count_query)
        total = total_result.first() or 0
        
        # 注意：这里仍然使用实时查询，因为订阅文章的数量可能经常变化
        # 如果需要优化，可以考虑在project表中添加subscription_count字段
        
        return {
            "posts": posts,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    async def count_subscriptions_by_project(self, project_id: int) -> int:
        """统计指定项目的订阅文章总数"""
        statement = (
            select(func.count(Subscription.id))
            .where(Subscription.projectid == project_id)
        )
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def create_broadcast(self, broadcast: Subscription) -> Subscription:
        """创建广播记录"""
        self.session.add(broadcast)
        await self.session.commit()
        await self.session.refresh(broadcast)
        return broadcast
    
    async def get_broadcast(self, project_id: int, piid: int) -> Optional[Subscription]:
        """检查是否已经广播过某篇文章给某个订阅者"""
        statement = select(Subscription).where(
            Subscription.projectid == project_id,
            Subscription.piid == piid
        )
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_broadcasts_by_project(self, project_id: int) -> List[Subscription]:
        """获取某个项目的所有广播记录"""
        statement = select(Subscription).where(Subscription.projectid == project_id)
        result = await self.session.exec(statement)
        return result.all()
    
    async def delete_broadcast(self, project_id: int, piid: int) -> bool:
        """删除广播记录"""
        statement = select(Subscription).where(
            Subscription.projectid == project_id,
            Subscription.piid == piid
        )
        result = await self.session.exec(statement)
        broadcast = result.first()
        if broadcast:
            await self.session.delete(broadcast)
            await self.session.commit()
            return True
        return False
