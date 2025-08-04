"""
缓存机制单元测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.utils.cache import (
    cache_manager, 
    cache_decorator, 
    cache_blog_list, 
    cache_user_profile,
    CacheStats
)
from src.config.cache import cache_settings, CacheKeyGenerator


class TestCacheManager:
    """缓存管理器测试类"""

    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self):
        """测试缓存管理器初始化"""
        # 重置缓存管理器状态
        cache_manager._initialized = False
        cache_manager._backend = None
        
        # 测试初始化
        await cache_manager.initialize()
        
        # 验证初始化成功
        assert cache_manager._initialized == True
        assert cache_manager._backend is not None

    @pytest.mark.asyncio
    async def test_cache_set_get_delete(self):
        """测试缓存设置、获取和删除"""
        # 确保缓存已初始化
        await cache_manager.initialize()
        
        # 测试数据
        test_key = "test:cache:key"
        test_value = {"data": "test_value", "timestamp": "2024-01-01"}
        
        # 测试设置缓存
        success = await cache_manager.set(test_key, test_value, ttl=60)
        
        # 如果缓存被禁用，设置操作应该返回False
        if not cache_settings.enable_cache:
            assert success == False
            # 当缓存禁用时，获取操作应该返回None
            cached_value = await cache_manager.get(test_key)
            assert cached_value is None
            # 删除操作也应该返回False
            delete_success = await cache_manager.delete(test_key)
            assert delete_success == False
        else:
            assert success == True
            
            # 测试获取缓存
            cached_value = await cache_manager.get(test_key)
            assert cached_value == test_value
            
            # 测试删除缓存
            delete_success = await cache_manager.delete(test_key)
            assert delete_success == True
            
            # 验证缓存已删除
            deleted_value = await cache_manager.get(test_key)
            assert deleted_value is None

    @pytest.mark.asyncio
    async def test_cache_key_generator(self):
        """测试缓存键生成器"""
        # 测试用户资料缓存键
        user_key = CacheKeyGenerator.user_profile(123)
        assert user_key == "user:profile:123"
        
        # 测试博客列表缓存键
        blog_list_key = CacheKeyGenerator.blog_list(1, 10)
        assert blog_list_key == "blog:list:1:10"
        
        # 测试博客详情缓存键
        blog_detail_key = CacheKeyGenerator.blog_detail(456)
        assert blog_detail_key == "blog:detail:456"
        
        # 测试元数据缓存键
        metadata_key = CacheKeyGenerator.metadata()
        assert metadata_key == "metadata:site"


class TestCacheDecorator:
    """缓存装饰器测试类"""

    @pytest.mark.asyncio
    async def test_cache_decorator_basic(self):
        """测试基本缓存装饰器"""
        # 创建一个测试函数
        call_count = 0
        
        @cache_decorator(ttl=60)
        async def test_function(param1, param2=10):
            nonlocal call_count
            call_count += 1
            return {"result": param1 + param2, "call_count": call_count}
        
        # 第一次调用 - 应该执行函数并缓存结果
        result1 = await test_function(5, param2=15)
        assert result1["result"] == 20
        assert result1["call_count"] == 1
        
        # 第二次调用 - 如果缓存启用，应该从缓存返回；如果禁用，应该重新执行
        result2 = await test_function(5, param2=15)
        assert result2["result"] == 20
        
        if cache_settings.enable_cache:
            assert result2["call_count"] == 1  # 调用次数没有增加
        else:
            assert result2["call_count"] == 2  # 调用次数增加
        
        # 不同参数 - 应该重新执行函数
        result3 = await test_function(10, param2=20)
        assert result3["result"] == 30
        
        if cache_settings.enable_cache:
            assert result3["call_count"] == 2  # 调用次数增加
        else:
            assert result3["call_count"] == 3  # 调用次数增加

    @pytest.mark.asyncio
    async def test_cache_blog_list_decorator(self):
        """测试博客列表缓存装饰器"""
        call_count = 0
        
        @cache_blog_list(ttl=60)
        async def get_blog_list(page=1, limit=10):
            nonlocal call_count
            call_count += 1
            return [{"id": call_count, "title": f"博客{call_count}"}]
        
        # 第一次调用
        result1 = await get_blog_list(page=1, limit=5)
        assert len(result1) == 1
        assert result1[0]["id"] == 1
        
        # 第二次调用相同参数
        result2 = await get_blog_list(page=1, limit=5)
        assert len(result2) == 1
        
        if cache_settings.enable_cache:
            assert result2[0]["id"] == 1  # 仍然是第一次的结果
        else:
            assert result2[0]["id"] == 2  # 新的结果
        
        # 不同参数 - 应该重新执行
        result3 = await get_blog_list(page=2, limit=5)
        assert len(result3) == 1
        
        if cache_settings.enable_cache:
            assert result3[0]["id"] == 2  # 新的结果
        else:
            assert result3[0]["id"] == 3  # 新的结果

    @pytest.mark.asyncio
    async def test_cache_user_profile_decorator(self):
        """测试用户资料缓存装饰器"""
        call_count = 0
        
        @cache_user_profile(ttl=60)
        async def get_user_profile(user_id=0):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "profile": f"用户{user_id}的资料", "call_count": call_count}
        
        # 第一次调用
        result1 = await get_user_profile(user_id=123)
        assert result1["user_id"] == 123
        assert result1["call_count"] == 1
        
        # 第二次调用相同参数
        result2 = await get_user_profile(user_id=123)
        assert result2["user_id"] == 123
        
        if cache_settings.enable_cache:
            assert result2["call_count"] == 1  # 仍然是第一次的结果
        else:
            assert result2["call_count"] == 2  # 新的结果
        
        # 不同用户ID - 应该重新执行
        result3 = await get_user_profile(user_id=456)
        assert result3["user_id"] == 456
        
        if cache_settings.enable_cache:
            assert result3["call_count"] == 2  # 新的结果
        else:
            assert result3["call_count"] == 3  # 新的结果

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """测试缓存禁用情况"""
        call_count = 0
        
        @cache_decorator(ttl=60, enable_cache=False)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return {"call_count": call_count}
        
        # 多次调用都应该执行函数
        result1 = await test_function()
        result2 = await test_function()
        result3 = await test_function()
        
        assert result1["call_count"] == 1
        assert result2["call_count"] == 2
        assert result3["call_count"] == 3


class TestCacheStats:
    """缓存统计测试类"""

    def test_cache_stats_basic(self):
        """测试基本缓存统计"""
        stats = CacheStats()
        
        # 初始状态
        initial_stats = stats.get_stats()
        assert initial_stats["hits"] == 0
        assert initial_stats["misses"] == 0
        assert initial_stats["sets"] == 0
        assert initial_stats["deletes"] == 0
        assert initial_stats["hit_rate"] == 0.0
        
        # 模拟一些操作
        stats.hit()
        stats.hit()
        stats.miss()
        stats.set()
        stats.delete()
        
        # 验证统计
        updated_stats = stats.get_stats()
        assert updated_stats["hits"] == 2
        assert updated_stats["misses"] == 1
        assert updated_stats["sets"] == 1
        assert updated_stats["deletes"] == 1
        assert updated_stats["total_requests"] == 3
        assert updated_stats["hit_rate"] == 66.67  # 2/3 * 100

    def test_cache_stats_hit_rate_calculation(self):
        """测试命中率计算"""
        stats = CacheStats()
        
        # 只有命中
        stats.hit()
        stats.hit()
        stats.hit()
        
        result = stats.get_stats()
        assert result["hit_rate"] == 100.0
        
        # 只有未命中
        stats2 = CacheStats()
        stats2.miss()
        stats2.miss()
        
        result2 = stats2.get_stats()
        assert result2["hit_rate"] == 0.0


class TestCacheIntegration:
    """缓存集成测试类"""

    @pytest.mark.asyncio
    async def test_cache_with_real_redis(self):
        """测试与真实Redis的集成"""
        # 确保缓存已初始化
        await cache_manager.initialize()
        
        # 测试数据
        test_data = {"message": "Hello Cache!", "timestamp": "2024-01-01"}
        test_key = "integration:test:key"
        
        # 设置缓存
        success = await cache_manager.set(test_key, test_data, ttl=30)
        
        if cache_settings.enable_cache:
            assert success == True
            
            # 获取缓存
            cached_data = await cache_manager.get(test_key)
            assert cached_data == test_data
            
            # 清理
            await cache_manager.delete(test_key)
        else:
            assert success == False

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """测试缓存TTL过期"""
        # 如果缓存被禁用，跳过此测试
        if not cache_settings.enable_cache:
            pytest.skip("缓存被禁用，跳过TTL测试")
        
        # 设置一个很短的TTL
        test_key = "ttl:test:key"
        test_data = {"expires": "soon"}
        
        # 设置缓存，TTL为1秒
        await cache_manager.set(test_key, test_data, ttl=1)
        
        # 立即获取应该成功
        cached_data = await cache_manager.get(test_key)
        assert cached_data == test_data
        
        # 等待过期
        await asyncio.sleep(2)
        
        # 过期后获取应该返回None
        expired_data = await cache_manager.get(test_key)
        assert expired_data is None 