#!/usr/bin/env python3
"""
BlogN2 FastAPI 应用启动脚本
"""

import uvicorn
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("🚀 启动 BlogN2 FastAPI 应用...")
    print("📍 访问地址:")
    print("   - 首页: http://localhost:8000")
    print("   - 测试页面: http://localhost:8000/api/test")
    print("   - API文档: http://localhost:8000/docs")
    print("   - 健康检查: http://localhost:8000/health")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 