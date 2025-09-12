"""
文件操作工具模块

提供文件操作相关的工具函数，包括临时目录管理、文件路径处理等。
"""

import os
import tempfile


def get_temp_dir():
    """获取临时目录路径，兼容不同操作系统"""
    return os.path.join(tempfile.gettempdir(), "blogn2_uploads")


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
