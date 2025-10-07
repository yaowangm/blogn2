#!/usr/bin/env python3
"""
恢复索引并重试优化脚本

用于从失败的优化中恢复，并重新执行优化。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_async_session
from sqlalchemy import text

async def restore_indexes():
    """恢复索引"""
    print("🔄 恢复索引...")
    
    try:
        async for session in get_async_session():
            # 检查备份文件
            backup_files = list(project_root.glob("scripts/index_backup_*.sql"))
            if not backup_files:
                print("❌ 未找到备份文件")
                return False
            
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            print(f"📁 使用备份文件: {latest_backup}")
            
            # 读取备份文件
            with open(latest_backup, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            
            # 提取CREATE INDEX语句
            lines = backup_content.split('\n')
            create_statements = []
            
            for line in lines:
                if line.strip().startswith('CREATE INDEX'):
                    create_statements.append(line.strip())
            
            print(f"📊 找到 {len(create_statements)} 个索引定义")
            
            # 恢复索引
            restored_count = 0
            for statement in create_statements:
                try:
                    await session.execute(text(statement))
                    await session.commit()
                    print(f"  ✅ 恢复索引: {statement.split()[2]}")
                    restored_count += 1
                except Exception as e:
                    print(f"  ⚠️  恢复失败: {e}")
                    await session.rollback()
            
            print(f"✅ 恢复了 {restored_count} 个索引")
            return True
            
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

async def main():
    """主函数"""
    print("🔄 索引恢复和重试脚本")
    print("=" * 40)
    
    # 恢复索引
    if await restore_indexes():
        print("\n✅ 索引恢复完成")
        print("🚀 现在可以重新运行优化脚本:")
        print("   python scripts/optimize_indexes_ivfflat_fixed.py")
    else:
        print("\n❌ 索引恢复失败")

if __name__ == "__main__":
    asyncio.run(main())
