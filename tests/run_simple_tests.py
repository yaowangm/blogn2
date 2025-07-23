#!/usr/bin/env python3
"""
简化测试运行脚本
不包含覆盖率报告，用于快速验证测试
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"🚀 {description}")
    print(f"{'='*50}")
    print(f"执行命令: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ 命令执行成功!")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 命令执行失败!")
        print(f"错误代码: {e.returncode}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python tests/run_simple_tests.py [命令]")
        print("\n可用命令:")
        print("  all          - 运行所有测试（无覆盖率）")
        print("  unit         - 运行单元测试（无覆盖率）")
        print("  integration  - 运行集成测试（无覆盖率）")
        return
    
    command = sys.argv[1]
    
    # 确保在项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if command == "all":
        success = run_command("python -m pytest --no-cov", "运行所有测试（无覆盖率）")
        
    elif command == "unit":
        success = run_command("python -m pytest tests/unit/ -m unit --no-cov", "运行单元测试（无覆盖率）")
        
    elif command == "integration":
        success = run_command("python -m pytest tests/integration/ -m integration --no-cov", "运行集成测试（无覆盖率）")
        
    else:
        print(f"❌ 未知命令: {command}")
        return
    
    if success:
        print("\n🎉 所有操作完成!")
    else:
        print("\n💥 操作失败!")
        sys.exit(1)

if __name__ == "__main__":
    main() 