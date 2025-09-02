from typing import List, Optional, Dict, Any
from src.repositories.user_repository import UserRepository
from src.database import User
from src.services.auth_service import AuthService

class UserService:
    """用户业务逻辑服务类
    
    提供用户相关的业务逻辑处理，包括用户查询、统计、分页等功能。
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
    
    async def get_users_paginated(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        """
        分页获取用户列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页大小
            search: 搜索关键词，对用户名进行模糊匹配，可选
            
        Returns:
            Dict[str, Any]: 包含用户列表和分页信息的字典
        """
        users, total_count = await self.user_repo.get_users_paginated(page, page_size, search)
        
        # 计算分页信息
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "users": [self._format_user_for_list(user) for user in users],
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def _format_user_for_list(self, user: User) -> Dict[str, Any]:
        """
        格式化用户数据用于列表显示
        
        Args:
            user: 用户对象
            
        Returns:
            Dict[str, Any]: 格式化后的用户数据
        """
        return {
            "id": user.id,
            "name": user.name,
            "state": user.state,
            "regtime": user.regtime.isoformat() if user.regtime else None,
            "point": user.point or 0,
            "projectid": user.projectid,
            "email": user.email  # 管理员可以查看邮箱
        } 
    
    async def reset_user_password(self, user_id: int, new_password: str) -> None:
        """
        重置用户密码
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            
        Raises:
            Exception: 当重置失败时
        """
        # 获取用户
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise Exception("用户不存在")
        
        # 使用正确的双重哈希处理密码
        auth_service = AuthService(self.user_repo, "dummy_secret")  # 临时创建，只用于哈希
        hashed_password = auth_service.hash_password(new_password)
        
        # 更新密码
        success = await self.user_repo.update_password(user_id, hashed_password)
        if not success:
            raise Exception("密码更新失败") 