from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Tuple
from src.models.user import User

class UserRepository:
    """用户数据访问层
    
    提供用户数据的CRUD操作，包括查询、统计、分页等功能。
    """
    
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
    
    async def update(self, user: User) -> User:
        """更新用户信息"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
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
    
    async def get_popular_users(self, limit: int = 10) -> List[dict]:
        """获取热门用户（按积分排序）"""
        statement = (
            select(User.id, User.name, User.point, User.regtime)
            .where(User.state == 1)
            .order_by(User.point.desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return [{"id": user.id, "name": user.name, "point": user.point or 0, "regtime": user.regtime} for user in result.all()]
    
    async def update_password(self, user_id: int, new_password: str) -> bool:
        """
        更新用户密码
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取用户
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # 更新密码
            user.password = new_password
            await self.session.commit()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            print(f"更新密码失败: {e}")
            return False
    
    async def update_projectid(self, user_id: int, project_id: int) -> bool:
        """
        更新用户的projectid
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取用户
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # 更新projectid
            user.projectid = project_id
            await self.session.commit()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            print(f"更新projectid失败: {e}")
            return False
    
    async def get_users_paginated(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Tuple[List[User], int]:
        """
        分页获取用户列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页大小
            search: 搜索关键词，对用户名进行模糊匹配，可选
            
        Returns:
            Tuple[List[User], int]: (用户列表, 总数量)
        """
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 构建搜索条件
        search_condition = self._build_search_condition(search)
        
        # 获取总数
        total_count = await self._get_user_count(search_condition)
        
        # 获取分页数据
        users = await self._get_users_with_condition(search_condition, offset, page_size)
        
        return users, total_count
    
    def _build_search_condition(self, search: Optional[str]):
        """
        构建搜索条件
        
        Args:
            search: 搜索关键词
            
        Returns:
            搜索条件表达式
        """
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            return User.name.ilike(search_term)
        return True
    
    async def _get_user_count(self, condition) -> int:
        """
        获取符合条件的用户总数
        
        Args:
            condition: 查询条件
            
        Returns:
            int: 用户总数
        """
        count_statement = select(func.count(User.id)).where(condition)
        count_result = await self.session.exec(count_statement)
        return count_result.first() or 0
    
    async def _get_users_with_condition(self, condition, offset: int, limit: int) -> List[User]:
        """
        根据条件获取用户列表
        
        Args:
            condition: 查询条件
            offset: 偏移量
            limit: 限制数量
            
        Returns:
            List[User]: 用户列表
        """
        statement = (
            select(User)
            .where(condition)
            .order_by(User.regtime.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all() 