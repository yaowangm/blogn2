"""
密码重置服务单元测试

测试 PasswordResetService：申请重置、执行重置、校验 token。
发信通过 mock，不依赖真实 SMTP/sendmail。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.services.password_reset_service import PasswordResetService
from src.models.user import User
from src.models.password_reset_token import PasswordResetToken


class TestPasswordResetService:
    """PasswordResetService 单元测试"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_service(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_token_repo, mock_auth_service):
        return PasswordResetService(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            auth_service=mock_auth_service,
        )

    @pytest.fixture
    def sample_user(self):
        user = User()
        user.id = 1
        user.name = "testuser"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def sample_token_record(self):
        return PasswordResetToken(
            id=1,
            user_id=1,
            token="abc123token",
            expires_at=datetime.utcnow() + timedelta(minutes=60),
        )

    @pytest.mark.asyncio
    @patch("src.services.password_reset_service.send_password_reset_email")
    @patch("src.services.password_reset_service.get_reset_link_expire_minutes", return_value=60)
    @patch("src.services.password_reset_service.get_base_url", return_value="https://blog.example.com")
    async def test_request_reset_user_exists_sends_email(
        self, mock_base_url, mock_expire_minutes, mock_send_email, service, mock_user_repo, mock_token_repo, sample_user
    ):
        """申请重置：邮箱已注册时创建 token、发邮件"""
        mock_user_repo.get_by_email.return_value = sample_user
        created_record = MagicMock()
        created_record.token = "generated_token_xyz"
        mock_token_repo.create.return_value = created_record

        with patch("src.services.password_reset_service.secrets") as mock_secrets:
            mock_secrets.token_urlsafe.return_value = "generated_token_xyz"
            await service.request_reset("test@example.com")

        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_token_repo.create.assert_called_once()
        call_kw = mock_token_repo.create.call_args[1]
        assert call_kw["user_id"] == 1
        assert call_kw["token"] == "generated_token_xyz"
        assert call_kw["expires_at"] is not None

        mock_send_email.assert_called_once_with(
            to_email="test@example.com",
            reset_link="https://blog.example.com/reset-password?token=generated_token_xyz",
            username="testuser",
        )

    @pytest.mark.asyncio
    async def test_request_reset_user_not_exists_no_email_no_raise(
        self, service, mock_user_repo, mock_token_repo
    ):
        """申请重置：邮箱未注册时不发邮件、不抛异常（防枚举）"""
        mock_user_repo.get_by_email.return_value = None

        await service.request_reset("nobody@example.com")

        mock_user_repo.get_by_email.assert_called_once_with("nobody@example.com")
        mock_token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.password_reset_service.send_password_reset_email")
    @patch("src.services.password_reset_service.get_reset_link_expire_minutes", return_value=60)
    @patch("src.services.password_reset_service.get_base_url", return_value="https://blog.example.com")
    async def test_request_reset_email_failure_does_not_raise_no_enumeration(
        self, mock_base_url, mock_expire_minutes, mock_send_email, service, mock_user_repo, mock_token_repo, sample_user
    ):
        """申请重置：发信失败时不抛异常、不创建 token，与未注册邮箱行为一致，防止枚举"""
        mock_user_repo.get_by_email.return_value = sample_user
        mock_send_email.side_effect = RuntimeError("SMTP failed")

        with patch("src.services.password_reset_service.secrets") as mock_secrets:
            mock_secrets.token_urlsafe.return_value = "t"
            await service.request_reset("test@example.com")

        mock_token_repo.create.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.password_reset_service.asyncio.get_event_loop")
    @patch("src.services.password_reset_service.send_password_reset_email")
    @patch("src.services.password_reset_service.get_reset_link_expire_minutes", return_value=60)
    @patch("src.services.password_reset_service.get_base_url", return_value="https://blog.example.com")
    async def test_request_reset_sends_email_via_executor(
        self, mock_base_url, mock_expire_minutes, mock_send_email, mock_get_loop, service, mock_user_repo, mock_token_repo, sample_user
    ):
        """申请重置：发信通过 run_in_executor 执行，不阻塞事件循环"""
        mock_user_repo.get_by_email.return_value = sample_user
        mock_token_repo.create.return_value = MagicMock(token="t")
        run_in_executor = AsyncMock(return_value=None)
        mock_loop = MagicMock()
        mock_loop.run_in_executor = run_in_executor
        mock_get_loop.return_value = mock_loop

        with patch("src.services.password_reset_service.secrets") as mock_secrets:
            mock_secrets.token_urlsafe.return_value = "t"
            await service.request_reset("test@example.com")

        run_in_executor.assert_called_once()
        assert run_in_executor.call_args[0][0] is None
        fn = run_in_executor.call_args[0][1]
        fn()
        mock_send_email.assert_called_once_with(
            to_email="test@example.com",
            reset_link="https://blog.example.com/reset-password?token=t",
            username="testuser",
        )

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, service, mock_user_repo, mock_token_repo, mock_auth_service, sample_token_record
    ):
        """执行重置：合法 token 时通过 update_password_and_delete_token 在同一事务中更新密码并删除 token"""
        mock_token_repo.get_valid_token.return_value = sample_token_record
        mock_auth_service.hash_password.return_value = "hashed_new_pass"
        mock_token_repo.update_password_and_delete_token = AsyncMock()

        await service.reset_password("abc123token", "newpassword123")

        mock_token_repo.get_valid_token.assert_called_once_with("abc123token")
        mock_auth_service.hash_password.assert_called_once_with("newpassword123")
        mock_token_repo.update_password_and_delete_token.assert_called_once_with(
            user_id=1, hashed_password="hashed_new_pass", token="abc123token"
        )

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token_raises(self, service, mock_token_repo):
        """执行重置：无效/过期 token 抛出 ValueError"""
        mock_token_repo.get_valid_token.return_value = None

        with pytest.raises(ValueError, match="链接无效或已过期"):
            await service.reset_password("invalid_token", "newpass")

        mock_token_repo.get_valid_token.assert_called_once_with("invalid_token")
        mock_token_repo.update_password_and_delete_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_password_update_fails_raises(
        self, service, mock_user_repo, mock_token_repo, mock_auth_service, sample_token_record
    ):
        """执行重置：update_password_and_delete_token 失败时抛出 ValueError"""
        mock_token_repo.get_valid_token.return_value = sample_token_record
        mock_auth_service.hash_password.return_value = "hashed"
        mock_token_repo.update_password_and_delete_token = AsyncMock(
            side_effect=ValueError("用户不存在")
        )

        with pytest.raises(ValueError, match="用户不存在"):
            await service.reset_password("abc123token", "newpass")

    @pytest.mark.asyncio
    async def test_is_token_valid_true(self, service, mock_token_repo, sample_token_record):
        """校验 token：有效时返回 True"""
        mock_token_repo.get_valid_token.return_value = sample_token_record

        result = await service.is_token_valid("abc123token")

        assert result is True
        mock_token_repo.get_valid_token.assert_called_once_with("abc123token")

    @pytest.mark.asyncio
    async def test_is_token_valid_false(self, service, mock_token_repo):
        """校验 token：无效或过期时返回 False"""
        mock_token_repo.get_valid_token.return_value = None

        result = await service.is_token_valid("bad_token")

        assert result is False
        mock_token_repo.get_valid_token.assert_called_once_with("bad_token")
