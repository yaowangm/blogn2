"""
权限检查工具类

提供通用的权限检查功能，减少重复代码。
"""

from typing import Dict, Any, Optional

class PermissionUtils:
    """权限检查工具类"""
    
    # 用户状态常量
    USER_STATE_NORMAL = 1
    USER_STATE_FROZEN = 2
    USER_STATE_ADMIN = 10
    
    @staticmethod
    def is_admin(current_user: Optional[Dict[str, Any]]) -> bool:
        """
        检查用户是否为管理员
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            bool: 是否为管理员
        """
        return current_user and current_user.get("state") == PermissionUtils.USER_STATE_ADMIN
    
    @staticmethod
    def is_owner(current_user: Optional[Dict[str, Any]], owner_id: int) -> bool:
        """
        检查用户是否为资源所有者
        
        Args:
            current_user: 当前用户信息
            owner_id: 资源所有者ID
            
        Returns:
            bool: 是否为所有者
        """
        return current_user and current_user.get("id") == owner_id
    
    @staticmethod
    def can_manage_resource(
        current_user: Optional[Dict[str, Any]], 
        owner_id: int
    ) -> bool:
        """
        检查用户是否可以管理资源（管理员或所有者）
        
        Args:
            current_user: 当前用户信息
            owner_id: 资源所有者ID
            
        Returns:
            bool: 是否可以管理
        """
        return (
            PermissionUtils.is_admin(current_user) or 
            PermissionUtils.is_owner(current_user, owner_id)
        )
    
    @staticmethod
    def can_view_profile(
        current_user: Optional[Dict[str, Any]], 
        target_user_id: int,
        target_user_state: int
    ) -> bool:
        """
        检查用户是否可以查看目标用户资料
        
        Args:
            current_user: 当前用户信息
            target_user_id: 目标用户ID
            target_user_state: 目标用户状态
            
        Returns:
            bool: 是否可以查看
        """
        # 管理员可以查看任何用户资料
        if PermissionUtils.is_admin(current_user):
            return True
        
        # 用户可以查看自己的资料
        if PermissionUtils.is_owner(current_user, target_user_id):
            return True
        
        # 不能查看已冻结用户的资料（除非是管理员或自己）
        if target_user_state == PermissionUtils.USER_STATE_FROZEN:
            return False
        
        # 其他情况可以查看
        return True
    
    @staticmethod
    def get_user_id(current_user: Optional[Dict[str, Any]]) -> Optional[int]:
        """
        获取用户ID
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            Optional[int]: 用户ID
        """
        return current_user.get("id") if current_user else None
    
    @staticmethod
    def get_user_state(current_user: Optional[Dict[str, Any]]) -> Optional[int]:
        """
        获取用户状态
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            Optional[int]: 用户状态
        """
        return current_user.get("state") if current_user else None
