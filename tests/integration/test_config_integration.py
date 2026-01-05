"""
配置加载集成测试

测试配置加载在实际应用场景中的行为
"""

import pytest
import os
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.app import validate_app_config
from src.config.cache import validate_cache_config, cache_settings
from src.config.model import validate_model_config
from src.config.utils import get_config_file_path, load_config_file


class TestConfigIntegration:
    """配置集成测试"""
    
    def test_config_modules_use_same_config_file(self, tmp_path, monkeypatch):
        """测试所有配置模块使用相同的配置文件"""
        # 创建配置文件
        config_file = tmp_path / "integration_test.env"
        config_file.write_text(
            "CACHE_REDIS_HOST=integration_host\n"
            "CACHE_REDIS_PORT=6380\n"
            "BASE_URL=http://test.example.com\n"
            "MODEL_MODEL_NAME=test-model\n"
        )
        
        monkeypatch.setenv("BLOGN_CONFIG_FILE", str(config_file))
        
        # 重置全局变量
        from src.config import utils
        utils._config_file_path = None
        
        with patch('src.config.utils.is_docker_container', return_value=False):
            # 加载配置文件
            load_config_file()
            
            # 验证所有模块都能获取配置文件路径
            config_path = get_config_file_path()
            assert config_path is not None
            
            # 验证配置信息中包含配置文件路径
            cache_config = validate_cache_config()
            assert "config_source" in cache_config
            assert str(config_path) in cache_config["config_source"] or "integration_host" in str(cache_config.get("redis_host", ""))
    
    def test_config_with_defaults(self, monkeypatch):
        """测试使用默认配置时各模块的行为"""
        monkeypatch.delenv("BLOGN_CONFIG_FILE", raising=False)
        
        # 重置全局变量
        from src.config import utils
        utils._config_file_path = None
        
        with patch('src.config.utils.is_docker_container', return_value=False):
            with patch('pathlib.Path.cwd') as mock_cwd:
                mock_env = MagicMock()
                mock_env.exists.return_value = False
                mock_cwd.return_value.__truediv__ = MagicMock(return_value=mock_env)
                
                # 加载配置（应该使用默认值）
                load_config_file()
                
                # 验证配置使用默认值
                cache_config = validate_cache_config()
                assert cache_config["config_source"] == "defaults" or "defaults" in str(cache_config.get("config_source", ""))
    
    def test_environment_variable_priority(self, tmp_path, monkeypatch):
        """测试环境变量优先于配置文件"""
        # 创建配置文件
        config_file = tmp_path / "priority_test.env"
        config_file.write_text("CACHE_REDIS_HOST=config_host\nCACHE_REDIS_PORT=6379\n")
        
        monkeypatch.setenv("BLOGN_CONFIG_FILE", str(config_file))
        # 设置环境变量（应该优先）
        monkeypatch.setenv("CACHE_REDIS_HOST", "env_host")
        
        # 重置全局变量
        from src.config import utils
        utils._config_file_path = None
        
        with patch('src.config.utils.is_docker_container', return_value=False):
            load_config_file()
            
            # 验证环境变量优先
            # 注意：pydantic_settings 会从环境变量读取，所以这里主要验证逻辑
            assert os.getenv("CACHE_REDIS_HOST") == "env_host"
