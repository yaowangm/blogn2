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


async def test_redis_connection():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")
    
    try:
        # 获取Redis URL
        redis_url = get_redis_url()
        print(f"📡 Redis URL: {redis_url}")
        
        # 初始化缓存管理器
        await cache_manager.initialize()
        
        if cache_manager.is_available():
            print("✅ Redis连接成功！")
            
            # 测试基本缓存操作
            test_key = "test:connection"
            test_value = {"message": "Hello Redis!", "timestamp": "2024-01-01"}
            
            # 设置缓存
            success = await cache_manager.set(test_key, test_value, ttl=60)
            if success:
                print("✅ 缓存设置成功")
            else:
                print("❌ 缓存设置失败")
            
            # 获取缓存
            cached_value = await cache_manager.get(test_key)
            if cached_value:
                print("✅ 缓存获取成功")
                print(f"📦 缓存内容: {cached_value}")
            else:
                print("❌ 缓存获取失败")
            
            # 删除缓存
            delete_success = await cache_manager.delete(test_key)
            if delete_success:
                print("✅ 缓存删除成功")
            else:
                print("❌ 缓存删除失败")
                
        else:
            print("❌ Redis连接失败！")
            print("💡 请检查Redis服务是否运行，以及配置是否正确")
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        print("💡 请确保Redis服务正在运行")


async def test_cache_settings():
    """测试缓存配置"""
    print("\n🔧 缓存配置信息:")
    print(f"   Redis主机: {cache_settings.redis_host}")
    print(f"   Redis端口: {cache_settings.redis_port}")
    print(f"   Redis数据库: {cache_settings.redis_db}")
    print(f"   缓存启用: {cache_settings.enable_cache}")
    print(f"   调试模式: {cache_settings.cache_debug}")
    print(f"   默认TTL: {cache_settings.default_ttl}秒")
    print(f"   最大TTL: {cache_settings.max_ttl}秒")
    print(f"   缓存前缀: {cache_settings.cache_prefix}")


async def main():
    """主函数"""
    print("🚀 Redis缓存系统测试")
    print("=" * 50)
    
    # 测试配置
    await test_cache_settings()
    
    # 测试连接
    await test_redis_connection()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")


if __name__ == "__main__":
    asyncio.run(main()) 