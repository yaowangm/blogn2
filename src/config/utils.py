"""
配置工具模块

提供配置相关的工具函数，如判断运行环境、加载配置文件等。
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 全局变量存储使用的配置文件路径
_config_file_path: Optional[Path] = None


def is_docker_container() -> bool:
    """
    判断是否在 Docker 容器中运行
    
    使用多种方法检测：
    1. 检查 /.dockerenv 文件是否存在（Docker 创建的标记文件）
    2. 检查 /proc/1/cgroup 文件是否包含 docker 或 containerd
    3. 检查环境变量 DOCKER_CONTAINER（如果显式设置）
    
    Returns:
        bool: 如果在 Docker 容器中返回 True，否则返回 False
    """
    # 方法1: 检查 /.dockerenv 文件（最可靠的方法）
    if Path("/.dockerenv").exists():
        return True
    
    # 方法2: 检查环境变量（如果显式设置）
    if os.getenv("DOCKER_CONTAINER", "").lower() in ("true", "1", "yes"):
        return True
    
    # 方法3: 检查 /proc/1/cgroup 文件
    try:
        cgroup_path = Path("/proc/1/cgroup")
        if cgroup_path.exists():
            with open(cgroup_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 检查是否包含 docker 或 containerd
                if "docker" in content.lower() or "containerd" in content.lower():
                    return True
    except (IOError, OSError):
        # 如果无法读取文件，忽略错误
        pass
    
    return False


def load_config_file() -> Optional[Path]:
    """
    加载配置文件
    
    配置规则：
    1. 优先使用 ``BLOGN_CONFIG_FILE`` 指向的文件（须存在）。
    2. 否则若当前工作目录下存在 ``.env``，则加载（Docker 中同样适用，便于挂载项目 ``.env``）。
    3. 若均不可用，返回 None；此时仅依赖进程环境变量与代码默认值。Docker 且无上述文件时会打日志提示。
    
    Returns:
        Optional[Path]: 使用的配置文件路径（绝对路径），如果未使用配置文件则返回 None
    """
    global _config_file_path
    
    # 如果已经加载过，直接返回
    if _config_file_path is not None:
        return _config_file_path
    
    try:
        in_docker = is_docker_container()
    except Exception:
        # 如果检测 Docker 容器时出错，假设不在容器中
        in_docker = False
    
    config_file: Optional[Path] = None
    
    # 检查 BLOGN_CONFIG_FILE 环境变量
    config_file_env = os.getenv("BLOGN_CONFIG_FILE")
    if config_file_env:
        try:
            config_file = Path(config_file_env).resolve()
            if not config_file.exists():
                logger.warning(f"配置文件不存在: {config_file}")
                config_file = None
        except Exception as e:
            logger.warning(f"解析配置文件路径失败: {e}")
            config_file = None
    if config_file is None:
        try:
            env_file = Path.cwd() / ".env"
            if env_file.exists():
                config_file = env_file.resolve()
        except Exception as e:
            logger.debug(f"无法获取当前目录或检查 .env: {e}")
            config_file = None

    if config_file is None and in_docker:
        logger.warning(
            "在 Docker 容器中运行：未设置 BLOGN_CONFIG_FILE，且工作目录下无 .env；"
            "将仅使用进程环境变量与代码默认值（若需 BASE_URL 等，请挂载 .env 或设置 BLOGN_CONFIG_FILE）"
        )
    
    # 如果找到配置文件，加载它
    if config_file:
        try:
            load_dotenv(config_file, override=False)  # override=False 表示环境变量优先
            _config_file_path = config_file
            return _config_file_path
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_file}: {e}")
            _config_file_path = None
            return None
    
    # 未使用配置文件
    _config_file_path = None
    return None


def get_config_file_path() -> Optional[Path]:
    """
    获取当前使用的配置文件路径
    
    Returns:
        Optional[Path]: 配置文件路径（绝对路径），如果未使用配置文件则返回 None
    """
    # 确保配置文件已加载
    load_config_file()
    return _config_file_path

