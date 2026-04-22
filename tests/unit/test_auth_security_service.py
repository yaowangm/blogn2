"""
认证安全服务单元测试

覆盖登录防爆破、密码重置限流、注册限流等新增安全分支。
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from src.services.auth_security_service import AuthSecurityService


class TestAuthSecurityService:
    @pytest.fixture
    def service(self):
        return AuthSecurityService()

    @pytest.fixture
    def mock_redis(self):
        client = AsyncMock()
        client.eval = AsyncMock()
        client.delete = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_pre_login_check_ok(self, service, mock_redis):
        mock_redis.eval.return_value = ["OK", 0]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            await service.pre_login_check("127.0.0.1", "user@example.com")
        assert mock_redis.eval.called

    @pytest.mark.asyncio
    async def test_pre_login_check_lock_ip(self, service, mock_redis):
        mock_redis.eval.return_value = ["LOCK_IP", 120]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await service.pre_login_check("127.0.0.1", "user@example.com")
        assert exc.value.status_code == 429
        assert "登录失败次数过多" in str(exc.value.detail)
        assert exc.value.headers["Retry-After"] == "120"

    @pytest.mark.asyncio
    async def test_pre_login_check_cooldown_account(self, service, mock_redis):
        mock_redis.eval.return_value = ["COOLDOWN_ACCOUNT", 3]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await service.pre_login_check("127.0.0.1", "user@example.com")
        assert exc.value.status_code == 429
        assert "两次登录尝试间隔不能少于" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_on_login_failed_not_locked(self, service, mock_redis):
        mock_redis.eval.return_value = [2, 2, 0, 0]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            await service.on_login_failed("127.0.0.1", "user@example.com")
        assert mock_redis.eval.called

    @pytest.mark.asyncio
    async def test_on_login_failed_locked(self, service, mock_redis):
        mock_redis.eval.return_value = [5, 3, 1, 86400]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await service.on_login_failed("127.0.0.1", "user@example.com")
        assert exc.value.status_code == 429
        assert exc.value.headers["Retry-After"] == "86400"

    @pytest.mark.asyncio
    async def test_on_login_success_clears_counters(self, service, mock_redis):
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            await service.on_login_success("127.0.0.1", "user@example.com")
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_forgot_password_rate_limit_blocked(self, service, mock_redis):
        mock_redis.eval.return_value = [6, 120, 1, 40, 1, "LIMIT_K1", 120]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await service.check_forgot_password_rate_limit("127.0.0.1", "user@example.com")
        assert exc.value.status_code == 429
        assert "请求过于频繁" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_check_validate_token_rate_limit_blocked(self, service, mock_redis):
        mock_redis.eval.return_value = [31, 50, 1]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await service.check_reset_token_validate_rate_limit("127.0.0.1")
        assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_check_register_rate_limit_blocked(self, service, mock_redis):
        mock_redis.eval.return_value = [11, 200, 1]
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc:
                await service.check_register_rate_limit("127.0.0.1")
        assert exc.value.status_code == 429
        assert "注册请求过于频繁" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_get_redis_fail_closed(self, service):
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=None), \
             patch("src.services.auth_security_service.os.getenv", return_value=None):
            with pytest.raises(HTTPException) as exc:
                await service.pre_login_check("127.0.0.1", "u")
        assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_get_redis_testing_env_bypass(self, service):
        with patch("src.services.auth_security_service.cache_manager.initialize", new=AsyncMock()), \
             patch("src.services.auth_security_service.cache_manager.get_redis_client", return_value=None), \
             patch.dict("os.environ", {"TESTING": "true"}, clear=False):
            await service.pre_login_check("127.0.0.1", "u")
