#!/usr/bin/env python3
"""
测试运行脚本
"""

import subprocess
import sys
import os

def run_tests(test_type="all"):
    """运行测试"""
    if test_type == "unit":
        cmd = ["pytest", "tests/", "-m", "unit", "-v"]
    elif test_type == "integration":
        cmd = ["pytest", "tests/", "-m", "integration", "-v"]
    elif test_type == "controllers":
        cmd = ["pytest", "tests/test_controllers.py", "-v"]
    elif test_type == "services":
        cmd = ["pytest", "tests/test_services.py", "-v"]
    elif test_type == "repositories":
        cmd = ["pytest", "tests/test_repositories.py", "-v"]
    else:
        cmd = ["pytest", "tests/", "-v"]
    
    print(f"运行测试: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def run_coverage():
    """运行覆盖率测试"""
    cmd = [
        "pytest", 
        "tests/", 
        "--cov=src", 
        "--cov-report=html", 
        "--cov-report=term-missing",
        "-v"
    ]
    print(f"运行覆盖率测试: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    if test_type == "coverage":
        exit_code = run_coverage()
    else:
        exit_code = run_tests(test_type)
    
    sys.exit(exit_code) 