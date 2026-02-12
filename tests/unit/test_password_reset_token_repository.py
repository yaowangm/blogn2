"""
密码重置令牌仓库单元测试

使用 AsyncMock 模拟 session，不依赖真实数据库。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.repositories.password_reset_token_repository import PasswordResetTokenRepository
from src.models.password_reset_token import PasswordResetToken


class TestPasswordResetTokenRepository:
    """PasswordResetTokenRepository 单元测试"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return PasswordResetTokenRepository(mock_session)

    @pytest.fixture
    def sample_record(self):
        return PasswordResetToken(
            id=1,
            user_id=1,
            token="test_token_abc",
            expires_at=datetime.utcnow() + timedelta(minutes=60),
        )

    @pytest.mark.unit
    def test_init(self, mock_session):
        """测试仓库初始化"""
        repo = PasswordResetTokenRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_returns_record(self, repo, mock_session, sample_record):
        """create：插入后 refresh 并返回记录"""
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        result = await repo.create(
            user_id=1,
            token="test_token_abc",
            expires_at=sample_record.expires_at,
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert result.user_id == 1
        assert result.token == "test_token_abc"
        assert result.expires_at == sample_record.expires_at

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_valid_token_found(self, repo, mock_session, sample_record):
        """get_valid_token：存在且未过期时返回记录"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_record
        mock_session.exec.return_value = mock_result

        result = await repo.get_valid_token("test_token_abc")

        assert result == sample_record
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_valid_token_not_found(self, repo, mock_session):
        """get_valid_token：不存在时返回 None"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await repo.get_valid_token("nonexistent")

        assert result is None
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_by_token_deleted(self, repo, mock_session, sample_record):
        """delete_by_token：存在记录时删除并返回 True"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_record
        mock_session.exec.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        result = await repo.delete_by_token("test_token_abc")

        assert result is True
        mock_session.delete.assert_called_once_with(sample_record)
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_by_token_not_found(self, repo, mock_session):
        """delete_by_token：不存在时返回 False"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await repo.delete_by_token("nonexistent")

        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_expired_returns_count(self, repo, mock_session, sample_record):
        """delete_expired：删除过期记录并返回条数"""
        expired = PasswordResetToken(
            id=2,
            user_id=2,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        mock_result = MagicMock()
        mock_result.all.return_value = [expired]
        mock_session.exec.return_value = mock_result
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()

        count = await repo.delete_expired()

        assert count == 1
        mock_session.delete.assert_called_once_with(expired)
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_expired_none_returns_zero(self, repo, mock_session):
        """delete_expired：无过期记录时返回 0"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        count = await repo.delete_expired()

        assert count == 0
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
