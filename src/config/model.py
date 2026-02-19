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

# Docker 内 BERT 模型 hub 可能挂载的路径（与 docker-compose volume 一致），用于路径解析回退
_HUB_DIRS = [
    "/app/.cache/models/bert-model-hub",
    "/app/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
]


def _resolve_model_path_to_snapshot(path: Optional[str]) -> Optional[str]:
    """
    当配置的路径存在但无 config.json 时（如 compose 默认的 /app/.cache/models/bert-model），
    从上述 _HUB_DIRS 的 snapshots/<revision> 中取第一个含 config.json 的目录并返回。
    用于 Docker 离线加载 BERT 模型。
    """
    if not path or not os.path.isdir(path):
        return path
    if os.path.isfile(os.path.join(path, "config.json")):
        return path
    for hub_dir in _HUB_DIRS:
        snapshots_dir = os.path.join(hub_dir, "snapshots")
        if not os.path.isdir(snapshots_dir):
            continue
        try:
            for rev in sorted(os.listdir(snapshots_dir)):
                snapshot = os.path.join(snapshots_dir, rev)
                if os.path.isdir(snapshot) and os.path.isfile(os.path.join(snapshot, "config.json")):
                    return snapshot
        except OSError:
            continue
    return path


class ModelSettings:
    """
    模型配置类
    
    支持从环境变量和.env文件加载配置。
    所有配置项都有合理的默认值。
    使用属性访问器确保每次访问时都读取最新的环境变量值。
    """
    
    def __init__(self):
        # 标记已初始化，避免重复初始化
        self._initialized = True
    
    @property
    def model_name(self) -> str:
        """模型名称"""
        return os.getenv('MODEL_MODEL_NAME', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    @property
    def model_path(self) -> Optional[str]:
        """本地模型路径（若配置的路径无 config.json 则自动解析到 HF hub 的 snapshot）"""
        raw = os.getenv('MODEL_MODEL_PATH') or None
        return _resolve_model_path_to_snapshot(raw)
    
    @property
    def device(self) -> str:
        """运行设备"""
        return os.getenv('MODEL_DEVICE', 'auto')
    
    @property
    def max_length(self) -> int:
        """最大输入长度"""
        return int(os.getenv('MODEL_MAX_LENGTH', '512'))
    
    @property
    def vector_dimension(self) -> int:
        """向量维度"""
        return int(os.getenv('MODEL_VECTOR_DIMENSION', '384'))
        
    @property
    def prefer_local(self) -> bool:
        """是否优先使用本地模型"""
        return os.getenv('MODEL_PREFER_LOCAL', 'true').lower() == 'true'
    
    @property
    def fallback_to_huggingface(self) -> bool:
        """本地模型失败时是否回退到Hugging Face"""
        return os.getenv('MODEL_FALLBACK_TO_HUGGINGFACE', 'true').lower() == 'true'
    
    @property
    def cache_dir(self) -> Optional[str]:
        """模型缓存目录"""
        return os.getenv('MODEL_CACHE_DIR') or None


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
