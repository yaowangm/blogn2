"""用户头像路径工具。"""

import os

_avatar_dir: str | None = None


def _get_avatar_dir() -> str:
    global _avatar_dir
    if _avatar_dir is None:
        from src.config.app import validate_app_config
        _avatar_dir = validate_app_config()["avatar_dir"]
    return _avatar_dir


def check_avatar_exists(userid: int | None) -> str | None:
    """检查用户头像文件是否存在，返回 Web 路径或 None。"""
    if not userid:
        return None

    avatar_dir = _get_avatar_dir()
    prefix = (userid // 10000) + 1
    avatar_path = f"/avatar/{prefix}/s_{userid}.jpg"
    real_path = os.path.join(avatar_dir, str(prefix), f"s_{userid}.jpg")
    if os.path.exists(real_path):
        return avatar_path
    return None
