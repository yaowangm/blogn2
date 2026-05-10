"""
用户注册安全增强测试

覆盖注册成功后的用户维度限流与防枚举统一错误文案。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
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

    @pytest.fixture
    def mock_auth_security(self):
        m = MagicMock()
        m.record_register_success = AsyncMock()
        return m

    @pytest.mark.asyncio
    async def test_register_rate_limit_blocked(self, register_req, mock_request):
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()

        added = []

        def capture_add(obj):
            added.append(obj)

        session.add = MagicMock(side_effect=capture_add)

        async def do_flush():
            for o in added:
                if getattr(o, "id", None) is None and hasattr(o, "name"):
                    o.id = 100

        session.flush = AsyncMock(side_effect=do_flush)

        username_result = MagicMock()
        username_result.first.return_value = None
        email_result = MagicMock()
        email_result.first.return_value = None
        regkey_record = MagicMock()
        regkey_record.status = 1
        regkey_result = MagicMock()
        regkey_result.first.return_value = regkey_record
        session.exec.side_effect = [username_result, email_result, regkey_result]

        auth = MagicMock()
        auth.record_register_success = AsyncMock(
            side_effect=HTTPException(status_code=429, detail="注册过于频繁，请稍后再试")
        )

        with pytest.raises(HTTPException) as exc_info:
            await register_user(register_req, session, auth, mock_request)

        assert exc_info.value.status_code == 429
        session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_username_returns_generic_message(
        self, register_req, mock_request, mock_auth_security
    ):
        session = AsyncMock()
        first_result = MagicMock()
        first_result.first.return_value = object()
        session.exec.return_value = first_result

        with pytest.raises(HTTPException) as exc_info:
            await register_user(register_req, session, mock_auth_security, mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "注册失败，请检查信息或稍后重试"
        mock_auth_security.record_register_success.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_generic_message(
        self, register_req, mock_request, mock_auth_security
    ):
        session = AsyncMock()
        username_result = MagicMock()
        username_result.first.return_value = None
        email_result = MagicMock()
        email_result.first.return_value = object()
        session.exec.side_effect = [username_result, email_result]

        with pytest.raises(HTTPException) as exc_info:
            await register_user(register_req, session, mock_auth_security, mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "注册失败，请检查信息或稍后重试"

    @pytest.mark.asyncio
    async def test_register_invalid_regkey_returns_generic_message(
        self, register_req, mock_request, mock_auth_security
    ):
        session = AsyncMock()
        username_result = MagicMock()
        username_result.first.return_value = None
        email_result = MagicMock()
        email_result.first.return_value = None
        regkey_result = MagicMock()
        regkey_result.first.return_value = None
        session.exec.side_effect = [username_result, email_result, regkey_result]

        with pytest.raises(HTTPException) as exc_info:
            await register_user(register_req, session, mock_auth_security, mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "注册失败，请检查信息或稍后重试"

    @pytest.mark.asyncio
    async def test_validate_regkey_no_rate_limit_wraps_errors(self, mock_request):
        session = AsyncMock()
        session.exec.side_effect = RuntimeError("db")
        result = await validate_regkey("AAAAA-BBBBB-CCCCC-DDDDD-EEEEE", session, mock_request)

        assert result["valid"] is False
        assert "验证失败" in result["message"]
