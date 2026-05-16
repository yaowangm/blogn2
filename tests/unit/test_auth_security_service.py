"""
认证安全服务单元测试（数据库实现，mock session / repository）
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from src.services.auth_security_service import AuthSecurityService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def service(mock_session):
    return AuthSecurityService(mock_session)


class TestAuthSecurityService:
    @pytest.mark.asyncio
    async def test_pre_login_check_skips_without_user_id(self, service):
        await service.pre_login_check(None)
        service.session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_pre_login_check_ok(self, service, mock_session):
        with patch.object(
            service._repo,
            "apply_login_pre_check",
            new=AsyncMock(return_value=None),
        ):
            await service.pre_login_check(1)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pre_login_check_lock(self, service, mock_session):
        with patch.object(
            service._repo,
            "apply_login_pre_check",
            new=AsyncMock(return_value=("LOCK", 120)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.pre_login_check(1)
        assert exc.value.status_code == 429
        assert "登录失败次数过多" in str(exc.value.detail)
        assert exc.value.headers["Retry-After"] == "120"
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_pre_login_check_cooldown(self, service, mock_session):
        with patch.object(
            service._repo,
            "apply_login_pre_check",
            new=AsyncMock(return_value=("COOLDOWN", 3)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.pre_login_check(1)
        assert exc.value.status_code == 429
        assert "两次登录尝试间隔不能少于" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_on_login_failed_not_locked(self, service, mock_session):
        with patch.object(
            service._repo,
            "apply_login_failed",
            new=AsyncMock(return_value=(False, 5)),
        ):
            await service.on_login_failed(1)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_login_failed_locked(self, service, mock_session):
        with patch.object(
            service._repo,
            "apply_login_failed",
            new=AsyncMock(return_value=(True, 86400)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.on_login_failed(1)
        assert exc.value.status_code == 429
        assert exc.value.headers["Retry-After"] == "86400"

    @pytest.mark.asyncio
    async def test_on_login_success(self, service, mock_session):
        with patch.object(service._repo, "apply_login_success", new=AsyncMock()):
            await service.on_login_success(1)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_forgot_password_blocked(self, service, mock_session):
        with patch.object(
            service._repo,
            "bump_windowed_usage",
            new=AsyncMock(return_value=(True, 200)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.check_forgot_password_rate_limit(1)
        assert exc.value.status_code == 429
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_validate_token_blocked(self, service, mock_session):
        with patch.object(
            service._repo,
            "bump_windowed_usage",
            new=AsyncMock(return_value=(True, 50)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.check_reset_token_validate_rate_limit(1)
        assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_check_reset_password_blocked(self, service, mock_session):
        with patch.object(
            service._repo,
            "bump_windowed_usage",
            new=AsyncMock(return_value=(True, 50)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.check_reset_password_rate_limit(1)
        assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_record_register_blocked(self, service, mock_session):
        with patch.object(
            service._repo,
            "bump_windowed_usage",
            new=AsyncMock(return_value=(True, 200)),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.record_register_success(1, defer_commit=False)
        assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_commit_failure_fail_closed(self, service, mock_session):
        from sqlalchemy.exc import OperationalError

        mock_session.commit.side_effect = OperationalError("stmt", {}, Exception("db"))
        with patch.object(
            service._repo,
            "apply_login_pre_check",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.pre_login_check(1)
        assert exc.value.status_code == 503


class TestAuthSecuritySettingsLegacyEnv:
    """AUTH_FAIL_CLOSED 旧变量名兼容（仅未设置新变量时）"""

    def test_legacy_redis_down_env_when_db_error_unset(self, monkeypatch):
        monkeypatch.delenv("AUTH_FAIL_CLOSED_WHEN_DB_ERROR", raising=False)
        monkeypatch.setenv("AUTH_FAIL_CLOSED_WHEN_REDIS_DOWN", "false")
        from src.config.auth_security import AuthSecuritySettings

        s = AuthSecuritySettings()
        assert s.fail_closed_when_db_error is False

    def test_db_error_env_takes_precedence_over_legacy(self, monkeypatch):
        monkeypatch.setenv("AUTH_FAIL_CLOSED_WHEN_DB_ERROR", "true")
        monkeypatch.setenv("AUTH_FAIL_CLOSED_WHEN_REDIS_DOWN", "false")
        from src.config.auth_security import AuthSecuritySettings

        s = AuthSecuritySettings()
        assert s.fail_closed_when_db_error is True
