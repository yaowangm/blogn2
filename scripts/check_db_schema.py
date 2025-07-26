#!/usr/bin/env python3
"""
检查数据库表结构脚本
用于查看当前数据库的表和字段信息
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置数据库URL
# 使用环境变量中的DATABASE_URL

from src.database import async_engine
from sqlalchemy import text

async def check_schema():
    """检查数据库表结构"""
    try:
        print("🔍 检查数据库表结构...")
        
        async with async_engine.begin() as conn:
            # 获取所有表名
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            )
            tables = result.fetchall()
            
            print(f"📋 找到 {len(tables)} 个表:")
            
            for table in tables:
                table_name = table[0]
                print(f"\n📊 表: {table_name}")
                
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
                
                print(f"  字段列表:")
                for col in columns:
                    col_name, data_type, is_nullable, col_default = col
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    default = f" DEFAULT {col_default}" if col_default else ""
                    print(f"    - {col_name}: {data_type} {nullable}{default}")
                    
                    # 检查字段名是否包含大写字母
                    if any(c.isupper() for c in col_name):
                        print(f"      ⚠️  字段名包含大写字母: {col_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 BlogN2 数据库表结构检查工具")
    print("=" * 50)
    
    # 运行异步检查
    try:
        result = asyncio.run(check_schema())
        if result:
            print("\n🎉 表结构检查完成！")
        else:
            print("\n💥 表结构检查失败！")
        return result
    except KeyboardInterrupt:
        print("\n⏹️  检查被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 检查过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 