"""
权限配置文件
定义系统中各种权限规则和配置
"""

from typing import Dict, List, Any
from enum import Enum


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = 10      # 管理员
    USER = 1        # 普通用户
    FROZEN = 0      # 冻结用户


class PermissionLevel(Enum):
    """权限级别枚举"""
    NONE = 0        # 无权限
    READ = 1        # 读取权限
    WRITE = 2       # 写入权限
    ADMIN = 3       # 管理权限


class ResourceType(Enum):
    """资源类型枚举"""
    USER_PROFILE = "user_profile"           # 用户个人资料
    USER_SENSITIVE = "user_sensitive"       # 用户敏感信息
    BLOG_CONTENT = "blog_content"           # 博客内容
    SYSTEM_CONFIG = "system_config"         # 系统配置
    USER_MANAGEMENT = "user_management"     # 用户管理


# 权限矩阵配置
PERMISSION_MATRIX = {
    # 未登录用户权限
    "anonymous": {
        ResourceType.USER_PROFILE: PermissionLevel.NONE,
        ResourceType.USER_SENSITIVE: PermissionLevel.NONE,
        ResourceType.BLOG_CONTENT: PermissionLevel.READ,
        ResourceType.SYSTEM_CONFIG: PermissionLevel.NONE,
        ResourceType.USER_MANAGEMENT: PermissionLevel.NONE,
    },
    
    # 普通用户权限
    UserRole.USER: {
        ResourceType.USER_PROFILE: PermissionLevel.READ,      # 可以查看自己的资料
        ResourceType.USER_SENSITIVE: PermissionLevel.READ,    # 可以查看自己的敏感信息
        ResourceType.BLOG_CONTENT: PermissionLevel.READ,      # 可以查看博客内容
        ResourceType.SYSTEM_CONFIG: PermissionLevel.NONE,     # 不能查看系统配置
        ResourceType.USER_MANAGEMENT: PermissionLevel.NONE,   # 不能管理其他用户
    },
    
    # 管理员权限
    UserRole.ADMIN: {
        ResourceType.USER_PROFILE: PermissionLevel.ADMIN,     # 可以查看所有用户资料
        ResourceType.USER_SENSITIVE: PermissionLevel.ADMIN,   # 可以查看所有用户敏感信息
        ResourceType.BLOG_CONTENT: PermissionLevel.ADMIN,     # 可以管理所有博客内容
        ResourceType.SYSTEM_CONFIG: PermissionLevel.ADMIN,    # 可以查看系统配置
        ResourceType.USER_MANAGEMENT: PermissionLevel.ADMIN,  # 可以管理所有用户
    },
    
    # 冻结用户权限
    UserRole.FROZEN: {
        ResourceType.USER_PROFILE: PermissionLevel.NONE,
        ResourceType.USER_SENSITIVE: PermissionLevel.NONE,
        ResourceType.BLOG_CONTENT: PermissionLevel.NONE,
        ResourceType.SYSTEM_CONFIG: PermissionLevel.NONE,
        ResourceType.USER_MANAGEMENT: PermissionLevel.NONE,
    }
}


# 敏感字段配置
SENSITIVE_FIELDS = {
    "user": [
        "email",        # 邮箱
        "password",     # 密码
        "iplog",        # IP日志
        "point",        # 积分
    ],
    "blog": [
        "draft_content",    # 草稿内容
        "private_notes",    # 私人笔记
    ]
}


# 公开字段配置
PUBLIC_FIELDS = {
    "user": [
        "id",           # 用户ID
        "name",         # 用户名
        "state",        # 用户状态
        "regtime",      # 注册时间
        "lastupdate",   # 最后更新时间
        "intropiid",    # 自我介绍文章ID
    ],
    "blog": [
        "id",           # 博客ID
        "name",         # 博客名称
        "comment",      # 博客说明
        "recordcount",  # 文章数量
        "accesscount",  # 访问数量
        "commentcount", # 评论数量
    ]
}


# 权限检查规则配置
PERMISSION_RULES = {
    # 个人资料查看规则
    "profile_view": {
        "own": {
            "required_role": [UserRole.USER, UserRole.ADMIN],
            "fields": PUBLIC_FIELDS["user"] + SENSITIVE_FIELDS["user"]
        },
        "other": {
            "required_role": [UserRole.ADMIN],
            "fields": PUBLIC_FIELDS["user"]
        }
    },
    
    # 博客信息查看规则
    "blog_view": {
        "own": {
            "required_role": [UserRole.USER, UserRole.ADMIN],
            "fields": PUBLIC_FIELDS["blog"] + SENSITIVE_FIELDS["blog"]
        },
        "other": {
            "required_role": [UserRole.USER, UserRole.ADMIN],
            "fields": PUBLIC_FIELDS["blog"]
        }
    },
    
    # 系统管理规则
    "system_management": {
        "required_role": [UserRole.ADMIN],
        "permissions": [
            "view_system_config",
            "modify_system_config",
            "view_system_logs",
            "manage_cache"
        ]
    },
    
    # 用户管理规则
    "user_management": {
        "required_role": [UserRole.ADMIN],
        "permissions": [
            "view_all_users",
            "modify_user_status",
            "reset_user_password",
            "delete_user"
        ]
    }
}


# 权限错误消息配置
PERMISSION_ERROR_MESSAGES = {
    "unauthorized": "需要登录才能访问",
    "forbidden": "无权限访问该资源",
    "profile_access_denied": "无权限查看该用户资料",
    "sensitive_fields_access_denied": "无权限查看敏感信息",
    "admin_required": "需要管理员权限",
    "user_management_required": "需要用户管理权限",
    "system_management_required": "需要系统管理权限",
    "frozen_user": "账户已被冻结，无法访问",
    "user_not_found": "用户不存在",
    "resource_not_found": "资源不存在"
}


def get_permission_level(role: UserRole, resource: ResourceType) -> PermissionLevel:
    """
    获取指定角色对指定资源的权限级别
    
    Args:
        role: 用户角色
        resource: 资源类型
        
    Returns:
        PermissionLevel: 权限级别
    """
    if role in PERMISSION_MATRIX and resource in PERMISSION_MATRIX[role]:
        return PERMISSION_MATRIX[role][resource]
    return PermissionLevel.NONE


def can_access_resource(role: UserRole, resource: ResourceType, level: PermissionLevel = PermissionLevel.READ) -> bool:
    """
    检查指定角色是否可以访问指定资源
    
    Args:
        role: 用户角色
        resource: 资源类型
        level: 所需权限级别
        
    Returns:
        bool: 是否可以访问
    """
    user_level = get_permission_level(role, resource)
    return user_level.value >= level.value


def get_accessible_fields(role: UserRole, resource_type: str, is_own: bool = False) -> List[str]:
    """
    获取指定角色可以访问的字段列表
    
    Args:
        role: 用户角色
        resource_type: 资源类型 ('user' 或 'blog')
        is_own: 是否是自己的资源
        
    Returns:
        List[str]: 可访问的字段列表
    """
    if role == UserRole.FROZEN:
        return []
    
    if is_own:
        # 自己的资源，可以访问所有字段
        return PUBLIC_FIELDS.get(resource_type, []) + SENSITIVE_FIELDS.get(resource_type, [])
    else:
        # 他人的资源，根据角色决定
        if role == UserRole.ADMIN:
            # 管理员可以访问所有字段
            return PUBLIC_FIELDS.get(resource_type, []) + SENSITIVE_FIELDS.get(resource_type, [])
        else:
            # 普通用户只能访问公开字段
            return PUBLIC_FIELDS.get(resource_type, [])
