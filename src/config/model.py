"""
模型配置模块

提供BERT模型相关配置，支持从环境变量和配置文件加载配置。
包含模型路径、设备选择、性能参数等配置项。
"""

import logging
import os
from typing import Optional

from .utils import load_config_file, get_config_file_path

logger = logging.getLogger(__name__)

# 加载配置文件（如果存在）
load_config_file()

# Docker 内 BERT 模型 hub 可能挂载的路径（与 docker-compose volume 一致），用于路径解析回退
_HUB_DIRS = [
    "/app/.cache/models/bert-model-hub",
    "/app/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
]


def _resolve_model_path_to_snapshot(path: Optional[str]) -> Optional[str]:
    """
    当配置的路径存在但无 config.json 时，从 _HUB_DIRS 解析：
    若挂载目录自身含 config.json 则直接返回该目录，否则从 snapshots/<revision> 取第一个含 config.json 的目录。
    对传入路径会做 strip 和 expanduser，避免 .env 中带空格或 ~ 导致加载失败。
    """
    if not path:
        return None
    path = path.strip()
    if not path:
        return None
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return path
    if os.path.isfile(os.path.join(path, "config.json")):
        return os.path.abspath(path)
    # 配置路径存在但无 config.json，回退到 _HUB_DIRS 可能加载到无关模型，打日志避免静默误用
    logger.warning(
        "MODEL_MODEL_PATH 指向的目录存在但无 config.json，将尝试从 Docker 挂载目录解析: %s",
        path,
    )
    for hub_dir in _HUB_DIRS:
        if not os.path.isdir(hub_dir):
            continue
        # 挂载目录本身即为 snapshot（含 config.json）
        if os.path.isfile(os.path.join(hub_dir, "config.json")):
            return os.path.abspath(hub_dir)
        snapshots_dir = os.path.join(hub_dir, "snapshots")
        if not os.path.isdir(snapshots_dir):
            continue
        try:
            for rev in sorted(os.listdir(snapshots_dir)):
                snapshot = os.path.join(snapshots_dir, rev)
                if os.path.isdir(snapshot) and os.path.isfile(os.path.join(snapshot, "config.json")):
                    return os.path.abspath(snapshot)
        except OSError:
            continue
    return os.path.abspath(path) if os.path.isdir(path) else path


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
    获取模型设备配置。
    auto 时：仅当 CUDA 可用且当前 GPU 架构在 PyTorch 编译支持列表内才返回 cuda，
    否则返回 cpu，避免 no kernel image 等运行时错误。
    """
    if model_settings.device == "auto":
        try:
            import torch
            if not torch.cuda.is_available():
                return "cpu"
            # 仅当存在 device 0 且其架构在 PyTorch 编译支持列表内时才用 cuda
            try:
                if torch.cuda.device_count() < 1:
                    return "cpu"
                major, minor = torch.cuda.get_device_capability(0)
                arch = f"sm_{major}{minor}"
                arch_list = torch.cuda.get_arch_list()
                # 支持带后缀的架构名（如 sm_90a），部分 PyTorch 构建仅列出 sm_90a 而无 sm_90
                if arch in arch_list or any(a.startswith(arch) for a in arch_list):
                    return "cuda"
            except (RuntimeError, AttributeError):
                pass
            return "cpu"
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
