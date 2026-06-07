"""
文件操作工具模块

提供文件操作相关的工具函数，包括临时目录管理、文件路径处理等。
"""

import os
import shutil
import tempfile


def get_temp_dir():
    """获取临时目录路径，兼容不同操作系统"""
    return os.path.join(tempfile.gettempdir(), "blogn2_uploads")


def promote_temp_relative_path(relative_path: str, upload_dir: str) -> str | None:
    """
    将 temp/ 下的临时文件移动到 upload_dir/YYYYMM/ 正式目录。

    使用 shutil.move 以支持跨文件系统（如 Docker 中 /tmp 与挂载卷 /app/uploads）。

    Returns:
        新的相对路径（如 202506/xxx.jpg）；临时源文件不存在时返回 None。
    """
    if not relative_path.startswith("temp/"):
        return relative_path

    temp_filename = relative_path[len("temp/") :]
    temp_path = os.path.join(get_temp_dir(), temp_filename)
    if not os.path.exists(temp_path):
        return None

    from src.utils.time_utils import TimeUtils

    month_dir = TimeUtils.now_utc().strftime("%Y%m")
    dest_dir = os.path.join(upload_dir, month_dir)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, temp_filename)
    shutil.move(temp_path, dest_path)
    return f"{month_dir}/{temp_filename}"


def validate_and_sanitize_path(base_path: str, user_path: str) -> str:
    """
    验证和清理文件路径，防止路径遍历攻击
    
    Args:
        base_path: 基础路径
        user_path: 用户提供的路径
        
    Returns:
        str: 清理后的安全路径
        
    Raises:
        HTTPException: 当路径不安全时抛出400错误
    """
    from fastapi import HTTPException
    
    # 规范化路径
    normalized_path = os.path.normpath(user_path)
    
    # 检查路径是否包含路径遍历攻击
    if normalized_path.startswith('..') or normalized_path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # 构建完整路径
    full_path = os.path.join(base_path, normalized_path)
    
    # 确保最终路径在基础路径内
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_path)):
        raise HTTPException(status_code=400, detail="Path traversal detected")
    
    return full_path
