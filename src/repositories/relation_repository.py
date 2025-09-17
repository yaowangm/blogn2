from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from src.models.relation import Relation

class RelationRepository:
    """关系表数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_relation(self, projectid: int, objectid: int, acttype: int = 1) -> Relation:
        """创建关系记录"""
        from datetime import datetime
        relation = Relation(
            projectid=projectid,
            objectid=objectid,
            acttype=acttype,
            created=datetime.now()
        )
        self.session.add(relation)
        await self.session.commit()
        await self.session.refresh(relation)
        return relation
    
    async def get_relation(self, projectid: int, objectid: int, acttype: int = 1) -> Optional[Relation]:
        """获取关系记录"""
        statement = select(Relation).where(
            and_(
                Relation.projectid == projectid,
                Relation.objectid == objectid,
                Relation.acttype == acttype
            )
        )
        result = await self.session.exec(statement)
        return result.first()
    
    async def delete_relation(self, projectid: int, objectid: int, acttype: int = 1) -> bool:
        """删除关系记录"""
        relation = await self.get_relation(projectid, objectid, acttype)
        if relation:
            await self.session.delete(relation)
            await self.session.commit()
            return True
        return False
    
    async def get_subscriptions_by_project(self, projectid: int) -> List[Relation]:
        """获取某个博客的所有订阅关系"""
        statement = select(Relation).where(
            and_(
                Relation.projectid == projectid,
                Relation.acttype == 1
            )
        )
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_subscribers_by_project(self, objectid: int) -> List[Relation]:
        """获取某个博客的所有订阅者"""
        statement = select(Relation).where(
            and_(
                Relation.objectid == objectid,
                Relation.acttype == 1
            )
        )
        result = await self.session.exec(statement)
        return result.all()
    
    async def is_subscribed(self, projectid: int, objectid: int) -> bool:
        """检查是否已订阅"""
        relation = await self.get_relation(projectid, objectid, 1)
        return relation is not None
