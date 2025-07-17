from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from src.database import User

class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def count(self) -> int:
        """获取用户总数"""
        statement = select(func.count(User.id))
        result = await self.session.exec(statement)
        return result.first() or 0
    
    async def get_by_id(self, id: int) -> Optional[User]:
        """根据ID获取用户"""
        statement = select(User).where(User.id == id)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        statement = select(User).where(User.email == email)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_by_name(self, name: str) -> Optional[User]:
        """根据用户名获取用户"""
        statement = select(User).where(User.name == name)
        result = await self.session.exec(statement)
        return result.first()
    
    async def get_active_users(self, limit: int = None) -> List[User]:
        """获取活跃用户"""
        statement = select(User).where(User.state == 1)
        if limit:
            statement = statement.limit(limit)
        result = await self.session.exec(statement)
        return result.all()
    
    async def get_recent_users(self, limit: int = 10) -> List[User]:
        """获取最近注册的用户"""
        statement = select(User).order_by(User.regtime.desc()).limit(limit)
        result = await self.session.exec(statement)
        return result.all() 