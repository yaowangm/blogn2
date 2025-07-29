#!/usr/bin/env python3
"""
简单的数据库连接测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入数据库模块
from src.database import DATABASE_URL, async_engine, async_session
from src.models.user import User
from sqlmodel import select

async def test_connection():
    """测试数据库连接"""
    try:
        print(f"🔍 测试数据库连接...")
        print(f"📡 数据库URL: {DATABASE_URL}")
        
        # 测试连接
        async with async_engine.begin() as conn:
            print("✅ 数据库连接成功")
        
        # 测试查询
        async with async_session() as session:
            result = await session.exec(select(User))
            users = result.all()
            print(f"✅ 查询成功！找到 {len(users)} 个用户")
            
            if users:
                print("\n📋 用户列表:")
                for user in users[:5]:  # 只显示前5个
                    print(f"  - ID: {user.id}, 用户名: {user.name}, 邮箱: {user.email}")
                if len(users) > 5:
                    print(f"  ... 还有 {len(users) - 5} 个用户")
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_connection())
    if success:
        print("\n🎉 数据库连接测试成功！")
    else:
        print("\n💥 数据库连接测试失败！")
        sys.exit(1) 