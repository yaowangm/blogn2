"""
权限管理器
统一管理系统中所有的权限检查逻辑
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class Permission(Enum):
    """权限类型枚举"""
    VIEW_OWN_PROFILE = "view_own_profile"           # 查看自己的个人资料
    VIEW_OTHER_PROFILE = "view_other_profile"       # 查看他人的个人资料
    VIEW_SENSITIVE_FIELDS = "view_sensitive_fields" # 查看敏感字段
    MANAGE_USERS = "manage_users"                   # 管理用户
    MANAGE_SYSTEM = "manage_system"                 # 管理系统


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        """初始化权限管理器"""
        pass
    
    @staticmethod
    def get_user_role(user_state: int) -> str:
        """
        根据用户状态获取用户角色
        
        Args:
            user_state: 用户状态值
            
        Returns:
            str: 用户角色 ('admin', 'user', 'frozen')
        """
        if user_state == 10:
            return "admin"
        elif user_state == 1:
            return "user"
        elif user_state == 0:
            return "frozen"
        else:
            return "unknown"
    
    @staticmethod
    def is_admin(user_state: int) -> bool:
        """
        判断用户是否为管理员
        
        Args:
            user_state: 用户状态值
            
        Returns:
            bool: 是否为管理员
        """
        return user_state == 10
    
    @staticmethod
    def is_frozen(user_state: int) -> bool:
        """
        判断用户是否被冻结
        
        Args:
            user_state: 用户状态值
            
        Returns:
            bool: 是否被冻结
        """
        return user_state == 0
    
    @staticmethod
    def can_view_profile(
        current_user: Optional[Dict[str, Any]], 
        target_user_id: int,
        target_user_state: int
    ) -> bool:
        """
        判断当前用户是否可以查看目标用户的个人资料
        
        Args:
            current_user: 当前登录用户信息
            target_user_id: 目标用户ID
            target_user_state: 目标用户状态
            
        Returns:
            bool: 是否可以查看
        """
        # 目标用户被冻结，任何人都不能查看
        if target_user_state == 0:
            return False
        
        # 管理员可以查看任何用户资料
        if current_user and current_user.get("state") == 10:
            return True
        
        # 普通用户可以查看自己的资料
        if current_user and current_user.get("id") == target_user_id:
            return True
        
        # 未登录用户和普通用户都可以查看其他用户的公开资料
        # 但敏感字段会显示"无权限查看"
        return True
    
    @staticmethod
    def can_view_sensitive_fields(
        current_user: Optional[Dict[str, Any]], 
        target_user_id: int
    ) -> bool:
        """
        判断当前用户是否可以查看目标用户的敏感字段
        
        Args:
            current_user: 当前登录用户信息
            target_user_id: 目标用户ID
            
        Returns:
            bool: 是否可以查看敏感字段
        """
        # 未登录用户不能查看敏感字段
        if not current_user:
            return False
        
        # 管理员可以查看任何用户的敏感字段
        if current_user.get("state") == 10:
            return True
        
        # 用户可以查看自己的敏感字段
        if current_user.get("id") == target_user_id:
            return True
        
        # 其他情况不允许查看敏感字段
        return False
    
    @staticmethod
    def can_manage_users(current_user: Optional[Dict[str, Any]]) -> bool:
        """
        判断当前用户是否可以管理其他用户
        
        Args:
            current_user: 当前登录用户信息
            
        Returns:
            bool: 是否可以管理用户
        """
        # 只有管理员可以管理用户
        return current_user and current_user.get("state") == 10
    
    @staticmethod
    def can_manage_system(current_user: Optional[Dict[str, Any]]) -> bool:
        """
        判断当前用户是否可以管理系统
        
        Args:
            current_user: 当前登录用户信息
            
        Returns:
            bool: 是否可以管理系统
        """
        # 只有管理员可以管理系统
        return current_user and current_user.get("state") == 10
    
    @staticmethod
    def get_profile_data_permissions(
        current_user: Optional[Dict[str, Any]], 
        target_user_id: int
    ) -> Dict[str, bool]:
        """
        获取个人资料数据的权限配置
        
        Args:
            current_user: 当前登录用户信息
            target_user_id: 目标用户ID
            
        Returns:
            Dict[str, bool]: 各字段的权限配置
        """
        can_view_sensitive = PermissionManager.can_view_sensitive_fields(
            current_user, target_user_id
        )
        
        return {
            "can_view_email": can_view_sensitive,
            "can_view_iplog": can_view_sensitive,
            "can_view_password": False,  # 密码字段永远不包含在API响应中
            "can_view_point": can_view_sensitive,
            "can_view_regtime": True,  # 注册时间公开
            "can_view_lastupdate": True,  # 最后更新时间公开
            "can_view_state": True,  # 用户状态公开
        }
    
    @staticmethod
    def filter_profile_data(
        user_data: Dict[str, Any],
        permissions: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        根据权限过滤个人资料数据
        
        安全说明：密码字段永远不会包含在API响应中，即使有权限也不返回
        
        Args:
            user_data: 原始用户数据
            permissions: 权限配置
            
        Returns:
            Dict[str, Any]: 过滤后的用户数据（不包含密码）
        """
        filtered_data = {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "projectid": user_data.get("projectid"),
            "intropiid": user_data.get("intropiid"),
        }
        
        # 根据权限添加字段（密码字段永远不包含）
        if permissions.get("can_view_email"):
            filtered_data["email"] = user_data.get("email")
        if permissions.get("can_view_iplog"):
            filtered_data["iplog"] = user_data.get("iplog")
        # 注意：密码字段永远不包含在API响应中，即使有权限也不返回
        if permissions.get("can_view_point"):
            filtered_data["point"] = user_data.get("point")
        if permissions.get("can_view_regtime"):
            filtered_data["regtime"] = user_data.get("regtime")
        if permissions.get("can_view_lastupdate"):
            filtered_data["lastupdate"] = user_data.get("lastupdate")
        if permissions.get("can_view_state"):
            filtered_data["state"] = user_data.get("state")
        
        return filtered_data


# 创建全局权限管理器实例
permission_manager = PermissionManager()
