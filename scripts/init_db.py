#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建新的数据库表
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import create_db_and_tables

def main():
    """主函数"""
    print("开始创建数据库表...")
    try:
        create_db_and_tables()
        print("✅ 数据库表创建完成！")
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 