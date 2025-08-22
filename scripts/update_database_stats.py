#!/usr/bin/env python3
"""
数据库统计信息更新脚本

功能：
1. 更新folders表的postcount和recordcount字段
2. 在project表中增加commentcount字段（如果不存在）
3. 更新project表的commentcount字段

注意：此脚本不会自动执行，需要手动审查后运行
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import select, func, text
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database import async_session
from src.models.folder import Folder
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.post import Post


class DatabaseStatsUpdater:
    """数据库统计信息更新器"""
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = async_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def check_and_add_commentcount_column(self) -> bool:
        """
        检查并添加project表的commentcount字段
        
        Returns:
            bool: 是否成功添加字段
        """
        try:
            # 检查commentcount字段是否存在
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'project' 
                AND column_name = 'commentcount'
            """)
            
            result = await self.session.exec(check_query)
            column_exists = result.first() is not None
            
            if not column_exists:
                print("📝 在project表中添加commentcount字段...")
                
                # 添加commentcount字段
                add_column_query = text("""
                    ALTER TABLE project 
                    ADD COLUMN commentcount INTEGER DEFAULT 0
                """)
                
                await self.session.exec(add_column_query)
                await self.session.commit()
                print("✅ commentcount字段添加成功")
                return True
            else:
                print("ℹ️  commentcount字段已存在")
                return False
                
        except Exception as e:
            print(f"❌ 添加commentcount字段失败: {e}")
            await self.session.rollback()
            return False
    
    async def update_folders_stats(self) -> Dict[str, int]:
        """
        更新folders表的postcount和recordcount字段
        
        Returns:
            Dict[str, int]: 更新统计信息
        """
        try:
            print("🔄 开始更新folders表统计信息...")
            
            # 获取所有文件夹
            folders_query = select(Folder)
            folders_result = await self.session.exec(folders_query)
            folders = folders_result.all()
            
            updated_count = 0
            total_folders = len(folders)
            
            for folder in folders:
                # 统计该文件夹下的文章数量（projectitem表）
                post_count_query = select(func.count(ProjectItem.id)).where(
                    ProjectItem.folderid == folder.id,
                    ProjectItem.status == 1  # 只统计正常状态的文章
                )
                post_count_result = await self.session.exec(post_count_query)
                post_count = post_count_result.first() or 0
                
                # 统计该文件夹下的评论数量（post表，排除留言本）
                comment_count_query = select(func.count(Post.id)).where(
                    Post.folderid == folder.id,
                    Post.projectitemid > 0  # 排除留言本
                )
                comment_count_result = await self.session.exec(comment_count_query)
                comment_count = comment_count_result.first() or 0
                
                # 更新文件夹统计信息
                folder.postcount = post_count
                folder.recordcount = post_count  # recordcount和postcount保持一致
                
                updated_count += 1
                if updated_count % 10 == 0:  # 每更新10个显示进度
                    print(f"   �� 已更新 {updated_count}/{total_folders} 个文件夹...")
            
            # 提交更改
            await self.session.commit()
            print(f"✅ folders表统计信息更新完成，共更新 {updated_count} 个文件夹")
            
            return {
                "total_folders": total_folders,
                "updated_folders": updated_count
            }
            
        except Exception as e:
            print(f"❌ 更新folders表统计信息失败: {e}")
            await self.session.rollback()
            return {"error": str(e)}
    
    async def update_projects_commentcount(self) -> Dict[str, int]:
        """
        更新project表的commentcount字段
        
        Returns:
            Dict[str, int]: 更新统计信息
        """
        try:
            print("�� 开始更新project表评论数量统计...")
            
            # 获取所有项目
            projects_query = select(Project)
            projects_result = await self.session.exec(projects_query)
            projects = projects_result.all()
            
            updated_count = 0
            total_projects = len(projects)
            
            for project in projects:
                # 统计该项目的所有评论数量
                # 通过projectitem表关联到post表，统计所有评论
                comment_count_query = select(func.count(Post.id)).join(
                    ProjectItem, Post.projectitemid == ProjectItem.id
                ).where(
                    ProjectItem.projectid == project.id,
                    Post.projectitemid > 0,  # 排除留言本
                    Post.status == 1  # 只统计正常状态的评论
                )
                
                comment_count_result = await self.session.exec(comment_count_query)
                comment_count = comment_count_result.first() or 0
                
                # 更新项目评论数量
                project.commentcount = comment_count
                
                updated_count += 1
                if updated_count % 10 == 0:  # 每更新10个显示进度
                    print(f"   �� 已更新 {updated_count}/{total_projects} 个项目...")
            
            # 提交更改
            await self.session.commit()
            print(f"✅ project表评论数量统计更新完成，共更新 {updated_count} 个项目")
            
            return {
                "total_projects": total_projects,
                "updated_projects": updated_count
            }
            
        except Exception as e:
            print(f"❌ 更新project表评论数量统计失败: {e}")
            await self.session.rollback()
            return {"error": str(e)}
    
    async def verify_updates(self) -> Dict[str, Any]:
        """
        验证更新结果
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            print("🔍 开始验证更新结果...")
            
            # 验证folders表
            folders_with_stats = select(Folder).where(Folder.recordcount > 0)
            folders_result = await self.session.exec(folders_with_stats)
            folders_with_stats_count = len(folders_result.all())
            
            # 验证project表
            projects_with_comments = select(Project).where(Project.commentcount > 0)
            projects_result = await self.session.exec(projects_with_comments)
            projects_with_comments_count = len(projects_result.all())
            
            # 获取总体统计
            total_folders = await self.session.exec(select(func.count(Folder.id)))
            total_projects = await self.session.exec(select(func.count(Project.id)))
            
            verification_result = {
                "folders": {
                    "total": total_folders.first() or 0,
                    "with_stats": folders_with_stats_count
                },
                "projects": {
                    "total": total_projects.first() or 0,
                    "with_comments": projects_with_comments_count
                }
            }
            
            print("✅ 验证完成")
            return verification_result
            
        except Exception as e:
            print(f"❌ 验证更新结果失败: {e}")
            return {"error": str(e)}
    
    async def run_full_update(self) -> Dict[str, Any]:
        """
        执行完整的数据库更新流程
        
        Returns:
            Dict[str, Any]: 更新结果摘要
        """
        print("🚀 开始执行数据库统计信息更新...")
        print("=" * 60)
        
        results = {}
        
        try:
            # 1. 检查并添加commentcount字段
            print("\n📋 步骤1: 检查project表结构...")
            commentcount_added = await self.check_and_add_commentcount_column()
            results["commentcount_added"] = commentcount_added
            
            # 2. 更新folders表统计信息
            print("\n📋 步骤2: 更新folders表统计信息...")
            folders_result = await self.update_folders_stats()
            results["folders_update"] = folders_result
            
            # 3. 更新project表评论数量统计
            print("\n📋 步骤3: 更新project表评论数量统计...")
            projects_result = await self.update_projects_commentcount()
            results["projects_update"] = projects_result
            
            # 4. 验证更新结果
            print("\n📋 步骤4: 验证更新结果...")
            verification_result = await self.verify_updates()
            results["verification"] = verification_result
            
            print("\n" + "=" * 60)
            print("🎉 数据库统计信息更新完成！")
            
            return results
            
        except Exception as e:
            print(f"\n❌ 更新过程中发生错误: {e}")
            results["error"] = str(e)
            return results


async def main():
    """主函数"""
    print("🔧 数据库统计信息更新脚本")
    print("⚠️  请仔细审查代码后再执行此脚本！")
    print("=" * 60)
    
    # 显示执行计划
    print("📋 执行计划:")
    print("1. 检查并添加project表的commentcount字段")
    print("2. 更新folders表的postcount和recordcount字段")
    print("3. 更新project表的commentcount字段")
    print("4. 验证更新结果")
    print()
    
    # 确认执行
    confirm = input("确认执行更新操作？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    # 执行更新
    async with DatabaseStatsUpdater() as updater:
        results = await updater.run_full_update()
        
        # 显示结果摘要
        print("\n📊 更新结果摘要:")
        print(f"Folders表更新: {results.get('folders_update', 'N/A')}")
        print(f"Projects表更新: {results.get('projects_update', 'N/A')}")
        print(f"验证结果: {results.get('verification', 'N/A')}")
        
        if "error" in results:
            print(f"❌ 错误信息: {results['error']}")


if __name__ == "__main__":
    # 注意：此脚本不会自动执行，需要手动审查后运行
    print("⚠️  重要提醒：")
    print("1. 请仔细审查此脚本的代码逻辑")
    print("2. 确保在测试环境中先运行")
    print("3. 备份数据库后再在生产环境中执行")
    print("4. 手动运行: python scripts/update_database_stats.py")
    print()
    
    # 如果要执行，取消下面的注释
    asyncio.run(main())
