"""
配置工具模块

提供配置相关的工具函数，如判断运行环境等。
"""

import os
from pathlib import Path


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

