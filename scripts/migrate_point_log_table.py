#!/usr/bin/env python3
"""
积分记录表迁移脚本
用于创建point_logs表，实现每日积分限制功能
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

async def migrate_point_log_table():
    """执行积分记录表迁移"""
    try:
        print("🚀 开始创建积分记录表...")
        
        # 读取SQL文件
        sql_file = project_root / "scripts" / "create_point_log_table.sql"
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 执行SQL
        async with async_engine.begin() as conn:
            # 分割SQL语句并逐个执行
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"📝 执行语句 {i}/{len(statements)}...")
                    await conn.execute(text(statement))
            
            print("✅ 积分记录表创建成功！")
            
            # 验证表是否创建成功
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'point_logs' 
                AND table_schema = 'public'
            """))
            
            if result.fetchone():
                print("✅ 验证成功：point_logs表已创建")
            else:
                print("❌ 验证失败：point_logs表未找到")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔧 BlogN2 积分记录表迁移工具")
    print("=" * 50)
    
    # 运行异步迁移
    try:
        result = asyncio.run(migrate_point_log_table())
        if result:
            print("\n🎉 迁移完成！")
            print("📋 积分记录表功能说明：")
            print("   - 用户每发表一篇文章可获得10积分")
            print("   - 每日最多只能获得10积分")
            print("   - 超过限制时不会获得积分，但文章仍可正常发表")
        else:
            print("\n💥 迁移失败！")
        return result
    except KeyboardInterrupt:
        print("\n⏹️  迁移被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 迁移过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
