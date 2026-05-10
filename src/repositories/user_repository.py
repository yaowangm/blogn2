from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from src.utils.database_utils import DatabaseUtils
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

    async def get_by_login_identifier(self, username_or_email: str) -> Optional[User]:
        """登录框输入：先按用户名再按邮箱解析（与 AuthService.authenticate_user 一致）。"""
        raw = (username_or_email or "").strip()
        if not raw:
            return None
        user = await self.get_by_name(raw)
        if user:
            return user
        return await self.get_by_email(raw)

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
            return False

    async def update_intropiid(self, user_id: int, intropiid: int) -> bool:
        """
        更新用户的intropiid（个人介绍文章ID）
        
        Args:
            user_id: 用户ID
            intropiid: 个人介绍文章ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取用户
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # 更新intropiid
            user.intropiid = intropiid
            await self.session.commit()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            return False

    async def update_email(self, user_id: int, new_email: str) -> bool:
        """
        更新用户邮箱
        
        Args:
            user_id: 用户ID
            new_email: 新邮箱地址
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 检查邮箱是否已被其他用户使用
            existing_user = await self.get_by_email(new_email)
            if existing_user and existing_user.id != user_id:
                return False
            
            # 获取用户
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # 更新邮箱
            user.email = new_email
            await self.session.commit()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            return False

    async def increment_point(self, user_id: int, points: int = 10, source: str = "unknown") -> bool:
        """
        增加用户积分（带每日10分限制）
        
        Args:
            user_id: 用户ID
            points: 增加的积分数，默认为10
            source: 积分来源，用于记录
            
        Returns:
            bool: 是否成功增加积分（如果达到每日限制则返回False）
        """
        from sqlmodel import select, func
        from datetime import datetime, date
        from src.models.point_log import PointLog
        
        # 检查今日已获得的积分
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 查询今日已获得的积分总数
        today_points_stmt = select(func.sum(PointLog.points)).where(
            PointLog.user_id == user_id,
            PointLog.log_date >= today_start,
            PointLog.log_date <= today_end
        )
        today_points_result = await self.session.exec(today_points_stmt)
        today_points = today_points_result.first() or 0
        
        # 检查是否会超过每日10分限制
        if today_points + points > 10:
            return False  # 超过每日限制，不增加积分
        
        # 获取用户信息
        statement = select(User).where(User.id == user_id)
        result = await self.session.exec(statement)
        user = result.first()
        
        if user:
            # 增加用户积分
            user.point = (user.point or 0) + points
            self.session.add(user)
            
            # 记录积分日志
            point_log = PointLog(
                user_id=user_id,
                points=points,
                source=source,
                log_date=datetime.now()
            )
            self.session.add(point_log)
            
            return True
        
        return False
    
    async def decrement_point(self, user_id: int, points: int = 10) -> None:
        """
        减少用户积分
        
        Args:
            user_id: 用户ID
            points: 减少的积分数，默认为10
        """
        from sqlmodel import select
        from datetime import datetime
        
        statement = select(User).where(User.id == user_id)
        result = await self.session.exec(statement)
        user = result.first()
        
        if user:
            user.point = max((user.point or 0) - points, 0)
            self.session.add(user)
    
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

    async def update_user_state(self, user_id: int, state: int) -> bool:
        """
        更新用户状态
        
        Args:
            user_id: 用户ID
            state: 新状态 (1=正常, 2=冻结, 10=管理员)
            
        Returns:
            bool: 更新是否成功
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            user.state = state
            self.session.add(user)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            return False 