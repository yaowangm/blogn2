#!/usr/bin/env python3
"""
清理测试数据脚本
用于清理数据库中可能残留的测试数据
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.database import async_engine, async_session
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem
from sqlmodel import select, delete

# 加载环境变量
load_dotenv()

async def cleanup_test_data():
    """清理测试数据"""
    try:
        print("🧹 开始清理测试数据...")
        
        async with async_session() as session:
            # 清理测试用户
            print("📝 清理测试用户...")
            result = await session.exec(
                select(User).where(User.name.like("testuser%"))
            )
            test_users = result.all()
            
            for user in test_users:
                print(f"  - 删除用户: {user.name} (ID: {user.id})")
                await session.delete(user)
            
            # 清理测试项目
            print("📝 清理测试项目...")
            result = await session.exec(
                select(Project).where(Project.name.like("Test%"))
            )
            test_projects = result.all()
            
            for project in test_projects:
                print(f"  - 删除项目: {project.name} (ID: {project.id})")
                await session.delete(project)
            
            # 清理测试项目项
            print("📝 清理测试项目项...")
            result = await session.exec(
                select(ProjectItem).where(ProjectItem.name.like("Test%"))
            )
            test_items = result.all()
            
            for item in test_items:
                print(f"  - 删除项目项: {item.name} (ID: {item.id})")
                await session.delete(item)
            
            # 提交更改
            await session.commit()
            
            print(f"✅ 清理完成！")
            print(f"  - 删除了 {len(test_users)} 个测试用户")
            print(f"  - 删除了 {len(test_projects)} 个测试项目")
            print(f"  - 删除了 {len(test_items)} 个测试项目项")
            
            return True
            
    except Exception as e:
        print(f"❌ 清理测试数据失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 BlogN2 测试数据清理工具")
    print("=" * 50)
    
    # 检查环境变量
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL 环境变量未设置")
        print("💡 请检查 .env 文件是否存在并包含 DATABASE_URL")
        return False
    
    # 运行异步清理
    try:
        result = asyncio.run(cleanup_test_data())
        if result:
            print("\n🎉 测试数据清理成功！")
        else:
            print("\n💥 测试数据清理失败！")
        return result
    except KeyboardInterrupt:
        print("\n⏹️  清理被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 清理过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 