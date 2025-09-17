from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List, Dict, Any
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
    
    async def get_subscribed_blogs_by_project(self, project_id: int, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """获取指定项目订阅的所有博客列表（按created字段倒序排序）"""
        from sqlmodel import select, func
        from src.models.project import Project
        from src.models.user import User
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 查询订阅的博客信息
        query = (
            select(Relation, Project, User)
            .join(Project, Relation.objectid == Project.id)
            .join(User, Project.userid == User.id)
            .where(Relation.projectid == project_id)
            .where(Relation.acttype == 1)
            .order_by(Relation.created.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.exec(query)
        relations = result.all()
        
        # 构建返回数据
        blogs = []
        for relation, project, user in relations:
            blogs.append({
                "relation_id": relation.id,
                "project_id": project.id,
                "project_name": project.name,
                "project_description": project.comment,
                "user_id": user.id,
                "user_name": user.name,
                "user_avatar": f"/avatar/1/s_{user.id}.jpg",  # 使用默认头像路径
                "subscribed_at": relation.created.isoformat() if relation.created else None,
                "project_created_at": project.createtime.isoformat() if project.createtime else None
            })
        
        # 查询总数
        count_query = (
            select(func.count(Relation.id))
            .where(Relation.projectid == project_id)
            .where(Relation.acttype == 1)
        )
        
        total_result = await self.session.exec(count_query)
        total = total_result.first() or 0
        
        return {
            "blogs": blogs,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
