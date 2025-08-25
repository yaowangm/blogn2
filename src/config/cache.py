"""
缓存配置模块

提供Redis连接配置和缓存设置，支持环境变量配置。
包含缓存键生成器和配置验证功能。
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseSettings):
    """
    缓存配置类
    
    支持从环境变量和.env文件加载配置。
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
        env_file=".env",
        env_file_encoding="utf-8",
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
        "config_source": "environment" if cache_settings.model_config.get("env_file") else "defaults"
    }
    
    if cache_settings.cache_debug:
        print(f"Cache configuration loaded: {config_info}")
    
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
    def article_detail(article_id: int) -> str:
        """
        文章详情缓存键
        
        Args:
            article_id: 文章ID
            
        Returns:
            str: 文章详情缓存键
        """
        return CacheKeyGenerator._build_key("article", "detail", article_id)
    
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