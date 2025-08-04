#!/usr/bin/env python3
"""
缓存配置测试脚本
用于验证缓存配置是否正确加载
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.cache import cache_settings, validate_cache_config, get_redis_url


def test_cache_config():
    """测试缓存配置"""
    print("🔍 测试缓存配置...")
    print("=" * 50)
    
    # 验证配置
    config_info = validate_cache_config()
    
    print("📋 当前配置信息:")
    for key, value in config_info.items():
        print(f"  {key}: {value}")
    
    print("\n🔗 Redis连接URL:")
    redis_url = get_redis_url()
    print(f"  {redis_url}")
    
    print("\n✅ 配置验证完成")
    
    # 检查.env文件是否存在
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env文件存在: {env_file.absolute()}")
    else:
        print(f"⚠️  .env文件不存在，将使用默认配置")
        print(f"   建议复制 env.example 到 .env 并配置参数")
    
    return config_info


if __name__ == "__main__":
    test_cache_config() 