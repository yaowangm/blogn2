#!/usr/bin/env python3
"""
Redis连接测试脚本
用于测试Redis连接和缓存功能
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.cache import cache_settings, get_redis_url
from src.utils.cache import cache_manager


# ==================== 测试函数 ====================

async def test_basic_cache_operations():
    """测试基本缓存操作"""
    test_key = "test:connection"
    test_value = {"message": "Hello Redis!", "timestamp": "2024-01-01"}
    
    # 设置缓存
    success = await cache_manager.set(test_key, test_value, ttl=60)
    if success:
        print("✅ 缓存设置成功")
    else:
        print("❌ 缓存设置失败")
        return False
    
    # 获取缓存
    cached_value = await cache_manager.get(test_key)
    if cached_value:
        print("✅ 缓存获取成功")
        print(f"📦 缓存内容: {cached_value}")
    else:
        print("❌ 缓存获取失败")
        return False
    
    # 删除缓存
    delete_success = await cache_manager.delete(test_key)
    if delete_success:
        print("✅ 缓存删除成功")
    else:
        print("❌ 缓存删除失败")
        return False
    
    return True


async def test_redis_connection():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")
    
    try:
        redis_url = get_redis_url()
        print(f"📡 Redis URL: {redis_url}")
        
        await cache_manager.initialize()
        
        if cache_manager.is_available():
            print("✅ Redis连接成功！")
            return await test_basic_cache_operations()
        else:
            print("❌ Redis连接失败！")
            print("💡 请检查Redis服务是否运行，以及配置是否正确")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        print("💡 请确保Redis服务正在运行")
        return False


def test_cache_settings():
    """测试缓存配置"""
    print("\n🔧 缓存配置信息:")
    config_items = [
        ("Redis主机", cache_settings.redis_host),
        ("Redis端口", cache_settings.redis_port),
        ("Redis数据库", cache_settings.redis_db),
        ("缓存启用", cache_settings.enable_cache),
        ("调试模式", cache_settings.cache_debug),
        ("默认TTL", f"{cache_settings.default_ttl}秒"),
        ("最大TTL", f"{cache_settings.max_ttl}秒"),
        ("缓存前缀", cache_settings.cache_prefix)
    ]
    
    for label, value in config_items:
        print(f"   {label}: {value}")


async def main():
    """主函数"""
    print("🚀 Redis缓存系统测试")
    print("=" * 50)
    
    # 测试配置
    test_cache_settings()
    
    # 测试连接
    connection_success = await test_redis_connection()
    
    print("\n" + "=" * 50)
    if connection_success:
        print("🏁 所有测试通过！")
    else:
        print("🏁 测试完成，但存在问题")
        print("💡 请检查Redis配置和服务状态")


if __name__ == "__main__":
    asyncio.run(main()) 