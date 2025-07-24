#!/usr/bin/env python3
"""
清理测试数据脚本 - 修复版本
用于清理数据库中可能残留的测试数据
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置数据库URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://wy:passw0rd@localhost:5432/blogn"

from src.database import async_engine, async_session
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.post import Post
from sqlmodel import select, delete

async def cleanup_test_data():
    """清理测试数据"""
    try:
        print("🧹 开始清理测试数据...")
        
        async with async_session() as session:
            # 创建测试时间戳
            test_timestamp = datetime(2024, 1, 1, 10, 0, 0)
            
            # 清理测试用户（按时间戳）
            print("📝 清理测试用户...")
            result = await session.exec(
                select(User).where(User.regtime == test_timestamp)
            )
            test_users = result.all()
            
            for user in test_users:
                print(f"  - 删除用户: {user.name} (ID: {user.id}, 注册时间: {user.regtime})")
                await session.delete(user)
            
            # 清理测试项目（按时间戳）
            print("📝 清理测试项目...")
            result = await session.exec(
                select(Project).where(Project.createtime == test_timestamp)
            )
            test_projects = result.all()
            
            for project in test_projects:
                print(f"  - 删除项目: {project.name} (ID: {project.id}, 创建时间: {project.createtime})")
                await session.delete(project)
            
            # 清理测试项目项（按时间戳）
            print("📝 清理测试项目项...")
            result = await session.exec(
                select(ProjectItem).where(ProjectItem.createtime == test_timestamp)
            )
            test_items = result.all()
            
            for item in test_items:
                print(f"  - 删除项目项: {item.name} (ID: {item.id}, 创建时间: {item.createtime})")
                await session.delete(item)
            
            # 清理测试帖子（按时间戳）
            print("📝 清理测试帖子...")
            result = await session.exec(
                select(Post).where(Post.posttime == test_timestamp)
            )
            test_posts = result.all()
            
            for post in test_posts:
                print(f"  - 删除帖子: {post.subject} (ID: {post.id}, 发布时间: {post.posttime})")
                await session.delete(post)
            
            # 提交更改
            await session.commit()
            
            print(f"✅ 清理完成！")
            print(f"  - 删除了 {len(test_users)} 个测试用户")
            print(f"  - 删除了 {len(test_projects)} 个测试项目")
            print(f"  - 删除了 {len(test_items)} 个测试项目项")
            print(f"  - 删除了 {len(test_posts)} 个测试帖子")
            
            return True
            
    except Exception as e:
        print(f"❌ 清理测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 BlogN2 测试数据清理工具 - 修复版本")
    print("=" * 50)
    
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 