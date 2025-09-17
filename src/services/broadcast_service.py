from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Any
from src.repositories.relation_repository import RelationRepository
from src.repositories.subscription_repository import SubscriptionRepository
from src.models.subscription import Subscription
from datetime import datetime

class BroadcastService:
    """广播服务层 - 处理博客文章发布后的订阅者通知"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.relation_repo = RelationRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
    
    async def broadcast_new_article(self, author_project_id: int, article_id: int) -> Dict[str, Any]:
        """
        广播新文章给所有订阅者
        
        Args:
            author_project_id: 作者博客的ID
            article_id: 新文章的ID (projectitem.id)
        
        Returns:
            Dict包含广播结果
        """
        try:
            # 1. 获取所有订阅了当前博客的订阅者ID列表
            subscribers = await self.relation_repo.get_subscribers_by_project(author_project_id)
            
            if not subscribers:
                return {
                    "success": True,
                    "message": "没有订阅者，无需广播",
                    "subscriber_count": 0,
                    "broadcast_count": 0
                }
            
            # 2. 为每个订阅者创建广播记录
            broadcast_count = 0
            failed_broadcasts = []
            
            for subscriber_relation in subscribers:
                try:
                    subscriber_project_id = subscriber_relation.projectid
                    # 检查是否已经广播过这篇文章给这个订阅者
                    existing_broadcast = await self.subscription_repo.get_broadcast(
                        subscriber_project_id, article_id
                    )
                    
                    if existing_broadcast:
                        # 已经广播过，跳过
                        continue
                    
                    # 创建新的广播记录
                    broadcast = Subscription(
                        projectid=subscriber_project_id,
                        piid=article_id
                    )
                    
                    await self.subscription_repo.create_broadcast(broadcast)
                    broadcast_count += 1
                    
                except Exception as e:
                    failed_broadcasts.append({
                        "subscriber_id": subscriber_project_id,
                        "error": str(e)
                    })
            
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
            # 获取订阅者数量
            subscribers = await self.relation_repo.get_subscribers_by_project(project_id)
            
            # 获取已广播的文章数量
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
