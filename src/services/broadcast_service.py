from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any
from src.repositories.relation_repository import RelationRepository
from src.repositories.subscription_repository import SubscriptionRepository
from src.models.subscription import Subscription

class BroadcastService:
    """广播服务层 - 处理博客文章发布后的订阅者通知"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.relation_repo = RelationRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
    
    async def broadcast_new_article(self, author_project_id: int, article_id: int) -> Dict[str, Any]:
        """广播新文章给所有订阅者"""
        try:
            subscribers = await self.relation_repo.get_subscribers_by_project(author_project_id)
            
            if not subscribers:
                return {
                    "success": True,
                    "message": "没有订阅者，无需广播",
                    "subscriber_count": 0,
                    "broadcast_count": 0
                }
            
            subscriber_project_ids = [s.projectid for s in subscribers]
            existing_ids = await self.subscription_repo.get_existing_broadcast_project_ids(
                article_id, subscriber_project_ids
            )

            new_broadcasts = [
                Subscription(projectid=subscriber_project_id, piid=article_id)
                for subscriber_project_id in subscriber_project_ids
                if subscriber_project_id not in existing_ids
            ]

            broadcast_count = 0
            failed_broadcasts = []
            try:
                broadcast_count = await self.subscription_repo.create_broadcasts_bulk(new_broadcasts)
            except Exception as e:
                failed_broadcasts.append({"error": str(e)})
            
            return {
                "success": True,
                "message": f"成功广播给 {broadcast_count} 个订阅者",
                "subscriber_count": len(subscribers),
                "broadcast_count": broadcast_count,
                "failed_broadcasts": failed_broadcasts
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"广播失败: {str(e)}",
                "subscriber_count": 0,
                "broadcast_count": 0
            }
    
    async def get_broadcast_stats(self, project_id: int) -> Dict[str, Any]:
        """获取广播统计信息"""
        try:
            subscribers = await self.relation_repo.get_subscribers_by_project(project_id)
            broadcasts = await self.subscription_repo.get_broadcasts_by_project(project_id)
            
            return {
                "subscriber_count": len(subscribers),
                "broadcast_count": len(broadcasts),
                "subscribers": subscribers,
                "broadcasts": broadcasts
            }
        except Exception as e:
            return {
                "subscriber_count": 0,
                "broadcast_count": 0,
                "error": str(e)
            }
