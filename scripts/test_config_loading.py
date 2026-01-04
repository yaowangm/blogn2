#!/usr/bin/env python3
"""
配置加载手动测试脚本

用于快速验证不同场景下的配置加载行为
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.utils import (
    is_docker_container,
    load_config_file,
    get_config_file_path
)
from src.config.cache import validate_cache_config, cache_settings
from src.config.app import validate_app_config
from src.config.model import validate_model_config


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_scenario_1():
    """场景1: 使用 BLOGN_CONFIG_FILE 环境变量"""
    print_section("场景1: 使用 BLOGN_CONFIG_FILE 环境变量")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("CACHE_REDIS_HOST=test_host_from_file\n")
        f.write("CACHE_REDIS_PORT=6380\n")
        f.write("BASE_URL=http://test.example.com\n")
        config_file_path = f.name
    
    try:
        # 设置环境变量
        os.environ["BLOGN_CONFIG_FILE"] = config_file_path
        if "DOCKER_CONTAINER" in os.environ:
            del os.environ["DOCKER_CONTAINER"]
        
        # 重置全局变量
        from src.config import utils
        utils._config_file_path = None
        
        # 加载配置
        result = load_config_file()
        
        print(f"✅ 配置文件路径: {result}")
        print(f"✅ 配置文件存在: {Path(config_file_path).exists()}")
        print(f"✅ CACHE_REDIS_HOST: {os.getenv('CACHE_REDIS_HOST')}")
        print(f"✅ CACHE_REDIS_PORT: {os.getenv('CACHE_REDIS_PORT')}")
        
        # 验证配置
        config_path = get_config_file_path()
        print(f"✅ 获取的配置路径: {config_path}")
        
        if result:
            print("✅ 场景1测试通过")
        else:
            print("❌ 场景1测试失败")
            
    finally:
        # 清理
        if os.path.exists(config_file_path):
            os.unlink(config_file_path)
        if "BLOGN_CONFIG_FILE" in os.environ:
            del os.environ["BLOGN_CONFIG_FILE"]


def test_scenario_2():
    """场景2: 使用当前目录的 .env 文件"""
    print_section("场景2: 使用当前目录的 .env 文件")
    
    # 创建临时 .env 文件
    original_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        env_file = Path(tmpdir) / ".env"
        env_file.write_text("CACHE_REDIS_HOST=env_file_host\nCACHE_REDIS_PORT=6379\n")
        
        try:
            # 不设置 BLOGN_CONFIG_FILE
            if "BLOGN_CONFIG_FILE" in os.environ:
                del os.environ["BLOGN_CONFIG_FILE"]
            if "DOCKER_CONTAINER" in os.environ:
                del os.environ["DOCKER_CONTAINER"]
            
            # 重置全局变量
            from src.config import utils
            utils._config_file_path = None
            
            # 加载配置
            result = load_config_file()
            
            print(f"✅ 配置文件路径: {result}")
            print(f"✅ .env 文件存在: {env_file.exists()}")
            print(f"✅ CACHE_REDIS_HOST: {os.getenv('CACHE_REDIS_HOST')}")
            
            if result and ".env" in str(result):
                print("✅ 场景2测试通过")
            else:
                print("⚠️  场景2: 未找到 .env 文件（这是正常的，如果在项目根目录外运行）")
                
        finally:
            os.chdir(original_dir)


def test_scenario_3():
    """场景3: 使用默认配置"""
    print_section("场景3: 使用默认配置")
    
    # 不设置任何配置文件
    if "BLOGN_CONFIG_FILE" in os.environ:
        del os.environ["BLOGN_CONFIG_FILE"]
    if "DOCKER_CONTAINER" in os.environ:
        del os.environ["DOCKER_CONTAINER"]
    
    # 重置全局变量
    from src.config import utils
    utils._config_file_path = None
    
    # 加载配置
    result = load_config_file()
    
    print(f"✅ 配置文件路径: {result}")
    print(f"✅ 使用默认配置: {result is None}")
    
    # 验证默认配置
    cache_config = validate_cache_config()
    print(f"✅ Redis Host (默认): {cache_config.get('redis_host', 'N/A')}")
    print(f"✅ 配置来源: {cache_config.get('config_source', 'N/A')}")
    
    if result is None:
        print("✅ 场景3测试通过")
    else:
        print("⚠️  场景3: 找到了配置文件（可能是项目中的 .env 文件）")


def test_scenario_4():
    """场景4: Docker 容器环境"""
    print_section("场景4: Docker 容器环境")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("CACHE_REDIS_HOST=docker_host\n")
        config_file_path = f.name
    
    try:
        # 设置 Docker 环境
        os.environ["DOCKER_CONTAINER"] = "true"
        os.environ["BLOGN_CONFIG_FILE"] = config_file_path
        
        # 重置全局变量
        from src.config import utils
        utils._config_file_path = None
        
        # 检测 Docker 容器
        is_docker = is_docker_container()
        print(f"✅ 检测到 Docker 容器: {is_docker}")
        
        # 加载配置
        result = load_config_file()
        
        print(f"✅ 配置文件路径: {result}")
        print(f"✅ CACHE_REDIS_HOST: {os.getenv('CACHE_REDIS_HOST')}")
        
        if result:
            print("✅ 场景4测试通过")
        else:
            print("⚠️  场景4: 未加载配置文件")
            
    finally:
        # 清理
        if os.path.exists(config_file_path):
            os.unlink(config_file_path)
        if "BLOGN_CONFIG_FILE" in os.environ:
            del os.environ["BLOGN_CONFIG_FILE"]
        if "DOCKER_CONTAINER" in os.environ:
            del os.environ["DOCKER_CONTAINER"]


def test_scenario_5():
    """场景5: Docker 容器中未配置 BLOGN_CONFIG_FILE"""
    print_section("场景5: Docker 容器中未配置 BLOGN_CONFIG_FILE")
    
    # 设置 Docker 环境，但不设置配置文件
    os.environ["DOCKER_CONTAINER"] = "true"
    if "BLOGN_CONFIG_FILE" in os.environ:
        del os.environ["BLOGN_CONFIG_FILE"]
    
    # 重置全局变量
    from src.config import utils
    utils._config_file_path = None
    
    # 加载配置（应该显示警告）
    print("⚠️  预期: 应该显示警告信息")
    result = load_config_file()
    
    print(f"✅ 配置文件路径: {result}")
    print(f"✅ 使用默认配置: {result is None}")
    
    if result is None:
        print("✅ 场景5测试通过（使用默认配置）")
    else:
        print("⚠️  场景5: 意外加载了配置文件")
    
    # 清理
    if "DOCKER_CONTAINER" in os.environ:
        del os.environ["DOCKER_CONTAINER"]


def test_config_file_path():
    """测试获取配置文件路径"""
    print_section("测试: 获取配置文件路径")
    
    config_path = get_config_file_path()
    print(f"✅ 当前配置文件路径: {config_path}")
    
    if config_path:
        print(f"✅ 配置文件绝对路径: {config_path.resolve()}")
        print(f"✅ 配置文件存在: {config_path.exists()}")
    else:
        print("ℹ️  未使用配置文件（使用默认配置）")


def test_all_config_modules():
    """测试所有配置模块"""
    print_section("测试: 所有配置模块")
    
    print("\n📋 缓存配置:")
    cache_config = validate_cache_config()
    print(f"  - Redis Host: {cache_config.get('redis_host')}")
    print(f"  - Redis Port: {cache_config.get('redis_port')}")
    print(f"  - 配置来源: {cache_config.get('config_source')}")
    
    print("\n📋 应用配置:")
    app_config = validate_app_config()
    print(f"  - Base URL: {app_config.get('base_url')}")
    print(f"  - 配置来源: {app_config.get('config_source')}")
    
    print("\n📋 模型配置:")
    model_config = validate_model_config()
    print(f"  - Model Name: {model_config.get('model_name')}")
    print(f"  - 配置来源: {model_config.get('config_source')}")


def main():
    """主函数"""
    print("🚀 配置加载测试脚本")
    print("=" * 60)
    
    # 显示当前环境
    print("\n📌 当前环境信息:")
    print(f"  - 工作目录: {os.getcwd()}")
    print(f"  - 是否在 Docker 容器中: {is_docker_container()}")
    print(f"  - BLOGN_CONFIG_FILE: {os.getenv('BLOGN_CONFIG_FILE', '未设置')}")
    print(f"  - DOCKER_CONTAINER: {os.getenv('DOCKER_CONTAINER', '未设置')}")
    
    # 运行测试场景
    try:
        test_scenario_1()
        test_scenario_2()
        test_scenario_3()
        test_scenario_4()
        test_scenario_5()
        test_config_file_path()
        test_all_config_modules()
        
        print_section("测试完成")
        print("✅ 所有测试场景已执行")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
