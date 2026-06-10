"""
注册码管理 API 单元测试

覆盖 src/routes/regkey.py 中的列表、兑换、校验与使用接口。
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.models.regkey import RegKey
from src.routes.regkey import (
    ExchangeRegKeyRequest,
    exchange_regkey,
    get_regkey_list,
    use_regkey,
    validate_regkey,
)


def _make_regkey_row(
    *,
    row_id=1,
    name="AAAAABBBBBCCCCCDDDDDEEEEE",
    ownerid=5,
    userid=None,
    status=1,
    owner_name="owner",
):
    row = MagicMock()
    row.id = row_id
    row.name = name
    row.ownerid = ownerid
    row.userid = userid
    row.status = status
    row.createtime = datetime(2026, 1, 1, tzinfo=timezone.utc)
    row.owner_name = owner_name
    return row


class TestRegKeyList:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_regkey_list_requires_login(self, mock_async_session):
        with pytest.raises(HTTPException) as exc_info:
            await get_regkey_list(session=mock_async_session, current_user=None)

        assert exc_info.value.status_code == 401

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_regkey_list_success(self, mock_async_session):
        list_result = MagicMock()
        list_result.all.return_value = [_make_regkey_row()]

        mock_async_session.exec.return_value = list_result

        result = await get_regkey_list(
            session=mock_async_session,
            current_user={"id": 5, "state": 1},
        )

        assert "regkeys" in result
        assert len(result["regkeys"]) == 1
        item = result["regkeys"][0]
        assert item["id"] == 1
        assert item["regkey"] == "AAAAABBBBBCCCCCDDDDDEEEEE"
        assert item["owner_name"] == "owner"
        assert item["user_name"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_regkey_list_includes_consumer_name(self, mock_async_session):
        list_result = MagicMock()
        list_result.all.return_value = [_make_regkey_row(userid=9)]

        user_name_result = MagicMock()
        user_name_result.first.return_value = "consumer"

        mock_async_session.exec.side_effect = [list_result, user_name_result]

        result = await get_regkey_list(
            session=mock_async_session,
            current_user={"id": 5, "state": 1},
        )

        assert result["regkeys"][0]["user_name"] == "consumer"


class TestRegKeyExchange:
    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.id = 5
        user.point = 20
        return user

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exchange_regkey_requires_login(self, mock_async_session):
        request = ExchangeRegKeyRequest(user_id=5)

        with pytest.raises(HTTPException) as exc_info:
            await exchange_regkey(request, mock_async_session, current_user=None)

        assert exc_info.value.status_code == 401

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exchange_regkey_forbidden_for_other_user(self, mock_async_session):
        request = ExchangeRegKeyRequest(user_id=6)

        with pytest.raises(HTTPException) as exc_info:
            await exchange_regkey(
                request,
                mock_async_session,
                current_user={"id": 5, "state": 1},
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exchange_regkey_user_not_found(self, mock_async_session):
        user_result = MagicMock()
        user_result.first.return_value = None
        mock_async_session.exec.return_value = user_result

        request = ExchangeRegKeyRequest(user_id=5)

        with pytest.raises(HTTPException) as exc_info:
            await exchange_regkey(
                request,
                mock_async_session,
                current_user={"id": 5, "state": 1},
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exchange_regkey_insufficient_points(self, mock_async_session, normal_user):
        normal_user.point = 5
        user_result = MagicMock()
        user_result.first.return_value = normal_user
        mock_async_session.exec.return_value = user_result

        request = ExchangeRegKeyRequest(user_id=5)

        with patch("src.routes.regkey.PermissionUtils.is_admin", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await exchange_regkey(
                    request,
                    mock_async_session,
                    current_user={"id": 5, "state": 1},
                )

        assert exc_info.value.status_code == 400
        assert "积分不足" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exchange_regkey_success_deducts_points(self, mock_async_session, normal_user):
        user_result = MagicMock()
        user_result.first.return_value = normal_user
        mock_async_session.exec.return_value = user_result
        mock_async_session.refresh = AsyncMock()

        request = ExchangeRegKeyRequest(user_id=5)

        with patch("src.routes.regkey.PermissionUtils.is_admin", return_value=False):
            result = await exchange_regkey(
                request,
                mock_async_session,
                current_user={"id": 5, "state": 1},
            )

        assert normal_user.point == 10
        assert len(result["regkey"]) == 25
        assert result["remaining_points"] == 10
        assert result["is_admin"] is False
        assert result["message"] == "注册码兑换成功"
        mock_async_session.add.assert_called()
        mock_async_session.commit.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exchange_regkey_admin_free(self, mock_async_session, normal_user):
        user_result = MagicMock()
        user_result.first.return_value = normal_user
        mock_async_session.exec.return_value = user_result
        mock_async_session.refresh = AsyncMock()

        request = ExchangeRegKeyRequest(user_id=5)

        with patch("src.routes.regkey.PermissionUtils.is_admin", return_value=True):
            result = await exchange_regkey(
                request,
                mock_async_session,
                current_user={"id": 5, "state": 10},
            )

        assert normal_user.point == 20
        assert result["is_admin"] is True
        assert result["message"] == "注册码生成成功（管理员免费）"


class TestRegKeyValidate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_regkey_not_found(self, mock_async_session):
        regkey_result = MagicMock()
        regkey_result.first.return_value = None
        mock_async_session.exec.return_value = regkey_result

        result = await validate_regkey("MISSING", mock_async_session)

        assert result["valid"] is False
        assert result["message"] == "注册码不存在"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_regkey_already_used(self, mock_async_session):
        record = RegKey(
            id=1,
            name="AAAAABBBBBCCCCCDDDDDEEEEE",
            ownerid=5,
            status=2,
        )
        regkey_result = MagicMock()
        regkey_result.first.return_value = record
        mock_async_session.exec.return_value = regkey_result

        result = await validate_regkey(record.name, mock_async_session)

        assert result["valid"] is False
        assert result["message"] == "注册码已被使用"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_regkey_success(self, mock_async_session):
        record = RegKey(
            id=1,
            name="AAAAABBBBBCCCCCDDDDDEEEEE",
            ownerid=5,
            status=1,
        )
        regkey_result = MagicMock()
        regkey_result.first.return_value = record
        mock_async_session.exec.return_value = regkey_result

        result = await validate_regkey(record.name, mock_async_session)

        assert result["valid"] is True
        assert result["regkey_id"] == 1
        assert result["owner_id"] == 5


class TestRegKeyUse:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_use_regkey_requires_login(self, mock_async_session):
        with pytest.raises(HTTPException) as exc_info:
            await use_regkey(1, 5, mock_async_session, current_user=None)

        assert exc_info.value.status_code == 401

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_use_regkey_not_found(self, mock_async_session):
        regkey_result = MagicMock()
        regkey_result.first.return_value = None
        mock_async_session.exec.return_value = regkey_result

        with pytest.raises(HTTPException) as exc_info:
            await use_regkey(
                1,
                5,
                mock_async_session,
                current_user={"id": 5, "state": 1},
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_use_regkey_already_used(self, mock_async_session):
        record = RegKey(
            id=1,
            name="AAAAABBBBBCCCCCDDDDDEEEEE",
            ownerid=5,
            status=2,
        )
        regkey_result = MagicMock()
        regkey_result.first.return_value = record
        mock_async_session.exec.return_value = regkey_result

        with pytest.raises(HTTPException) as exc_info:
            await use_regkey(
                1,
                5,
                mock_async_session,
                current_user={"id": 5, "state": 1},
            )

        assert exc_info.value.status_code == 404
        assert "已被使用" in exc_info.value.detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_use_regkey_success(self, mock_async_session):
        record = RegKey(
            id=1,
            name="AAAAABBBBBCCCCCDDDDDEEEEE",
            ownerid=5,
            status=1,
        )
        regkey_result = MagicMock()
        regkey_result.first.return_value = record
        mock_async_session.exec.return_value = regkey_result

        result = await use_regkey(
            1,
            9,
            mock_async_session,
            current_user={"id": 9, "state": 1},
        )

        assert result["message"] == "注册码使用成功"
        assert record.status == 2
        assert record.userid == 9
        mock_async_session.add.assert_called_once_with(record)
        mock_async_session.commit.assert_awaited_once()
