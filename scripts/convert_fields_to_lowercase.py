#!/usr/bin/env python3
"""
将数据库字段名转换为小写脚本
用于将所有表的字段名改为小写
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置数据库URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://wy:passw0rd@localhost:5432/blogn"

from src.database import async_engine
from sqlalchemy import text

async def convert_fields_to_lowercase():
    """将所有字段名转换为小写"""
    try:
        print("🔄 开始将字段名转换为小写...")
        
        async with async_engine.begin() as conn:
            # 获取所有表名
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            )
            tables = result.fetchall()
            
            print(f"📋 找到 {len(tables)} 个表")
            
            for table in tables:
                table_name = table[0]
                print(f"\n📊 处理表: {table_name}")
                
                # 获取表的字段信息
                result = await conn.execute(
                    text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                    """)
                )
                columns = result.fetchall()
                
                # 找出需要重命名的字段
                fields_to_rename = []
                for col in columns:
                    col_name = col[0]
                    if any(c.isupper() for c in col_name):
                        new_name = col_name.lower()
                        if new_name != col_name:
                            fields_to_rename.append((col_name, new_name))
                
                if fields_to_rename:
                    print(f"  🔄 需要重命名的字段: {len(fields_to_rename)} 个")
                    for old_name, new_name in fields_to_rename:
                        print(f"    - {old_name} → {new_name}")
                        
                        # 重命名字段
                        try:
                            await conn.execute(
                                text(f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}"')
                            )
                            print(f"      ✅ 成功重命名: {old_name} → {new_name}")
                        except Exception as e:
                            print(f"      ❌ 重命名失败: {old_name} → {new_name}, 错误: {e}")
                else:
                    print(f"  ✅ 所有字段名已经是小写")
        
        print("\n🎉 字段名转换完成！")
        return True
        
    except Exception as e:
        print(f"❌ 字段名转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 BlogN2 数据库字段名转换工具")
    print("=" * 50)
    print("⚠️  警告: 此操作将修改数据库表结构，请确保已备份数据库！")
    print("=" * 50)
    
    # 确认操作
    confirm = input("确认要继续吗？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False
    
    # 运行异步转换
    try:
        result = asyncio.run(convert_fields_to_lowercase())
        if result:
            print("\n🎉 字段名转换成功！")
        else:
            print("\n💥 字段名转换失败！")
        return result
    except KeyboardInterrupt:
        print("\n⏹️  转换被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 转换过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 