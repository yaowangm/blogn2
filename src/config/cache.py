"""
缓存配置模块

提供Redis连接配置和缓存设置，支持环境变量配置。
包含缓存键生成器和配置验证功能。
"""

import os
import logging
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

from .utils import load_config_file, get_config_file_path

# 加载配置文件（如果存在）
load_config_file()

logger = logging.getLogger(__name__)


class CacheSettings(BaseSettings):
    """
    缓存配置类
    
    配置加载规则：
    1. 在本地开发环境中，可以通过 BLOGN_CONFIG_FILE 环境变量指定配置文件，
       如果未指定，则使用当前目录下的 .env 文件
    2. 在 Docker 容器中，必须通过 BLOGN_CONFIG_FILE 环境变量指定配置文件
    3. 如果未使用配置文件，则使用代码中的默认配置
    所有配置项都有合理的默认值。
    """
    
    # Redis连接配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    
    # 缓存策略配置
    cache_prefix: str = "blogn2"
    default_ttl: int = 600  # 10分钟
    max_ttl: int = 86400    # 24小时
    
    # 功能开关
    enable_cache: bool = True
    cache_debug: bool = False
    
    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        # 使用统一的配置文件加载逻辑
        # env_file 由 load_config_file() 函数处理，这里设置为 None
        # pydantic_settings 会从已加载的环境变量中读取配置
        env_file=None,
        case_sensitive=False,
        extra="ignore"
    )


# 创建全局缓存配置实例
cache_settings = CacheSettings()


def validate_cache_config() -> dict:
    """
    验证缓存配置并返回配置信息
    
    Returns:
        Dict: 包含完整缓存配置信息的字典
    """
    config_file = get_config_file_path()
    config_info = {
        "redis_host": cache_settings.redis_host,
        "redis_port": cache_settings.redis_port,
        "redis_db": cache_settings.redis_db,
        "redis_ssl": cache_settings.redis_ssl,
        "cache_prefix": cache_settings.cache_prefix,
        "default_ttl": cache_settings.default_ttl,
        "max_ttl": cache_settings.max_ttl,
        "enable_cache": cache_settings.enable_cache,
        "cache_debug": cache_settings.cache_debug,
        "config_source": str(config_file) if config_file else "defaults"
    }
    
    if cache_settings.cache_debug:
        logger.debug(f"Cache configuration loaded: {config_info}")
    
    return config_info


def get_redis_url() -> str:
    """
    获取Redis连接URL
    
    Returns:
        str: Redis连接URL字符串
    """
    if cache_settings.redis_password:
        return f"redis://:{cache_settings.redis_password}@{cache_settings.redis_host}:{cache_settings.redis_port}/{cache_settings.redis_db}"
    return f"redis://{cache_settings.redis_host}:{cache_settings.redis_port}/{cache_settings.redis_db}"


def get_cache_key_prefix() -> str:
    """
    获取缓存键前缀
    
    Returns:
        str: 带冒号的缓存键前缀
    """
    return f"{cache_settings.cache_prefix}:"


# ==================== 缓存键生成器 ====================

class CacheKeyGenerator:
    """
    缓存键生成器
    
    提供统一的缓存键生成逻辑，确保键的一致性和唯一性。
    支持各种业务场景的缓存键生成。
    """
    
    @staticmethod
    def _build_key(*parts) -> str:
        """
        构建缓存键的通用方法
        
        Args:
            *parts: 键的各个部分
            
        Returns:
            str: 用冒号连接的缓存键
        """
        return ":".join(str(part) for part in parts if part is not None)
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        """
        用户资料缓存键
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户资料缓存键
        """
        return CacheKeyGenerator._build_key("user", "profile", user_id)
    
    @staticmethod
    def blog_list(page: int = 1, limit: int = 10) -> str:
        """
        博客列表缓存键
        
        Args:
            page: 页码
            limit: 每页数量
            
        Returns:
            str: 博客列表缓存键
        """
        return CacheKeyGenerator._build_key("blog", "list", page, limit)
    
    @staticmethod
    def blog_detail(blog_id: int) -> str:
        """
        博客详情缓存键
        
        Args:
            blog_id: 博客ID
            
        Returns:
            str: 博客详情缓存键
        """
        return CacheKeyGenerator._build_key("blog", "detail", blog_id)
    
    @staticmethod
    def blog_comments(blog_id: int) -> str:
        """
        博客评论缓存键
        
        Args:
            blog_id: 博客ID
            
        Returns:
            str: 博客评论缓存键
        """
        return CacheKeyGenerator._build_key("blog", "comments", blog_id)
    
    @staticmethod
    def user_blogs(user_id: int, page: int = 1) -> str:
        """
        用户博客列表缓存键
        
        Args:
            user_id: 用户ID
            page: 页码
            
        Returns:
            str: 用户博客列表缓存键
        """
        return CacheKeyGenerator._build_key("user", "blogs", user_id, page)
    
    @staticmethod
    def search_results(query: str, page: int = 1) -> str:
        """
        搜索结果缓存键
        
        Args:
            query: 搜索查询
            page: 页码
            
        Returns:
            str: 搜索结果缓存键
        """
        return CacheKeyGenerator._build_key("search", query, page)
    
    @staticmethod
    def metadata() -> str:
        """
        元数据缓存键
        
        Returns:
            str: 元数据缓存键
        """
        return CacheKeyGenerator._build_key("metadata", "site")
    
    @staticmethod
    def article_detail(article_id: int, page: int = 1, per_page: int = 10) -> str:
        """
        文章详情缓存键（含评论分页）
        
        Args:
            article_id: 文章ID
            page: 评论页码
            per_page: 每页评论数
            
        Returns:
            str: 文章详情缓存键
        """
        return CacheKeyGenerator._build_key("article", "detail", article_id, page, per_page)
    
    @staticmethod
    def article_comments(article_id: int, page: int = 1, limit: int = 20) -> str:
        """
        文章评论缓存键
        
        Args:
            article_id: 文章ID
            page: 页码
            limit: 每页数量
            
        Returns:
            str: 文章评论缓存键
        """
        return CacheKeyGenerator._build_key("article", "comments", article_id, page, limit)
    
    @staticmethod
    def article_attachments(article_id: int) -> str:
        """
        文章附件缓存键
        
        Args:
            article_id: 文章ID
            
        Returns:
            str: 文章附件缓存键
        """
        return CacheKeyGenerator._build_key("article", "attachments", article_id)
    
    # ==================== 项目相关缓存键 ====================
    
    @staticmethod
    def project_detail(project_id: int) -> str:
        """
        项目详情缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目详情缓存键
        """
        return CacheKeyGenerator._build_key("project", "detail", project_id)
    
    @staticmethod
    def project_posts(project_id: int, page: int = 1, page_size: int = 10, post_type: str = "original") -> str:
        """
        项目文章列表缓存键
        
        Args:
            project_id: 项目ID
            page: 页码
            page_size: 每页数量
            post_type: 文章类型
            
        Returns:
            str: 项目文章列表缓存键
        """
        return CacheKeyGenerator._build_key("project", "posts", project_id, page, page_size, post_type)
    
    @staticmethod
    def project_comments(project_id: int) -> str:
        """
        项目评论缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目评论缓存键
        """
        return CacheKeyGenerator._build_key("project", "comments", project_id, "recent")
    
    @staticmethod
    def project_categories(project_id: int) -> str:
        """
        项目分类缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目分类缓存键
        """
        return CacheKeyGenerator._build_key("project", "categories", project_id)
    
    @staticmethod
    def project_external_links(project_id: int) -> str:
        """
        项目外部链接缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目外部链接缓存键
        """
        return CacheKeyGenerator._build_key("project", "external_links", project_id)
    
    @staticmethod
    def project_rss(project_id: int) -> str:
        """
        项目RSS缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目RSS缓存键
        """
        return CacheKeyGenerator._build_key("project", "rss", project_id)
    
    @staticmethod
    def project_stats(project_id: int) -> str:
        """
        项目统计缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目统计缓存键
        """
        return CacheKeyGenerator._build_key("project", "stats", project_id)
    
    @staticmethod
    def user_projects(user_id: int) -> str:
        """
        用户项目缓存键
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户项目缓存键
        """
        return CacheKeyGenerator._build_key("user", "projects", user_id)
    
    # ==================== RSS相关缓存键 ====================
    
    @staticmethod
    def site_rss() -> str:
        """
        站点RSS缓存键
        
        Returns:
            str: 站点RSS缓存键
        """
        return CacheKeyGenerator._build_key("rss", "site")
    
    @staticmethod
    def blog_rss(project_id: int) -> str:
        """
        博客RSS缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 博客RSS缓存键
        """
        return CacheKeyGenerator._build_key("rss", "blog", project_id)
    
    @staticmethod
    def site_rss_full() -> str:
        """
        完整站点RSS缓存键
        
        Returns:
            str: 完整站点RSS缓存键
        """
        return CacheKeyGenerator._build_key("rss", "site", "full")
    
    @staticmethod
    def blog_rss_full(project_id: int) -> str:
        """
        完整博客RSS缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 完整博客RSS缓存键
        """
        return CacheKeyGenerator._build_key("rss", "blog", project_id, "full")
    
    # ==================== 友情链接相关缓存键 ====================
    
    @staticmethod
    def project_friend_links(project_id: int) -> str:
        """
        项目友情链接缓存键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目友情链接缓存键
        """
        return CacheKeyGenerator._build_key("friend_links", "project", project_id)
    
    @staticmethod
    def all_friend_links() -> str:
        """
        所有友情链接缓存键
        
        Returns:
            str: 所有友情链接缓存键
        """
        return CacheKeyGenerator._build_key("friend_links", "all")
    
    # ==================== 留言相关缓存键 ====================
    
    @staticmethod
    def blog_messages_recent(limit: int = 5) -> str:
        """
        最近留言缓存键
        
        Args:
            limit: 返回数量限制
            
        Returns:
            str: 最近留言缓存键
        """
        return CacheKeyGenerator._build_key("blog", "messages", "recent", limit)
    
    @staticmethod
    def blog_messages_list(page: int = 1, limit: int = 10) -> str:
        """
        留言列表缓存键
        
        Args:
            page: 页码
            limit: 每页数量
            
        Returns:
            str: 留言列表缓存键
        """
        return CacheKeyGenerator._build_key("blog", "messages", "list", page, limit)
    
    @staticmethod
    def blog_message_thread(thread_id: int) -> str:
        """
        留言主题缓存键
        
        Args:
            thread_id: 主题ID
            
        Returns:
            str: 留言主题缓存键
        """
        return CacheKeyGenerator._build_key("blog", "messages", "thread", thread_id) 