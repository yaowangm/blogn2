#!/usr/bin/env python3
"""
Redis连接和功能测试脚本

测试Redis连接是否正常，验证基本的缓存操作功能。
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.cache import get_redis_url
import redis.asyncio as redis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_cache_operations(redis_client):
    """
    测试基本的缓存操作
    
    Args:
        redis_client: Redis客户端实例
        
    Returns:
        bool: 测试是否成功
    """
    try:
        # 测试设置缓存
        await redis_client.set("test_key", "test_value", ex=60)
        logger.info("✅ 缓存设置成功")
        
        # 测试获取缓存
        cached_value = await redis_client.get("test_key")
        if cached_value == "test_value":
            logger.info("✅ 缓存获取成功")
            logger.info(f"📦 缓存内容: {cached_value}")
        else:
            logger.error("❌ 缓存获取失败")
            return False
        
        # 测试删除缓存
        await redis_client.delete("test_key")
        logger.info("✅ 缓存删除成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 缓存操作测试失败: {e}")
        return False


async def test_redis_connection():
    """测试Redis连接和基本功能"""
    try:
        logger.info("🔍 测试Redis连接...")
        
        # 获取Redis配置
        redis_url = get_redis_url()
        logger.info(f"📡 Redis URL: {redis_url}")
        
        # 创建Redis客户端
        redis_client = redis.from_url(redis_url, encoding='utf-8', decode_responses=True)
        
        # 测试连接
        await redis_client.ping()
        logger.info("✅ Redis连接成功！")
        
        # 测试基本缓存操作
        cache_test_success = await test_basic_cache_operations(redis_client)
        
        # 关闭连接
        await redis_client.close()
        
        return cache_test_success
        
    except Exception as e:
        logger.error(f"❌ Redis连接测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始Redis连接测试...")
    
    success = await test_redis_connection()
    
    if success:
        logger.info("\n🎉 Redis连接测试成功！")
    else:
        logger.error("\n💥 Redis连接测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 