#!/usr/bin/env python3
"""
测试运行脚本

提供统一的测试运行接口，支持不同类型的测试和覆盖率报告。
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: str, description: str) -> bool:
    """
    运行命令并返回执行结果
    
    Args:
        command: 要执行的命令
        description: 命令描述
        
    Returns:
        bool: 命令是否执行成功
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"🚀 {description}")
    logger.info(f"{'='*50}")
    logger.info(f"执行命令: {command}")
    logger.info("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        logger.info("✅ 命令执行成功!")
        
        if result.stdout.strip():
            logger.info("输出:")
            logger.info(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error("❌ 命令执行失败!")
        logger.error(f"错误代码: {e.returncode}")
        
        if e.stdout.strip():
            logger.error("标准输出:")
            logger.error(e.stdout)
        
        if e.stderr.strip():
            logger.error("错误输出:")
            logger.error(e.stderr)
        
        return False


def show_usage():
    """显示使用说明"""
    logger.info("使用方法:")
    logger.info("  python tests/run_tests.py [命令]")
    logger.info("\n可用命令:")
    logger.info("  all          - 运行所有测试")
    logger.info("  unit         - 运行单元测试")
    logger.info("  integration  - 运行集成测试")
    logger.info("  basic        - 运行基础端点测试（快速验证）")
    logger.info("  coverage     - 运行测试并生成覆盖率报告")
    logger.info("  lint         - 运行代码检查")
    logger.info("  clean        - 清理测试文件")


def run_coverage_tests():
    """运行覆盖率测试"""
    logger.info("📊 运行覆盖率测试...")
    
    # 运行测试并生成覆盖率报告
    success = run_command(
        "python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing",
        "覆盖率测试"
    )
    
    if success:
        logger.info("\n📊 覆盖率报告已生成:")
        logger.info("  - HTML报告: htmlcov/index.html")
        logger.info("  - 控制台报告: 见上方输出")
    
    return success


def clean_test_files():
    """清理测试生成的文件"""
    logger.info("🧹 清理测试文件...")
    
    # 要清理的文件和目录
    files_to_clean = [
        ".coverage",
        "coverage.xml",
        "htmlcov/",
        ".pytest_cache/",
        "__pycache__/",
        "*.pyc",
        "*.pyo"
    ]
    
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
                logger.info(f"  ✅ 已删除目录: {file_path}")
            else:
                os.remove(file_path)
                logger.info(f"  ✅ 已删除: {file_path}")
        else:
            logger.info(f"  ⏭️  跳过: {file_path} (不存在)")
    
    logger.info("✅ 清理完成!")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "all":
        success = run_command("python -m pytest tests/", "所有测试")
    elif command == "unit":
        success = run_command("python -m pytest tests/unit/", "单元测试")
    elif command == "integration":
        success = run_command("python -m pytest tests/integration/", "集成测试")
    elif command == "basic":
        success = run_command("python -m pytest tests/integration/test_basic_endpoints.py -v", "基础端点测试")
    elif command == "coverage":
        success = run_coverage_tests()
    elif command == "lint":
        success = run_command("python -m flake8 src/ tests/", "代码检查")
    elif command == "clean":
        clean_test_files()
        success = True
    else:
        logger.error(f"❌ 未知命令: {command}")
        show_usage()
        return
    
    if success:
        logger.info("\n🎉 所有操作完成!")
    else:
        logger.error("\n💥 操作失败!")
        sys.exit(1)


if __name__ == "__main__":
    main() 