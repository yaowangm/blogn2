from typing import List, Optional, Dict, Any
from src.repositories.user_repository import UserRepository
from src.repositories.project_repository import ProjectRepository
from src.database import User
from src.services.auth_service import AuthService
from src.services.base_service import BaseService

class UserService(BaseService):
    """用户业务逻辑服务类
    
    提供完整的用户管理业务逻辑，包括：
    - 用户信息查询和统计
    - 分页列表和搜索功能
    - 用户状态管理（冻结/恢复）
    - 密码和邮箱更新
    - 数据格式化和安全处理
    
    设计原则：
    - 业务逻辑与数据访问分离
    - 统一的错误处理和验证
    - 敏感信息的安全处理
    - 支持缓存和性能优化
    """
    
    def __init__(self, user_repo: UserRepository, project_repo: Optional[ProjectRepository] = None):
        self.user_repo = user_repo
        self.project_repo = project_repo
    
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
        
        # 格式化用户数据
        formatted_users = []
        for user in users:
            formatted_user = await self._format_user_for_list(user)
            formatted_users.append(formatted_user)
        
        return {
            "users": formatted_users,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    async def _format_user_for_list(self, user: User) -> Dict[str, Any]:
        """
        格式化用户数据用于列表显示
        
        Args:
            user: 用户对象
            
        Returns:
            Dict[str, Any]: 格式化后的用户数据
        """
        # 获取项目名称
        project_name = None
        if user.projectid and self.project_repo:
            project = await self.project_repo.get_project_by_id(user.projectid)
            if project:
                project_name = project.name
        
        return {
            "id": user.id,
            "name": user.name,
            "state": user.state,
            "regtime": user.regtime.isoformat() if user.regtime else None,
            "point": user.point or 0,
            "projectid": user.projectid,
            "project_name": project_name
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

    async def update_user_email(self, user_id: int, new_email: str) -> None:
        """
        更新用户邮箱
        
        Args:
            user_id: 用户ID
            new_email: 新邮箱地址
            
        Raises:
            Exception: 当更新失败时
        """
        # 验证邮箱格式
        if not self._is_valid_email(new_email):
            raise Exception("邮箱格式不正确")
        
        # 检查用户是否存在
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise Exception("用户不存在")
        
        # 检查邮箱是否已被其他用户使用
        existing_user = await self.user_repo.get_by_email(new_email)
        if existing_user and existing_user.id != user_id:
            raise Exception("该邮箱已被其他用户使用")
        
        # 更新邮箱
        success = await self.user_repo.update_email(user_id, new_email)
        if not success:
            raise Exception("邮箱更新失败")
    
    def _is_valid_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 邮箱格式是否有效
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    async def freeze_user(self, user_id: int) -> bool:
        """
        冻结用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 冻结是否成功
        """
        return await self.user_repo.update_user_state(user_id, 2)

    async def restore_user(self, user_id: int) -> bool:
        """
        恢复用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 恢复是否成功
        """
        return await self.user_repo.update_user_state(user_id, 1) 