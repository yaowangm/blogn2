#!/usr/bin/env python3
"""
数据库连接测试脚本
用于验证 .env 文件中的数据库配置是否正确
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
import contextlib

# 加载环境变量
load_dotenv()

async def test_database_connection():
    """测试数据库连接"""
    try:
        # 导入数据库相关模块
        from src.database import async_engine, User, get_async_session
        from sqlmodel import select
        
        print("🔍 正在测试数据库连接...")
        print(f"📡 数据库URL: {os.getenv('DATABASE_URL', '未设置')[:50]}...")
        
        # 测试引擎连接
        async with async_engine.begin() as conn:
            print("✅ 数据库引擎连接成功")
            
            # 测试查询
            session_gen = get_async_session()
            session = await session_gen.__anext__()
            try:
                print("📊 正在测试查询...")
                # 尝试查询用户表
                statement = select(User)
                result = await session.exec(statement)
                users = result.all()
                
                print(f"✅ 查询成功！找到 {len(users)} 个用户")
                
                if users:
                    print("\n📋 用户列表预览:")
                    for i, user in enumerate(users[:3], 1):
                        print(f"  {i}. ID: {user.ID}, 用户名: {user.name}, 邮箱: {user.Email}")
                    if len(users) > 3:
                        print(f"  ... 还有 {len(users) - 3} 个用户")
                else:
                    print("ℹ️  用户表为空")
                
                return True
            finally:
                await session.close()
                
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查 .env 文件中的 DATABASE_URL 是否正确")
        print("2. 确保 PostgreSQL 服务正在运行")
        print("3. 验证数据库用户名和密码")
        print("4. 确认数据库名称存在")
        return False

def main():
    """主函数"""
    print("🚀 BlogN2 数据库连接测试")
    print("=" * 50)
    
    # 检查环境变量
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL 环境变量未设置")
        print("💡 请检查 .env 文件是否存在并包含 DATABASE_URL")
        return False
    
    # 运行异步测试
    try:
        result = asyncio.run(test_database_connection())
        if result:
            print("\n🎉 数据库连接测试成功！")
        else:
            print("\n💥 数据库连接测试失败！")
        return result
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 