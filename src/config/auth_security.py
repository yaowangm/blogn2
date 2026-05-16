"""
认证安全配置模块

统一管理登录防爆破、密码重置限流、注册限流等配置项（状态存储为 PostgreSQL，非 Redis）。
"""

import os
from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .utils import load_config_file

# 加载配置文件（如果存在）
load_config_file()


class AuthSecuritySettings(BaseSettings):
    """认证安全配置"""

    # 登录防爆破（仅按用户维度持久化）
    login_max_fail_per_account: int = 5
    login_lock_seconds: int = 86400
    login_min_interval_seconds: int = 5

    # 密码重置申请限流（按已解析用户）
    pwdreset_req_max_per_email: int = 3
    pwdreset_req_window_seconds: int = 3600

    # 重置 token 校验 / 执行重置（按用户维度）
    pwdreset_validate_max_per_user: int = 30
    pwdreset_validate_window_seconds: int = 3600

    # 注册成功后的用户维度窗口计数
    register_max_per_user: int = 10
    register_window_seconds: int = 3600

    # 认证安全状态写库失败时是否拒绝请求（true=更安全）
    fail_closed_when_db_error: bool = True

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fail_closed_env(cls, data: Any) -> Any:
        """若未设置 AUTH_FAIL_CLOSED_WHEN_DB_ERROR，则读取已废弃的 AUTH_FAIL_CLOSED_WHEN_REDIS_DOWN。"""
        if not isinstance(data, dict):
            return data
        if "fail_closed_when_db_error" in data and data["fail_closed_when_db_error"] is not None:
            return data
        legacy = os.environ.get("AUTH_FAIL_CLOSED_WHEN_REDIS_DOWN")
        if legacy is not None:
            out = {**data, "fail_closed_when_db_error": legacy.lower() in ("1", "true", "yes", "on")}
            return out
        return data


auth_security_settings = AuthSecuritySettings()
