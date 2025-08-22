#!/usr/bin/env python3
"""
数据库连接测试脚本

验证数据库连接是否正常，测试基本查询功能。
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database import get_async_session
from src.models.user import User

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """测试数据库连接和基本查询功能"""
    try:
        logger.info("🔍 测试数据库连接...")
        
        # 获取数据库URL
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL 环境变量未设置")
            return False
        
        logger.info(f"📡 数据库URL: {DATABASE_URL}")
        
        # 测试数据库连接
        async for session in get_async_session():
            # 执行简单查询
            result = await session.execute("SELECT 1")
            logger.info("✅ 数据库连接成功")
            
            # 测试用户表查询
            users = await session.execute("SELECT * FROM users LIMIT 5")
            users = users.fetchall()
            
            if users:
                logger.info(f"✅ 查询成功！找到 {len(users)} 个用户")
                
                logger.info("\n📋 用户列表:")
                for i, user in enumerate(users[:5]):
                    logger.info(f"  - ID: {user.id}, 用户名: {user.name}, 邮箱: {user.email}")
                
                if len(users) > 5:
                    logger.info(f"  ... 还有 {len(users) - 5} 个用户")
            else:
                logger.info("ℹ️  用户表为空或查询失败")
            
            break
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始数据库连接测试...")
    
    success = await test_database_connection()
    
    if success:
        logger.info("\n🎉 数据库连接测试成功！")
    else:
        logger.error("\n💥 数据库连接测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 