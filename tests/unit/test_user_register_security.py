"""
用户注册安全增强测试

覆盖新增限流接入与防枚举统一错误文案。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from src.routes.user_register import (
    UserRegisterRequest,
    register_user,
    validate_regkey,
)


class TestUserRegisterSecurity:
    @pytest.fixture
    def mock_request(self):
        req = MagicMock()
        req.client.host = "127.0.0.1"
        req.headers.get.return_value = ""
        return req

    @pytest.fixture
    def register_req(self):
        return UserRegisterRequest(
            username="test_user",
            email="test@example.com",
            password="Abcdef12",
            regkey="AAAAA-BBBBB-CCCCC-DDDDD-EEEEE",
        )

    @pytest.mark.asyncio
    async def test_register_rate_limit_blocked(self, register_req, mock_request):
        session = AsyncMock()
        service = MagicMock()
        service.normalize_ip.return_value = "127.0.0.1"
        service.check_register_rate_limit = AsyncMock(
            side_effect=HTTPException(status_code=429, detail="注册请求过于频繁，请稍后再试")
        )
        with patch("src.routes.user_register.AuthSecurityService", return_value=service):
            with pytest.raises(HTTPException) as exc_info:
                await register_user(register_req, session, mock_request)

        assert exc_info.value.status_code == 429
        session.exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_duplicate_username_returns_generic_message(self, register_req, mock_request):
        session = AsyncMock()
        first_result = MagicMock()
        first_result.first.return_value = object()
        session.exec.return_value = first_result

        service = MagicMock()
        service.normalize_ip.return_value = "127.0.0.1"
        service.check_register_rate_limit = AsyncMock()

        with patch("src.routes.user_register.AuthSecurityService", return_value=service):
            with pytest.raises(HTTPException) as exc_info:
                await register_user(register_req, session, mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "注册失败，请检查信息或稍后重试"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_generic_message(self, register_req, mock_request):
        session = AsyncMock()
        username_result = MagicMock()
        username_result.first.return_value = None
        email_result = MagicMock()
        email_result.first.return_value = object()
        session.exec.side_effect = [username_result, email_result]

        service = MagicMock()
        service.normalize_ip.return_value = "127.0.0.1"
        service.check_register_rate_limit = AsyncMock()

        with patch("src.routes.user_register.AuthSecurityService", return_value=service):
            with pytest.raises(HTTPException) as exc_info:
                await register_user(register_req, session, mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "注册失败，请检查信息或稍后重试"

    @pytest.mark.asyncio
    async def test_register_invalid_regkey_returns_generic_message(self, register_req, mock_request):
        session = AsyncMock()
        username_result = MagicMock()
        username_result.first.return_value = None
        email_result = MagicMock()
        email_result.first.return_value = None
        regkey_result = MagicMock()
        regkey_result.first.return_value = None
        session.exec.side_effect = [username_result, email_result, regkey_result]

        service = MagicMock()
        service.normalize_ip.return_value = "127.0.0.1"
        service.check_register_rate_limit = AsyncMock()

        with patch("src.routes.user_register.AuthSecurityService", return_value=service):
            with pytest.raises(HTTPException) as exc_info:
                await register_user(register_req, session, mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "注册失败，请检查信息或稍后重试"

    @pytest.mark.asyncio
    async def test_validate_regkey_rate_limit_blocked(self, mock_request):
        session = AsyncMock()
        service = MagicMock()
        service.normalize_ip.return_value = "127.0.0.1"
        service.check_register_rate_limit = AsyncMock(
            side_effect=HTTPException(status_code=429, detail="注册请求过于频繁，请稍后再试")
        )
        with patch("src.routes.user_register.AuthSecurityService", return_value=service):
            result = await validate_regkey("AAAAA-BBBBB-CCCCC-DDDDD-EEEEE", session, mock_request)

        assert result["valid"] is False
        assert "验证失败" in result["message"]
