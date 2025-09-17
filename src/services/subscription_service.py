from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, Dict, Any
from src.repositories.relation_repository import RelationRepository
from src.repositories.project_repository import ProjectRepository
from src.models.relation import Relation

class SubscriptionService:
    """订阅服务层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.relation_repo = RelationRepository(session)
        self.project_repo = ProjectRepository(session)
    
    async def subscribe_to_blog(self, subscriber_project_id: int, target_project_id: int) -> Dict[str, Any]:
        """订阅博客"""
        # 检查目标博客是否存在
        target_project = await self.project_repo.get_project_by_id(target_project_id)
        if not target_project:
            return {"success": False, "message": "目标博客不存在"}
        
        # 检查是否已经订阅
        if await self.relation_repo.is_subscribed(subscriber_project_id, target_project_id):
            return {"success": False, "message": "已经订阅过该博客"}
        
        # 创建订阅关系
        relation = await self.relation_repo.create_relation(
            projectid=subscriber_project_id,
            objectid=target_project_id,
            acttype=1
        )
        
        return {
            "success": True, 
            "message": "订阅成功",
            "relation_id": relation.id
        }
    
    async def unsubscribe_from_blog(self, subscriber_project_id: int, target_project_id: int) -> Dict[str, Any]:
        """取消订阅博客"""
        # 检查是否已订阅
        if not await self.relation_repo.is_subscribed(subscriber_project_id, target_project_id):
            return {"success": False, "message": "未订阅该博客"}
        
        # 删除订阅关系
        success = await self.relation_repo.delete_relation(
            projectid=subscriber_project_id,
            objectid=target_project_id,
            acttype=1
        )
        
        if success:
            return {"success": True, "message": "取消订阅成功"}
        else:
            return {"success": False, "message": "取消订阅失败"}
    
    async def check_subscription_status(self, subscriber_project_id: int, target_project_id: int) -> Dict[str, Any]:
        """检查订阅状态"""
        is_subscribed = await self.relation_repo.is_subscribed(subscriber_project_id, target_project_id)
        
        return {
            "is_subscribed": is_subscribed,
            "subscriber_project_id": subscriber_project_id,
            "target_project_id": target_project_id
        }
    
    async def get_subscription_count(self, project_id: int) -> Dict[str, int]:
        """获取订阅统计"""
        subscribers = await self.relation_repo.get_subscribers_by_project(project_id)
        subscriptions = await self.relation_repo.get_subscriptions_by_project(project_id)
        
        return {
            "subscriber_count": len(subscribers),
            "subscription_count": len(subscriptions)
        }
