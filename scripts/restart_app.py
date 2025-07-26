#!/usr/bin/env python3
"""
重启应用脚本
用于重启BlogN2应用，确保使用正确的数据库配置
"""

import os
import sys
import subprocess
import signal
import time

def stop_app():
    """停止当前运行的应用"""
    print("🛑 停止当前应用...")
    
    # 查找并停止uvicorn进程
    try:
        result = subprocess.run(
            ["pkill", "-f", "uvicorn"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ 应用已停止")
        else:
            print("ℹ️  没有找到运行中的应用")
    except Exception as e:
        print(f"⚠️  停止应用时出错: {e}")

def start_app():
    """启动应用"""
    print("🚀 启动应用...")
    
    # 设置环境变量
    # 使用环境变量中的DATABASE_URL
    
    try:
        # 启动应用
        subprocess.Popen([
            sys.executable, "run.py"
        ], env=os.environ)
        
        print("✅ 应用已启动")
        print("📍 访问地址: http://localhost:8000")
        print("⏳ 等待应用完全启动...")
        
        # 等待应用启动
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ 启动应用失败: {e}")

def main():
    """主函数"""
    print("🔄 BlogN2 应用重启工具")
    print("=" * 50)
    
    # 停止应用
    stop_app()
    
    # 等待一下
    time.sleep(2)
    
    # 启动应用
    start_app()
    
    print("\n🎉 应用重启完成！")
    print("💡 如果首页仍然显示静态数据，请检查数据库连接和配置")

if __name__ == "__main__":
    main() 