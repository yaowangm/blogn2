#!/usr/bin/env python3
"""
测试运行脚本
提供便捷的测试运行命令
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
        print("  python tests/run_tests.py [命令]")
        print("\n可用命令:")
        print("  all          - 运行所有测试")
        print("  unit         - 运行单元测试")
        print("  integration  - 运行集成测试")
        print("  coverage     - 运行测试并生成覆盖率报告")
        print("  lint         - 运行代码检查")
        print("  clean        - 清理测试文件")
        return
    
    command = sys.argv[1]
    
    # 确保在项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if command == "all":
        success = run_command("pytest", "运行所有测试")
        
    elif command == "unit":
        success = run_command("pytest tests/unit/ -m unit", "运行单元测试")
        
    elif command == "integration":
        success = run_command("pytest tests/integration/ -m integration", "运行集成测试")
        
    elif command == "coverage":
        success = run_command("pytest --cov=src --cov-report=html --cov-report=term-missing", "运行测试并生成覆盖率报告")
        if success:
            print("\n📊 覆盖率报告已生成:")
            print("  - HTML报告: htmlcov/index.html")
            print("  - 控制台报告: 见上方输出")
        
    elif command == "lint":
        success = run_command("flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503", "运行代码检查")
        
    elif command == "clean":
        print("🧹 清理测试文件...")
        files_to_remove = [
            ".pytest_cache",
            "htmlcov",
            "coverage.xml",
            ".coverage",
            "test.db"
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                print(f"  ✅ 已删除: {file_path}")
            else:
                print(f"  ⏭️  跳过: {file_path} (不存在)")
        
        print("✅ 清理完成!")
        return
        
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