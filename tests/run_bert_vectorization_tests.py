#!/usr/bin/env python3
"""
BERT向量化测试运行脚本

统一运行所有BERT向量化相关的测试，包括：
- 单元测试
- 集成测试
- 性能测试

使用方法:
    python tests/run_bert_vectorization_tests.py
    python tests/run_bert_vectorization_tests.py --unit
    python tests/run_bert_vectorization_tests.py --integration
    python tests/run_bert_vectorization_tests.py --performance
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 测试通过")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 测试失败")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="运行BERT向量化测试")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--performance", action="store_true", help="只运行性能测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 基础pytest命令
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    else:
        base_cmd.append("-q")
    
    if args.coverage:
        base_cmd.extend(["--cov=src.services", "--cov-report=html", "--cov-report=term"])
    
    # 测试结果统计
    test_results = {}
    
    print("🚀 开始运行BERT向量化测试")
    print(f"项目根目录: {project_root}")
    
    # 运行单元测试
    if not args.integration and not args.performance:
        unit_cmd = base_cmd + [
            "tests/unit/test_bert_vectorization_services.py",
            "--tb=short"
        ]
        
        success = run_command(unit_cmd, "BERT向量化服务单元测试")
        test_results["单元测试"] = success
    
    # 运行集成测试
    if not args.unit and not args.performance:
        integration_cmd = base_cmd + [
            "tests/integration/test_bert_vectorization_with_real_db.py",
            "--tb=short"
        ]
        
        success = run_command(integration_cmd, "BERT向量化集成测试")
        test_results["集成测试"] = success
    
    # 运行性能测试
    if not args.unit and not args.integration:
        performance_cmd = base_cmd + [
            "tests/performance/test_bert_vectorization_performance.py",
            "--tb=short",
            "-s"  # 显示print输出
        ]
        
        success = run_command(performance_cmd, "BERT向量化性能测试")
        test_results["性能测试"] = success
    
    # 运行所有测试
    if not args.unit and not args.integration and not args.performance:
        all_tests = [
            "tests/unit/test_bert_vectorization_services.py",
            "tests/integration/test_bert_vectorization_with_real_db.py",
            "tests/performance/test_bert_vectorization_performance.py"
        ]
        
        for test_file in all_tests:
            test_name = Path(test_file).stem.replace("test_", "").replace("_", " ").title()
            cmd = base_cmd + [test_file, "--tb=short"]
            
            success = run_command(cmd, f"BERT向量化{test_name}")
            test_results[test_name] = success
    
    # 显示测试结果总结
    print(f"\n{'='*60}")
    print("测试结果总结")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for success in test_results.values() if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in test_results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {total_tests} 个测试")
    print(f"通过: {passed_tests} 个")
    print(f"失败: {failed_tests} 个")
    
    if args.coverage:
        print(f"\n📊 覆盖率报告已生成: htmlcov/index.html")
    
    # 返回适当的退出码
    if failed_tests > 0:
        print(f"\n❌ 有 {failed_tests} 个测试失败")
        sys.exit(1)
    else:
        print(f"\n🎉 所有测试通过！")
        sys.exit(0)

if __name__ == "__main__":
    main()
