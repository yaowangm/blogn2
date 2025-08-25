#!/usr/bin/env python3
"""
修复数据库中所有表的id字段为自增长格式和主键
基于之前的聊天记录，将id字段改为BIGSERIAL PRIMARY KEY
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import async_engine
from sqlalchemy import text

async def get_all_tables():
    """获取数据库中所有表名"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            )
            tables = [row[0] for row in result.fetchall()]
            return tables
    except Exception as e:
        print(f"获取表列表失败: {e}")
        return []

async def fix_table_id_column(table_name):
    """修复表的id字段为BIGSERIAL PRIMARY KEY"""
    try:
        print(f"修复表 {table_name} 的id字段...")
        
        async with async_engine.begin() as conn:
            # 1. 删除现有主键约束
            print(f"   删除现有主键约束...")
            await conn.execute(
                text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {table_name}_pkey")
            )
            
            # 2. 删除默认值
            print(f"   删除默认值...")
            await conn.execute(
                text(f"ALTER TABLE {table_name} ALTER COLUMN id DROP DEFAULT")
            )
            
            # 3. 修改字段类型为BIGINT
            print(f"   修改字段类型为BIGINT...")
            await conn.execute(
                text(f"ALTER TABLE {table_name} ALTER COLUMN id TYPE BIGINT")
            )
            
            # 4. 设置NOT NULL
            print(f"   设置NOT NULL...")
            await conn.execute(
                text(f"ALTER TABLE {table_name} ALTER COLUMN id SET NOT NULL")
            )
            
            # 5. 创建序列
            sequence_name = f"{table_name}_id_seq"
            print(f"   创建序列 {sequence_name}...")
            await conn.execute(
                text(f"CREATE SEQUENCE IF NOT EXISTS {sequence_name}")
            )
            
            # 6. 设置序列起始值
            print(f"   设置序列起始值...")
            result = await conn.execute(
                text(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table_name}")
            )
            max_id = result.fetchone()[0]
            await conn.execute(
                text(f"SELECT setval('{sequence_name}', {max_id}, false)")
            )
            
            # 7. 设置默认值为序列
            print(f"   设置默认值为序列...")
            await conn.execute(
                text(f"ALTER TABLE {table_name} ALTER COLUMN id SET DEFAULT nextval('{sequence_name}')")
            )
            
            # 8. 设置序列所有者
            await conn.execute(
                text(f"ALTER SEQUENCE {sequence_name} OWNED BY {table_name}.id")
            )
            
            # 9. 添加主键约束
            print(f"   添加主键约束...")
            await conn.execute(
                text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (id)")
            )
            
            print(f"   {table_name} 的id字段修复完成！")
            return True
            
    except Exception as e:
        print(f"   修复 {table_name} 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("BlogN2 数据库ID字段修复工具")
    print("=" * 60)
    print("警告：此脚本将修改数据库结构，请确保已备份数据库！")
    print("=" * 60)
    
    tables = await get_all_tables()
    if not tables:
        print("没有找到任何表")
        return False
    
    print(f"找到 {len(tables)} 个表:")
    for table in tables:
        print(f"   - {table}")
    
    print("\n" + "=" * 60)
    confirm = input("确认要修复所有表的id字段吗？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("操作已取消")
        return False
    
    print("\n开始修复...")
    
    success_count = 0
    total_count = len(tables)
    
    for table_name in tables:
        success = await fix_table_id_column(table_name)
        if success:
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"修复完成！总计: {total_count}, 成功: {success_count}, 失败: {total_count - success_count}")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
