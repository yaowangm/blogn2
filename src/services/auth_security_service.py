"""
认证安全服务

提供：
- 登录防爆破（IP + 账号双维度，失败锁定，最小尝试间隔）
- 密码重置申请限流（IP + 邮箱）
- 重置 token 校验限流（IP）
- 注册限流（IP）
"""

import hashlib
import os
from typing import Optional, Tuple

from fastapi import HTTPException, status

from src.config.auth_security import auth_security_settings
from src.config.cache import cache_settings
from src.utils.cache import cache_manager


class AuthSecurityService:
    """认证相关安全策略服务"""

    _LOGIN_PRECHECK_LUA = """
local lock_ip_exists = redis.call('EXISTS', KEYS[1])
if lock_ip_exists == 1 then
  local ttl = redis.call('TTL', KEYS[1])
  return {'LOCK_IP', ttl}
end

local lock_acc_exists = redis.call('EXISTS', KEYS[2])
if lock_acc_exists == 1 then
  local ttl = redis.call('TTL', KEYS[2])
  return {'LOCK_ACCOUNT', ttl}
end

local cd_ip_exists = redis.call('EXISTS', KEYS[3])
if cd_ip_exists == 1 then
  local ttl = redis.call('TTL', KEYS[3])
  return {'COOLDOWN_IP', ttl}
end

local cd_acc_exists = redis.call('EXISTS', KEYS[4])
if cd_acc_exists == 1 then
  local ttl = redis.call('TTL', KEYS[4])
  return {'COOLDOWN_ACCOUNT', ttl}
end

redis.call('SET', KEYS[3], '1', 'EX', tonumber(ARGV[1]), 'NX')
redis.call('SET', KEYS[4], '1', 'EX', tonumber(ARGV[1]), 'NX')
return {'OK', 0}
"""

    _LOGIN_FAIL_LUA = """
local ip_count = redis.call('INCR', KEYS[1])
if ip_count == 1 then
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
end

local acc_count = redis.call('INCR', KEYS[2])
if acc_count == 1 then
  redis.call('EXPIRE', KEYS[2], tonumber(ARGV[3]))
end

local locked = 0
local retry_after = 0

if ip_count >= tonumber(ARGV[1]) then
  redis.call('SET', KEYS[3], '1', 'EX', tonumber(ARGV[3]))
  locked = 1
  retry_after = tonumber(ARGV[3])
end

if acc_count >= tonumber(ARGV[2]) then
  redis.call('SET', KEYS[4], '1', 'EX', tonumber(ARGV[3]))
  locked = 1
  retry_after = tonumber(ARGV[3])
end

return {ip_count, acc_count, locked, retry_after}
"""

    _DUAL_WINDOW_LIMIT_LUA = """
local c1 = redis.call('INCR', KEYS[1])
if c1 == 1 then
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
end
local ttl1 = redis.call('TTL', KEYS[1])

local c2 = redis.call('INCR', KEYS[2])
if c2 == 1 then
  redis.call('EXPIRE', KEYS[2], tonumber(ARGV[3]))
end
local ttl2 = redis.call('TTL', KEYS[2])

local blocked = 0
local reason = 'OK'
local retry_after = 0
if c1 > tonumber(ARGV[1]) then
  blocked = 1
  reason = 'LIMIT_K1'
  retry_after = ttl1
end
if c2 > tonumber(ARGV[2]) then
  blocked = 1
  if ttl2 > retry_after then
    retry_after = ttl2
  end
  reason = 'LIMIT_K2'
end
return {c1, ttl1, c2, ttl2, blocked, reason, retry_after}
"""

    _SINGLE_WINDOW_LIMIT_LUA = """
local c = redis.call('INCR', KEYS[1])
if c == 1 then
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[2]))
end
local ttl = redis.call('TTL', KEYS[1])
local blocked = 0
if c > tonumber(ARGV[1]) then
  blocked = 1
end
return {c, ttl, blocked}
"""

    def __init__(self):
        self.settings = auth_security_settings
        self.prefix = cache_settings.cache_prefix

    def _login_lock_message(self) -> str:
        return (
            "登录失败次数过多，请24小时后再试。"
            "安全规则：同一IP或账号5次失败将锁定24小时。"
        )

    def _login_cooldown_message(self) -> str:
        return (
            f"两次登录尝试间隔不能少于{self.settings.login_min_interval_seconds}秒。"
            f"安全规则：两次登录尝试至少间隔{self.settings.login_min_interval_seconds}秒。"
        )

    def _forgot_password_limit_message(self) -> str:
        return (
            "请求过于频繁，请稍后再试。"
            f"安全规则：忘记密码接口每IP每小时最多{self.settings.pwdreset_req_max_per_ip}次，"
            f"同邮箱每小时最多{self.settings.pwdreset_req_max_per_email}次。"
        )

    def _reset_token_validate_limit_message(self) -> str:
        return (
            "请求过于频繁，请稍后再试。"
            f"安全规则：重置令牌校验接口每IP每小时最多{self.settings.pwdreset_validate_max_per_ip}次。"
        )

    def _register_limit_message(self) -> str:
        return (
            "注册请求过于频繁，请稍后再试。"
            f"安全规则：注册相关接口每IP每小时最多{self.settings.register_max_per_ip}次。"
        )

    @staticmethod
    def normalize_account(username_or_email: str) -> str:
        return (username_or_email or "").strip().lower()

    @staticmethod
    def normalize_email(email: str) -> str:
        return (email or "").strip().lower()

    @staticmethod
    def normalize_ip(client_ip: Optional[str]) -> str:
        v = (client_ip or "").strip()
        return v if v else "unknown"

    @staticmethod
    def hash_identifier(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]

    def _k(self, *parts: str) -> str:
        raw = ":".join(parts)
        return f"{self.prefix}:{self.settings.key_namespace}:{raw}"

    async def _get_redis(self):
        await cache_manager.initialize()
        redis_client = cache_manager.get_redis_client()
        if redis_client:
            return redis_client
        # 测试环境默认放行，避免无 Redis 时单测被保护逻辑阻断
        if os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("TESTING") == "true":
            return None
        if self.settings.fail_closed_when_redis_down:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="认证安全服务不可用，请稍后重试",
            )
        return None

    @staticmethod
    def _parse_reason_and_ttl(result) -> Tuple[str, int]:
        reason = str(result[0]) if result and len(result) > 0 else "UNKNOWN"
        ttl = int(result[1]) if result and len(result) > 1 and result[1] is not None else 0
        return reason, max(ttl, 1)

    async def pre_login_check(self, client_ip: str, username_or_email: str) -> None:
        redis_client = await self._get_redis()
        if redis_client is None:
            return

        ip = self.normalize_ip(client_ip)
        acc_hash = self.hash_identifier(self.normalize_account(username_or_email))

        lock_ip = self._k("login", "lock", "ip", ip)
        lock_acc = self._k("login", "lock", "acc", acc_hash)
        cd_ip = self._k("login", "cd", "ip", ip)
        cd_acc = self._k("login", "cd", "acc", acc_hash)

        result = await redis_client.eval(
            self._LOGIN_PRECHECK_LUA,
            4,
            lock_ip,
            lock_acc,
            cd_ip,
            cd_acc,
            str(self.settings.login_min_interval_seconds),
        )
        reason, ttl = self._parse_reason_and_ttl(result)

        if reason in ("LOCK_IP", "LOCK_ACCOUNT"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self._login_lock_message(),
                headers={"Retry-After": str(ttl)},
            )
        if reason in ("COOLDOWN_IP", "COOLDOWN_ACCOUNT"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self._login_cooldown_message(),
                headers={"Retry-After": str(ttl)},
            )

    async def on_login_failed(self, client_ip: str, username_or_email: str) -> None:
        redis_client = await self._get_redis()
        if redis_client is None:
            return

        ip = self.normalize_ip(client_ip)
        acc_hash = self.hash_identifier(self.normalize_account(username_or_email))

        fail_ip = self._k("login", "fail", "ip", ip)
        fail_acc = self._k("login", "fail", "acc", acc_hash)
        lock_ip = self._k("login", "lock", "ip", ip)
        lock_acc = self._k("login", "lock", "acc", acc_hash)

        result = await redis_client.eval(
            self._LOGIN_FAIL_LUA,
            4,
            fail_ip,
            fail_acc,
            lock_ip,
            lock_acc,
            str(self.settings.login_max_fail_per_ip),
            str(self.settings.login_max_fail_per_account),
            str(self.settings.login_lock_seconds),
        )

        locked = int(result[2]) if result and len(result) > 2 else 0
        retry_after = int(result[3]) if result and len(result) > 3 and result[3] is not None else self.settings.login_lock_seconds
        if locked == 1:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self._login_lock_message(),
                headers={"Retry-After": str(max(retry_after, 1))},
            )

    async def on_login_success(self, client_ip: str, username_or_email: str) -> None:
        redis_client = await self._get_redis()
        if redis_client is None:
            return

        ip = self.normalize_ip(client_ip)
        acc_hash = self.hash_identifier(self.normalize_account(username_or_email))

        fail_ip = self._k("login", "fail", "ip", ip)
        fail_acc = self._k("login", "fail", "acc", acc_hash)
        await redis_client.delete(fail_ip, fail_acc)

    async def check_forgot_password_rate_limit(self, client_ip: str, email: str) -> None:
        redis_client = await self._get_redis()
        if redis_client is None:
            return

        ip = self.normalize_ip(client_ip)
        email_hash = self.hash_identifier(self.normalize_email(email))

        k_ip = self._k("pwdreset", "req", "ip", ip)
        k_email = self._k("pwdreset", "req", "email", email_hash)
        result = await redis_client.eval(
            self._DUAL_WINDOW_LIMIT_LUA,
            2,
            k_ip,
            k_email,
            str(self.settings.pwdreset_req_max_per_ip),
            str(self.settings.pwdreset_req_max_per_email),
            str(self.settings.pwdreset_req_window_seconds),
        )
        blocked = int(result[4]) if result and len(result) > 4 else 0
        retry_after = int(result[6]) if result and len(result) > 6 and result[6] is not None else self.settings.pwdreset_req_window_seconds
        if blocked == 1:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self._forgot_password_limit_message(),
                headers={"Retry-After": str(max(retry_after, 1))},
            )

    async def check_reset_token_validate_rate_limit(self, client_ip: str) -> None:
        redis_client = await self._get_redis()
        if redis_client is None:
            return

        ip = self.normalize_ip(client_ip)
        key = self._k("pwdreset", "validate", "ip", ip)
        result = await redis_client.eval(
            self._SINGLE_WINDOW_LIMIT_LUA,
            1,
            key,
            str(self.settings.pwdreset_validate_max_per_ip),
            str(self.settings.pwdreset_validate_window_seconds),
        )
        blocked = int(result[2]) if result and len(result) > 2 else 0
        retry_after = int(result[1]) if result and len(result) > 1 and result[1] is not None else self.settings.pwdreset_validate_window_seconds
        if blocked == 1:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self._reset_token_validate_limit_message(),
                headers={"Retry-After": str(max(retry_after, 1))},
            )

    async def check_register_rate_limit(self, client_ip: str) -> None:
        redis_client = await self._get_redis()
        if redis_client is None:
            return

        ip = self.normalize_ip(client_ip)
        key = self._k("register", "ip", ip)
        result = await redis_client.eval(
            self._SINGLE_WINDOW_LIMIT_LUA,
            1,
            key,
            str(self.settings.register_max_per_ip),
            str(self.settings.register_window_seconds),
        )
        blocked = int(result[2]) if result and len(result) > 2 else 0
        retry_after = int(result[1]) if result and len(result) > 1 and result[1] is not None else self.settings.register_window_seconds
        if blocked == 1:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self._register_limit_message(),
                headers={"Retry-After": str(max(retry_after, 1))},
            )
