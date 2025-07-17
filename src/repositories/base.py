from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from typing import TypeVar, Generic, Type, List, Optional
from sqlmodel import SQLModel

T = TypeVar('T', bound=SQLModel)

class BaseRepository(Generic[T]):
    """基础仓库类，提供通用的CRUD操作"""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def count(self) -> int:
        """获取记录总数"""
        statement = select(func.count(self.model.id))
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """根据ID获取记录"""
        statement = select(self.model).where(self.model.id == id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_all(self, limit: int = None) -> List[T]:
        """获取所有记录"""
        statement = select(self.model)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def create(self, obj: T) -> T:
        """创建新记录"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, obj: T) -> T:
        """更新记录"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, id: int) -> bool:
        """删除记录"""
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False 