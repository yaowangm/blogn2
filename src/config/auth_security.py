"""
认证安全配置模块

统一管理登录防爆破、密码重置限流、注册限流等配置项。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from .utils import load_config_file

# 加载配置文件（如果存在）
load_config_file()


class AuthSecuritySettings(BaseSettings):
    """认证安全配置"""

    # 登录防爆破
    login_max_fail_per_ip: int = 5
    login_max_fail_per_account: int = 5
    login_lock_seconds: int = 86400
    login_min_interval_seconds: int = 5

    # 密码重置申请限流
    pwdreset_req_max_per_ip: int = 5
    pwdreset_req_max_per_email: int = 3
    pwdreset_req_window_seconds: int = 3600

    # 重置 token 校验限流
    pwdreset_validate_max_per_ip: int = 30
    pwdreset_validate_window_seconds: int = 3600

    # 注册限流
    register_max_per_ip: int = 10
    register_window_seconds: int = 3600

    # Redis 不可用策略：True=拒绝（更安全），False=放行
    fail_closed_when_redis_down: bool = True

    # redis key 命名空间
    key_namespace: str = "authsec"

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )


auth_security_settings = AuthSecuritySettings()
