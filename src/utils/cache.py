"""
缓存工具模块
提供缓存装饰器和工具函数
"""

import asyncio
import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Optional, Union
from datetime import datetime, timedelta

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from src.config.cache import cache_settings, CacheKeyGenerator
import redis.asyncio as redis

logger = logging.getLogger(__name__)


# ==================== 工具函数 ====================

def _is_testing_environment() -> bool:
    """检查是否在测试环境中"""
    return os.getenv("PYTEST_CURRENT_TEST") is not None


def _has_mock_objects(kwargs: dict) -> bool:
    """检查kwargs中是否有模拟对象"""
    return any(
        hasattr(v, '_mock_name') or
        hasattr(v, '_mock_return_value') or
        str(type(v)).find('Mock') != -1 or
        str(type(v)).find('AsyncMock') != -1
        for v in kwargs.values()
    )


def _build_default_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """构建默认缓存键"""
    args_str = "_".join(str(arg) for arg in args)
    kwargs_str = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
    return f"{func_name}:{args_str}:{kwargs_str}"


def _ensure_cache_prefix(key: str) -> str:
    """确保缓存键有正确的前缀"""
    if not key.startswith(f"{cache_settings.cache_prefix}:"):
        return f"{cache_settings.cache_prefix}:{key}"
    return key


# ==================== 缓存管理器 ====================

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._backend = None
        self._initialized = False
    
    async def initialize(self):
        """初始化缓存"""
        if self._initialized:
            return
        
        try:
            from src.config.cache import get_redis_url
            redis_url = get_redis_url()
            redis_client = redis.from_url(redis_url, encoding='utf-8', decode_responses=True)
            self._backend = RedisBackend(redis_client)
            await redis_client.ping()
            FastAPICache.init(self._backend, prefix=cache_settings.cache_prefix)
            self._initialized = True
            logger.info("缓存系统初始化成功")
        except Exception as e:
            logger.error(f"缓存系统初始化失败: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """检查缓存是否可用"""
        return self._initialized and cache_settings.enable_cache
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_available():
            return None
        
        try:
            value = await self._backend.redis.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存值"""
        if not self.is_available():
            return False
        
        try:
            ttl = ttl or cache_settings.default_ttl
            value_str = json.dumps(value, ensure_ascii=False)
            await self._backend.redis.set(key, value_str, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available():
            return False
        
        try:
            await self._backend.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """清除匹配模式的缓存"""
        if not self.is_available():
            return False
        
        try:
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._backend.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._backend.redis.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break
            
            logger.info(f"清除缓存模式 {pattern}: 删除了 {deleted_count} 个键")
            return True
        except Exception as e:
            logger.error(f"清除缓存模式失败 {pattern}: {e}")
            return False


# 全局缓存管理器实例
cache_manager = CacheManager()


# ==================== 缓存装饰器 ====================

def cache_decorator(
    ttl: int = None,
    key_builder: Callable = None,
    enable_cache: bool = True
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        key_builder: 自定义键生成器
        enable_cache: 是否启用缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 测试环境检查
            if _is_testing_environment() and _has_mock_objects(kwargs):
                return await func(*args, **kwargs)
            
            # 缓存启用检查
            if not enable_cache or not cache_settings.enable_cache:
                return await func(*args, **kwargs)
            
            try:
                await cache_manager.initialize()
                
                # 生成缓存键
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = _build_default_cache_key(func.__name__, args, kwargs)
                
                cache_key = _ensure_cache_prefix(cache_key)
                
                # 调试信息
                if cache_settings.cache_debug:
                    logger.debug(f"缓存键: {cache_key}, 参数: args={args}, kwargs={kwargs}")
                
                # 尝试从缓存获取
                cached_value = await cache_manager.get(cache_key)
                if cached_value is not None:
                    if cache_settings.cache_debug:
                        logger.debug(f"缓存命中: {cache_key}")
                    return cached_value
                
                # 执行函数并缓存结果
                result = await func(*args, **kwargs)
                
                # 设置缓存
                cache_ttl = ttl or cache_settings.default_ttl
                await cache_manager.set(cache_key, result, cache_ttl)
                
                if cache_settings.cache_debug:
                    logger.debug(f"缓存设置: {cache_key}, TTL: {cache_ttl}")
                
                return result
            except Exception as e:
                logger.warning(f"缓存操作失败，直接执行函数: {e}")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    缓存失效装饰器
    
    Args:
        pattern: 缓存键模式
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if cache_settings.enable_cache:
                await cache_manager.clear_pattern(pattern)
                if cache_settings.cache_debug:
                    logger.debug(f"清除缓存模式: {pattern}")
            
            return result
        
        return wrapper
    return decorator


# ==================== 预定义缓存装饰器 ====================

def _create_key_builder(key_template: str, param_names: list):
    """创建键生成器的工厂函数"""
    def key_builder(*args, **kwargs):
        params = {}
        for name in param_names:
            params[name] = kwargs.get(name, 0)
        return key_template.format(**params)
    return key_builder


# 用户相关缓存装饰器
def cache_user_profile(ttl: int = 1800):
    """用户资料缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          CacheKeyGenerator.user_profile(kwargs.get('user_id', 0)))


def cache_user_summary(ttl: int = 1800):
    """用户摘要缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: "user:summary")


def cache_user_count(ttl: int = 3600):
    """用户数量缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: "user:count")


def cache_new_users(ttl: int = 900):
    """最新用户缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          f"user:new:{kwargs.get('limit', 3)}")


def cache_user_blogs(ttl: int = 900):
    """用户博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          CacheKeyGenerator.user_blogs(kwargs.get('user_id', 0), kwargs.get('page', 1)))


# 博客相关缓存装饰器
def cache_blog_list(ttl: int = 900):
    """博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          CacheKeyGenerator.blog_list(kwargs.get('page', 1), kwargs.get('limit', 10)))


def cache_blog_recent_list(ttl: int = 900):
    """最新博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          f"blog:recent:list:{kwargs.get('limit', 10)}")


def cache_blog_popular_list(ttl: int = 1800):
    """热门博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          f"blog:popular:list:{kwargs.get('limit', 10)}")


def cache_blog_detail(ttl: int = 3600):
    """博客详情缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          CacheKeyGenerator.blog_detail(kwargs.get('blog_id', 0)))


def cache_blog_comments(ttl: int = 1800):
    """博客评论缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          CacheKeyGenerator.blog_comments(kwargs.get('blog_id', 0)))


def cache_blog_messages(ttl: int = 1800):
    """博客留言缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          f"blog:messages:recent:{kwargs.get('limit', 5)}")


# 其他缓存装饰器
def cache_search_results(ttl: int = 1800):
    """搜索结果缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: 
                          CacheKeyGenerator.search_results(kwargs.get('query', ''), kwargs.get('page', 1)))


def cache_metadata(ttl: int = 7200):
    """元数据缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: CacheKeyGenerator.metadata())


# ==================== 缓存失效装饰器 ====================

def invalidate_user_cache():
    """用户相关缓存失效装饰器"""
    return invalidate_cache_pattern("user:*")


def invalidate_blog_cache():
    """博客相关缓存失效装饰器"""
    return invalidate_cache_pattern("blog:*")


def invalidate_search_cache():
    """搜索相关缓存失效装饰器"""
    return invalidate_cache_pattern("search:*")


def invalidate_metadata_cache():
    """元数据缓存失效装饰器"""
    return invalidate_cache_pattern("metadata:*")


# ==================== 缓存统计 ====================

class CacheStats:
    """缓存统计"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
    
    def hit(self):
        """缓存命中"""
        self.hits += 1
    
    def miss(self):
        """缓存未命中"""
        self.misses += 1
    
    def set(self):
        """缓存设置"""
        self.sets += 1
    
    def delete(self):
        """缓存删除"""
        self.deletes += 1
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2)
        }


# 全局缓存统计实例
cache_stats = CacheStats() 