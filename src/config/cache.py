"""
缓存配置模块
提供Redis连接配置和缓存设置
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseSettings):
    """缓存配置类"""
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    
    # 缓存配置
    cache_prefix: str = "blogn2"
    default_ttl: int = 3600  # 默认缓存时间1小时
    max_ttl: int = 86400     # 最大缓存时间24小时
    
    # 缓存策略
    enable_cache: bool = True
    cache_debug: bool = False
    
    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 允许大小写不敏感的环境变量
        extra="ignore"  # 忽略额外的环境变量
    )


# 创建全局缓存配置实例
cache_settings = CacheSettings()


def validate_cache_config() -> dict:
    """验证缓存配置并返回配置信息"""
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
    
    # 打印配置信息（仅在调试模式下）
    if cache_settings.cache_debug:
        print(f"Cache configuration loaded: {config_info}")
    
    return config_info


def get_redis_url() -> str:
    """获取Redis连接URL"""
    if cache_settings.redis_password:
        return f"redis://:{cache_settings.redis_password}@{cache_settings.redis_host}:{cache_settings.redis_port}/{cache_settings.redis_db}"
    else:
        return f"redis://{cache_settings.redis_host}:{cache_settings.redis_port}/{cache_settings.redis_db}"


def get_cache_key_prefix() -> str:
    """获取缓存键前缀"""
    return f"{cache_settings.cache_prefix}:"


# 缓存键生成器
class CacheKeyGenerator:
    """缓存键生成器"""
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        """用户资料缓存键"""
        return f"user:profile:{user_id}"
    
    @staticmethod
    def blog_list(page: int = 1, limit: int = 10) -> str:
        """博客列表缓存键"""
        return f"blog:list:{page}:{limit}"
    
    @staticmethod
    def blog_detail(blog_id: int) -> str:
        """博客详情缓存键"""
        return f"blog:detail:{blog_id}"
    
    @staticmethod
    def blog_comments(blog_id: int) -> str:
        """博客评论缓存键"""
        return f"blog:comments:{blog_id}"
    
    @staticmethod
    def user_blogs(user_id: int, page: int = 1) -> str:
        """用户博客列表缓存键"""
        return f"user:blogs:{user_id}:{page}"
    
    @staticmethod
    def search_results(query: str, page: int = 1) -> str:
        """搜索结果缓存键"""
        return f"search:{query}:{page}"
    
    @staticmethod
    def metadata() -> str:
        """元数据缓存键"""
        return "metadata:site" 