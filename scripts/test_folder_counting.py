#!/usr/bin/env python3
"""
测试文件夹计数逻辑的脚本
验证"全部文章"分类是否能正确统计所有文章
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import or_
from sqlmodel import select, func
from src.constants import ArticleStatus
from src.database import async_session
from src.repositories.project_item_repository import ProjectItemRepository
from src.models.project_item import ProjectItem
from src.models.folder import Folder


async def test_folder_counting():
    """测试文件夹计数逻辑"""
    async with async_session() as session:
        project_item_repo = ProjectItemRepository(session)
        
        # 测试项目ID（你可以修改为实际的项目ID）
        test_project_id = 1
        
        print(f"🔍 测试项目ID: {test_project_id}")
        print("=" * 50)
        
        # 1. 测试实时查询的总数
        print("📊 实时查询统计:")
        real_time_total = await project_item_repo.count_by_project_id_and_folder(test_project_id)
        print(f"   实时查询总数: {real_time_total}")
        
        # 2. 测试 folders.recordcount 汇总
        print("\n📊 folders.recordcount 汇总:")
        folders_query = select(Folder).where(Folder.projectid == test_project_id)
        folders_result = await session.exec(folders_query)
        folders = folders_result.all()
        cached_total = sum((f.recordcount or 0) for f in folders)
        print(f"   folders.recordcount 合计: {cached_total}")
        
        # 3. 详细分析
        print("\n📊 详细分析:")
        
        folder_count = 0
        for folder in folders:
            folder_count += folder.recordcount or 0
            print(f"   文件夹 '{folder.name}': {folder.recordcount or 0} 篇文章")
        
        print(f"   文件夹 recordcount 合计: {folder_count}")
        
        # 未分类：folderid 为 NULL 或 0
        unassigned_query = select(func.count(ProjectItem.id)).where(
            ProjectItem.projectid == test_project_id,
            or_(ProjectItem.folderid.is_(None), ProjectItem.folderid == 0),
            ProjectItem.status == 1,
            or_(
                ProjectItem.itemtype.is_(None),
                ProjectItem.itemtype != ArticleStatus.DELETED,
            ),
        )
        unassigned_result = await session.exec(unassigned_query)
        unassigned_count = unassigned_result.first() or 0
        print(f"   未分配文件夹文章: {unassigned_count}")
        
        # 4. 验证结果
        print("\n📊 验证结果:")
        expected_total = folder_count + unassigned_count
        print(f"   预期总数: {expected_total}")
        print(f"   预存储统计: {cached_total}")
        print(f"   实时查询: {real_time_total}")
        
        if cached_total == real_time_total:
            print("   ✅ 预存储统计与实时查询结果一致")
        else:
            print("   ❌ 预存储统计与实时查询结果不一致")
            print(f"   差异: {abs(cached_total - real_time_total)}")
        
        if cached_total == expected_total:
            print("   ✅ 预存储统计与预期结果一致")
        else:
            print("   ❌ 预存储统计与预期结果不一致")
            print(f"   差异: {abs(cached_total - expected_total)}")


if __name__ == "__main__":
    print("🧪 文件夹计数逻辑测试")
    print("⚠️  请确保数据库连接正常")
    print()
    
    try:
        asyncio.run(test_folder_counting())
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
