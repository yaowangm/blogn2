from typing import List, Optional, Dict, Any
from src.repositories.user_repository import UserRepository
from src.database import User

class UserService:
    """用户业务逻辑服务类
    
    提供用户相关的业务逻辑处理，包括用户查询、统计等功能。
    """
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_user_count(self) -> int:
        """获取用户总数"""
        return await self.user_repo.count()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return await self.user_repo.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.user_repo.get_by_email(email)
    
    async def get_user_by_name(self, name: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.user_repo.get_by_name(name)
    
    async def get_active_users(self, limit: int = None) -> List[User]:
        """获取活跃用户"""
        return await self.user_repo.get_active_users(limit)
    
    async def get_recent_users(self, limit: int = 10) -> List[User]:
        """获取最近注册的用户"""
        return await self.user_repo.get_recent_users(limit)
    
    async def get_top_users(self, limit: int = 3) -> List[User]:
        """获取按创建时间排序的前N个用户"""
        return await self.user_repo.get_recent_users(limit)
    
    async def get_user_summary(self) -> Dict[str, Any]:
        """获取用户统计摘要"""
        total_users = await self.user_repo.count()
        recent_users = await self.user_repo.get_recent_users(3)
        
        return {
            "total_users": total_users,
            "recent_users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "regtime": user.regtime.isoformat() if user.regtime else None
                }
                for user in recent_users
            ]
        } 