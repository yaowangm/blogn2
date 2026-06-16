"""
应用常量定义

定义应用中使用的各种常量，避免魔法数字和字符串，提高代码可读性和维护性。

常量分类：
- 状态常量：文章、项目、用户等实体的状态值
- 角色常量：用户角色和权限级别
- 文件常量：文件类型和大小限制
- 缓存常量：缓存键前缀和默认值
- 错误常量：统一的错误消息

使用说明：
- 所有状态值应使用对应的常量类
- 新增状态时应在相应常量类中添加
- 避免在代码中直接使用魔法数字
"""

# 文章状态常量
class ArticleStatus:
    """文章状态常量"""
    UNKNOWN = 0      # 未知状态
    NORMAL = 1       # 正常状态
    DELETED = 2      # 已删除状态

# 项目状态常量
class ProjectStatus:
    """项目（博客）状态常量，与生产库 project.state 一致"""
    ACTIVE = 0       # 正常
    DISABLED = 1     # 禁用

# 通用状态常量
class Status:
    """通用状态常量"""
    INACTIVE = 0     # 非活跃状态
    ACTIVE = 1       # 活跃状态

# 注册码状态常量
class RegKeyStatus:
    """注册码状态常量"""
    UNUSED = 1       # 未使用
    USED = 2         # 已使用

# 评论状态常量
class CommentStatus:
    """评论状态常量"""
    INACTIVE = 0     # 非活跃状态
    ACTIVE = 1       # 活跃状态

# 用户角色常量
class UserRole:
    """用户角色常量"""
    GUEST = 0        # 访客
    USER = 1         # 普通用户
    ADMIN = 2        # 管理员

# 文件类型常量
class FileType:
    """文件类型常量"""
    IMAGE = 1        # 图片文件
    DOCUMENT = 2     # 文档文件
    OTHER = 3        # 其他文件

# 缓存键前缀常量
class CachePrefix:
    """缓存键前缀常量"""
    ARTICLE = "article"
    USER = "user"
    PROJECT = "project"
    COMMENT = "comment"
    ATTACHMENT = "attachment"

# 默认值常量
class Defaults:
    """默认值常量"""
    PAGE_SIZE = 10           # 默认分页大小
    MAX_FILE_SIZE = 1048576  # 默认最大文件大小（1MB）
    CACHE_TTL = 600          # 默认缓存时间（10分钟）
    MAX_ATTACHMENTS = 10     # 默认最大附件数量

# 错误消息常量
class ErrorMessages:
    """错误消息常量"""
    ARTICLE_NOT_FOUND = "文章不存在"
    ARTICLE_DELETED = "文章已被删除"
    PERMISSION_DENIED = "权限不足"
    INVALID_FILE_TYPE = "不支持的文件类型"
    FILE_TOO_LARGE = "文件过大"
    INVALID_FILENAME = "文件名包含非法字符"
