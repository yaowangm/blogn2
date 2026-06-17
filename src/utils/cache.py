"""
缓存工具模块

提供缓存装饰器和工具函数，支持Redis后端缓存系统。
包含智能缓存管理、装饰器、统计功能等。
"""

import asyncio
import json
import logging
import os
import sys
from functools import wraps
from typing import Any, Callable, Optional, Union
from datetime import datetime, timedelta

from fastapi import HTTPException
from starlette.responses import Response as StarletteResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from src.config.cache import cache_settings, CacheKeyGenerator
import redis.asyncio as redis

logger = logging.getLogger(__name__)


# ==================== JSON 序列化工具 ====================

def _json_serializer(obj: Any) -> Any:
    """
    自定义 JSON 序列化器，处理 datetime、SQLModel、Pydantic 等不可序列化的对象

    Args:
        obj: 要序列化的对象

    Returns:
        可序列化的对象
    """
    # 处理 datetime 对象
    if isinstance(obj, datetime):
        return obj.isoformat()

    # 处理 SQLModel 和 Pydantic BaseModel 对象
    # SQLModel 继承自 Pydantic BaseModel，所以检查 BaseModel 即可
    if hasattr(obj, 'model_dump'):
        # Pydantic v2 使用 model_dump()
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        # Pydantic v1 使用 dict()
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        # 普通对象，尝试使用 __dict__
        return obj.__dict__

    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# ==================== 工具函数 ====================

def _is_testing_environment() -> bool:
    """检查是否在测试环境中"""
    # 检查环境变量
    if os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("TESTING") == "true":
        return True

    # 检查命令行参数
    if any("pytest" in arg for arg in sys.argv):
        return True

    # 检查是否在pytest模块中运行
    if "pytest" in sys.modules:
        return True

    # 检查调用栈中是否有pytest相关模块
    import inspect
    frame = inspect.currentframe()
    while frame:
        if frame.f_code.co_filename and "pytest" in frame.f_code.co_filename:
            return True
        frame = frame.f_back

    # 调试信息
    if os.getenv("CACHE_DEBUG") == "true":
        logger.debug(f"测试环境检测: PYTEST_CURRENT_TEST={os.getenv('PYTEST_CURRENT_TEST')}, "
              f"TESTING={os.getenv('TESTING')}, pytest in modules={'pytest' in sys.modules}, "
              f"pytest in argv={any('pytest' in arg for arg in sys.argv)}")

    return False


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
    """缓存管理器，负责Redis连接和缓存操作"""

    def __init__(self):
        self._backend = None
        self._initialized = False

    async def initialize(self):
        """初始化缓存系统"""
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

    def get_redis_client(self):
        """获取底层 Redis client（不可用时返回 None）"""
        if not self.is_available() or not self._backend:
            return None
        return self._backend.redis

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
            value_str = json.dumps(value, ensure_ascii=False, default=_json_serializer)
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
        """清除匹配模式的缓存。pattern 可与键一致或省略前缀，内部会统一加前缀以匹配实际存储的键。"""
        if not self.is_available():
            return False
        pattern = _ensure_cache_prefix(pattern)
        try:
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._backend.redis.scan(cursor, match=pattern, count=1000)
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
    enable_cache: bool = True,
    store_empty_list: bool = True,
):
    """
    通用缓存装饰器

    Args:
        ttl: 缓存时间（秒），默认使用配置中的default_ttl
        key_builder: 自定义键生成器函数
        enable_cache: 是否启用缓存
        store_empty_list: 为 False 时不写入空列表 []（避免异常兜底或瞬态空结果被长期缓存）

    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 在测试环境中直接跳过缓存
            if _is_testing_environment():
                return await func(*args, **kwargs)

            # 缓存启用检查
            if not enable_cache or not cache_settings.enable_cache:
                return await func(*args, **kwargs)

            try:
                await cache_manager.initialize()
                if not cache_manager.is_available():
                    return await func(*args, **kwargs)

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
                    # 历史上可能把 [] 写入缓存；对「不缓存空列表」的端点视为未命中并删键，避免首页长期空白
                    if (
                        not store_empty_list
                        and isinstance(cached_value, list)
                        and len(cached_value) == 0
                    ):
                        await cache_manager.delete(cache_key)
                    else:
                        if cache_settings.cache_debug:
                            logger.debug(f"缓存命中: {cache_key}")
                        return cached_value

                # 执行函数并缓存结果
                result = await func(*args, **kwargs)

                # Response（如 RSS XML）含 bytes，无法 JSON 序列化，跳过写入缓存
                if isinstance(result, StarletteResponse):
                    return result

                # 设置缓存
                cache_ttl = ttl or cache_settings.default_ttl
                if not store_empty_list and isinstance(result, list) and len(result) == 0:
                    if cache_settings.cache_debug:
                        logger.debug(f"跳过缓存空列表: {cache_key}")
                else:
                    await cache_manager.set(cache_key, result, cache_ttl)

                if cache_settings.cache_debug:
                    logger.debug(f"缓存设置: {cache_key}, TTL: {cache_ttl}")

                return result
            except Exception as e:
                # 对于HTTPException等业务异常，应该直接抛出
                if isinstance(e, (HTTPException, ValueError, TypeError)):
                    raise e

                # 对于缓存相关的异常，记录日志并直接执行函数
                logger.warning(f"缓存操作失败，直接执行函数: {e}")
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    缓存失效装饰器

    Args:
        pattern: 缓存键模式，支持通配符

    Returns:
        装饰后的函数
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

# 用户相关缓存装饰器
def cache_user_profile(ttl: int = None, enable_cache: bool = True):
    """用户资料缓存装饰器"""
    return cache_decorator(ttl=ttl, enable_cache=enable_cache, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.user_profile(kwargs.get('user_id', 0)))


def cache_user_summary(ttl: int = None):
    """用户摘要缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: "user:summary")


def cache_user_count(ttl: int = None):
    """用户数量缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: "user:count")


def cache_new_users(ttl: int = None):
    """最新用户缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          f"user:new:{kwargs.get('limit', 3)}")


def cache_user_blogs(ttl: int = None):
    """用户博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.user_blogs(kwargs.get('user_id', 0), kwargs.get('page', 1)))


# 博客相关缓存装饰器
def cache_blog_list(ttl: int = None, enable_cache: bool = True):
    """博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, enable_cache=enable_cache, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blog_list(kwargs.get('page', 1), kwargs.get('limit', 10)))


def cache_blog_recent_list(ttl: int = None):
    """最新博文列表缓存装饰器（/blogs/posts/latest）"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          f"blog:recent:list:{kwargs.get('page', 1)}:{kwargs.get('page_size', 10)}:{kwargs.get('exclude', 'none')}:{kwargs.get('blogid', 'none')}")


def cache_blogs_joined_recent(ttl: int = None):
    """最新加入博客列表缓存装饰器（/blogs/recent）"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blogs_joined_recent(kwargs.get('limit', 10)))


def cache_blog_popular_list(ttl: int = None):
    """热门博客列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          f"blog:popular:list:{kwargs.get('limit', 10)}")


def cache_blog_detail(ttl: int = None):
    """博客详情缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blog_detail(kwargs.get('blog_id', 0)))


def cache_blog_comments(ttl: int = None):
    """全站最近评论缓存装饰器（/comments/recent）"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.site_recent_comments(kwargs.get('limit', 5)))


def _blog_messages_recent_cache_key(*args, **kwargs) -> str:
    """与 FastAPI 注入参数兼容：limit 可能在 kwargs 或靠前位置参数中。"""
    limit = kwargs.get("limit")
    if limit is None:
        for a in args:
            if isinstance(a, int) and not isinstance(a, bool):
                limit = a
                break
    if limit is None:
        limit = 5
    return CacheKeyGenerator.blog_messages_recent(limit)


def cache_blog_messages_recent(ttl: int = None):
    """最近留言缓存装饰器（不缓存空列表，避免与留言列表 API 出现「卡片空、列表有」的长期不一致）"""
    return cache_decorator(
        ttl=ttl,
        key_builder=_blog_messages_recent_cache_key,
        store_empty_list=False,
    )


def cache_blog_messages_list(ttl: int = None):
    """留言列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blog_messages_list(
                              kwargs.get('page', 1),
                              kwargs.get('limit', 10)
                          ))


def cache_blog_message_thread(ttl: int = None):
    """留言主题缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blog_message_thread(kwargs.get('thread_id', 0)))


# 其他缓存装饰器
def cache_search_results(ttl: int = None):
    """搜索结果缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.search_results(
                              kwargs.get('q') or kwargs.get('query', ''),
                              kwargs.get('page', 1),
                              kwargs.get('type', kwargs.get('search_type', 'all')),
                              kwargs.get('sort', 'relevance'),
                              kwargs.get('limit', 10),
                          ))


def cache_global_stats(ttl: int = 60):
    """全局统计缓存装饰器（短 TTL）"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: "stats:global")


def cache_metadata(ttl: int = None):
    """元数据缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: CacheKeyGenerator.metadata())


# 文章相关缓存装饰器
def cache_article_detail(ttl: int = None):
    """文章详情缓存装饰器（按评论分页区分缓存键，避免分页时返回同一页缓存）"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.article_detail(
                              kwargs.get('article_id', 0),
                              kwargs.get('page', 1),
                              kwargs.get('per_page', 10),
                              kwargs.get('include_comments', False),
                          ))


def cache_article_comments(ttl: int = None):
    """文章评论缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.article_comments(
                              kwargs.get('article_id', 0),
                              kwargs.get('page', 1),
                              kwargs.get('limit', 20)
                          ))


def cache_article_attachments(ttl: int = None):
    """文章附件缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.article_attachments(kwargs.get('article_id', 0)))


# 项目相关缓存装饰器
def cache_project_detail(ttl: int = None):
    """项目详情缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_detail(kwargs.get('project_id', 0)))


def cache_project_posts(ttl: int = None):
    """项目文章列表缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_posts(
                              kwargs.get('project_id', 0),
                              kwargs.get('page', 1),
                              kwargs.get('limit', 10),
                              kwargs.get('type', 'original'),
                              kwargs.get('folderid'),
                              kwargs.get('include_deleted', False),
                          ))


def cache_project_comments(ttl: int = None):
    """项目最近评论缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_comments(
                              kwargs.get('project_id', 0),
                              kwargs.get('limit', 5),
                          ))


def cache_project_categories(ttl: int = None):
    """项目分类缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_categories(kwargs.get('project_id', 0)))


def cache_project_external_links(ttl: int = None):
    """项目外部链接缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_external_links(kwargs.get('project_id', 0)))


def cache_project_rss(ttl: int = None):
    """项目RSS缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_rss(kwargs.get('project_id', 0)))


def cache_project_stats(ttl: int = None):
    """项目统计缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_stats(kwargs.get('project_id', 0)))


def cache_user_projects(ttl: int = None):
    """用户项目缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.user_projects(kwargs.get('user_id', 0)))


# RSS相关缓存装饰器
def cache_site_rss(ttl: int = None):
    """站点RSS缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.site_rss(kwargs.get('limit', 20)))


def cache_blog_rss(ttl: int = None):
    """博客RSS缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blog_rss(kwargs.get('project_id', 0), kwargs.get('limit', 20)))


def cache_site_rss_full(ttl: int = None):
    """完整站点RSS缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.site_rss_full(kwargs.get('limit', 20)))


def cache_blog_rss_full(ttl: int = None):
    """完整博客RSS缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.blog_rss_full(kwargs.get('project_id', 0), kwargs.get('limit', 20)))


# 友情链接相关缓存装饰器
def cache_project_friend_links(ttl: int = None):
    """项目友情链接缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs:
                          CacheKeyGenerator.project_friend_links(kwargs.get('project_id', 0)))


def cache_all_friend_links(ttl: int = None):
    """所有友情链接缓存装饰器"""
    return cache_decorator(ttl=ttl, key_builder=lambda *args, **kwargs: CacheKeyGenerator.all_friend_links())


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


def invalidate_article_cache():
    """文章相关缓存失效装饰器"""
    return invalidate_cache_pattern("article:*")


def invalidate_article_detail_cache(article_id: int):
    """特定文章详情缓存失效装饰器（清除该文章所有评论分页的缓存）"""
    pattern = f"article:detail:{article_id}:*"
    return invalidate_cache_pattern(pattern)


def invalidate_article_comments_cache(article_id: int):
    """特定文章评论缓存失效装饰器"""
    return invalidate_cache_pattern(f"article:comments:{article_id}:*")


def invalidate_article_attachments_cache(article_id: int):
    """特定文章附件缓存失效装饰器"""
    return invalidate_cache_pattern(f"article:attachments:{article_id}")


# ==================== 直接缓存失效函数 ====================

async def clear_article_cache():
    """直接清除所有文章相关缓存"""
    if cache_settings.enable_cache:
        await cache_manager.clear_pattern("article:*")
        if cache_settings.cache_debug:
            logger.debug("清除所有文章相关缓存")


async def clear_article_detail_cache(article_id: int):
    """直接清除特定文章详情缓存（含该文章所有评论分页）"""
    if cache_settings.enable_cache:
        pattern = f"article:detail:{article_id}:*"
        await cache_manager.clear_pattern(pattern)
        if cache_settings.cache_debug:
            logger.debug(f"清除文章详情缓存: {pattern}")


async def clear_article_comments_cache(article_id: int):
    """直接清除特定文章评论缓存"""
    if cache_settings.enable_cache:
        await cache_manager.clear_pattern(f"article:comments:{article_id}:*")
        if cache_settings.cache_debug:
            logger.debug(f"清除文章评论缓存: article:comments:{article_id}:*")


async def clear_article_attachments_cache(article_id: int):
    """直接清除特定文章附件缓存"""
    if cache_settings.enable_cache:
        await cache_manager.clear_pattern(f"article:attachments:{article_id}")
        if cache_settings.cache_debug:
            logger.debug(f"清除文章附件缓存: article:attachments:{article_id}")


async def clear_blog_messages_cache():
    """直接清除所有留言相关缓存"""
    if cache_settings.enable_cache:
        await cache_manager.clear_pattern("blog:messages:*")
        if cache_settings.cache_debug:
            logger.debug("清除所有留言相关缓存: blog:messages:*")


async def invalidate_project_post_list_caches(
    project_id: int, owner_user_id: Optional[int] = None
) -> None:
    """
    某博客下文章列表/数量变化后失效缓存（含分页、分类、详情、统计、RSS、全站最新文章等）。
    避免 N 分钟内列表仍为旧数据。
    """
    if not cache_settings.enable_cache:
        return
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning("缓存未初始化，跳过 project 文章相关失效: %s", e)
        return
    if not cache_manager.is_available():
        return

    patterns = [
        f"project:posts:{project_id}:*",
        f"project:detail:{project_id}",
        f"project:stats:{project_id}",
        f"project:rss:{project_id}",
        f"project:categories:{project_id}",
        "blog:recent:list:*",
        "blog:list:*",
        "rss:site*",
        f"rss:blog:{project_id}*",
    ]
    if owner_user_id is not None:
        patterns.append(f"user:projects:{owner_user_id}")

    async def clear_one(pattern: str) -> None:
        try:
            await cache_manager.clear_pattern(pattern)
        except Exception as e:
            logger.warning("清除缓存模式失败 %s: %s", pattern, e)

    await asyncio.gather(*(clear_one(pattern) for pattern in patterns))


async def invalidate_site_recent_comments_cache() -> None:
    """评论增减后：失效全站最近评论缓存。"""
    if not cache_settings.enable_cache:
        return
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning("缓存未初始化，跳过全站最近评论缓存失效: %s", e)
        return
    if not cache_manager.is_available():
        return
    try:
        await cache_manager.clear_pattern("blog:comments:recent:*")
    except Exception as e:
        logger.warning("清除缓存模式失败 blog:comments:recent:*: %s", e)


async def invalidate_project_recent_comments_cache(project_id: int) -> None:
    """评论增减后：博客「最近评论」及依赖评论计数的 project 详情/统计缓存。"""
    if not cache_settings.enable_cache:
        return
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning("缓存未初始化，跳过 project 评论相关失效: %s", e)
        return
    if not cache_manager.is_available():
        return
    patterns = (
        f"project:comments:{project_id}:*",
        f"project:detail:{project_id}",
        f"project:stats:{project_id}",
    )

    async def clear_one(pattern: str) -> None:
        try:
            await cache_manager.clear_pattern(pattern)
        except Exception as e:
            logger.warning("清除缓存模式失败 %s: %s", pattern, e)

    await asyncio.gather(*(clear_one(pattern) for pattern in patterns))
    await invalidate_site_recent_comments_cache()


async def invalidate_project_categories_cache(project_id: int) -> None:
    """分类增删改后，失效该博客分类列表缓存。"""
    if not cache_settings.enable_cache:
        return
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning("缓存未初始化，跳过 project 分类缓存失效: %s", e)
        return
    if not cache_manager.is_available():
        return
    try:
        await cache_manager.clear_pattern(f"project:categories:{project_id}")
    except Exception as e:
        logger.warning("清除缓存模式失败 project:categories: %s", e)


async def invalidate_blog_directory_caches(user_id: int) -> None:
    """新建博客等：全站博客列表、元数据与用户博客入口缓存。"""
    if not cache_settings.enable_cache:
        return
    try:
        await cache_manager.initialize()
    except Exception as e:
        logger.warning("缓存未初始化，跳过全站博客目录缓存失效: %s", e)
        return
    if not cache_manager.is_available():
        return
    patterns = ["blog:list:*", "metadata:*", f"user:projects:{user_id}"]

    async def clear_one(pattern: str) -> None:
        try:
            await cache_manager.clear_pattern(pattern)
        except Exception as e:
            logger.warning("清除缓存模式失败 %s: %s", pattern, e)

    await asyncio.gather(*(clear_one(pattern) for pattern in patterns))


# ==================== 缓存统计 ====================

class CacheStats:
    """缓存统计类，提供缓存命中率等统计信息"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0

    def hit(self):
        """记录缓存命中"""
        self.hits += 1

    def miss(self):
        """记录缓存未命中"""
        self.misses += 1

    def set(self):
        """记录缓存设置"""
        self.sets += 1

    def delete(self):
        """记录缓存删除"""
        self.deletes += 1

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            Dict: 包含缓存统计信息的字典
        """
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
