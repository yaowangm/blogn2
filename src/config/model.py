"""
模型配置模块

提供BERT模型相关配置，支持从环境变量和配置文件加载配置。
包含模型路径、设备选择、性能参数等配置项。
"""

import os
from typing import Optional

from .utils import load_config_file, get_config_file_path

# 加载配置文件（如果存在）
load_config_file()


class ModelSettings:
    """
    模型配置类
    
    支持从环境变量和.env文件加载配置。
    所有配置项都有合理的默认值。
    """
    
    def __init__(self):
        # 模型配置
        self.model_name = os.getenv('MODEL_MODEL_NAME', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.model_path = os.getenv('MODEL_MODEL_PATH') or None  # 本地模型路径，如果为None则使用model_name从Hugging Face下载
        self.device = os.getenv('MODEL_DEVICE', 'auto')  # auto, cpu, cuda, cuda:0等
        
        # 模型性能参数
        self.max_length = int(os.getenv('MODEL_MAX_LENGTH', '512'))
        self.vector_dimension = int(os.getenv('MODEL_VECTOR_DIMENSION', '384'))
        
        # 模型加载策略
        self.prefer_local = os.getenv('MODEL_PREFER_LOCAL', 'true').lower() == 'true'  # 是否优先使用本地模型
        self.fallback_to_huggingface = os.getenv('MODEL_FALLBACK_TO_HUGGINGFACE', 'true').lower() == 'true'  # 本地模型失败时是否回退到Hugging Face
        
        # 模型缓存配置
        self.cache_dir = os.getenv('MODEL_CACHE_DIR') or None  # 模型缓存目录，None表示使用默认目录


# 创建全局模型配置实例
model_settings = ModelSettings()


def get_model_device() -> str:
    """
    获取模型设备配置
    
    Returns:
        str: 设备名称 (cpu, cuda, cuda:0等)
    """
    if model_settings.device == "auto":
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"
    return model_settings.device


def get_model_path() -> Optional[str]:
    """
    获取模型路径配置
    
    Returns:
        Optional[str]: 本地模型路径，如果为None则使用model_name
    """
    return model_settings.model_path


def get_model_name() -> str:
    """
    获取模型名称
    
    Returns:
        str: 模型名称
    """
    return model_settings.model_name


def get_model_cache_dir() -> Optional[str]:
    """
    获取模型缓存目录
    
    Returns:
        Optional[str]: 缓存目录路径，None表示使用默认目录
    """
    return model_settings.cache_dir


def validate_model_config() -> dict:
    """
    验证模型配置并返回配置信息
    
    Returns:
        Dict: 包含完整模型配置信息的字典
    """
    config_file = get_config_file_path()
    config_info = {
        "model_name": model_settings.model_name,
        "model_path": model_settings.model_path,
        "device": get_model_device(),
        "max_length": model_settings.max_length,
        "vector_dimension": model_settings.vector_dimension,
        "prefer_local": model_settings.prefer_local,
        "fallback_to_huggingface": model_settings.fallback_to_huggingface,
        "cache_dir": model_settings.cache_dir,
        "config_source": str(config_file) if config_file else "defaults"
    }
    
    return config_info


def get_default_model_path() -> str:
    """
    获取默认的本地模型路径
    
    Returns:
        str: 默认本地模型路径
    """
    # 使用常见的模型缓存目录
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".cache", "modelscope", "hub", "models", "sentence-transformers", "paraphrase-multilingual-MiniLM-L12-v2")
