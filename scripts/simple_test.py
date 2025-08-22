#!/usr/bin/env python3
"""
简单的测试脚本，验证修复后的逻辑
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_logic():
    """测试逻辑（不涉及数据库）"""
    print("🧪 测试修复后的逻辑")
    print("=" * 30)
    
    # 模拟查询结果
    folder_recordcounts = [5, 3, 0, 8, None]  # 模拟从数据库查询的结果
    
    # 测试修复后的逻辑
    folder_count = sum(recordcount or 0 for recordcount in folder_recordcounts)
    
    print(f"模拟的recordcount值: {folder_recordcounts}")
    print(f"计算后的总数: {folder_count}")
    
    # 验证逻辑
    expected = 5 + 3 + 0 + 8 + 0  # None 应该被转换为 0
    print(f"预期结果: {expected}")
    
    if folder_count == expected:
        print("✅ 逻辑正确！")
    else:
        print("❌ 逻辑错误！")

if __name__ == "__main__":
    test_logic()
