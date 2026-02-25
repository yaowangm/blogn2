"""
用户认证控制器测试
测试登录、登出、令牌刷新、用户信息获取等认证功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from src.controllers.auth import router, get_auth_service
from src.models.auth import (
    LoginRequest,
    TokenRefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.models.user import User


class TestAuthController:
    """认证控制器测试类"""
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = User()
        user.id = 1
        user.name = "testuser"
        user.email = "test@example.com"
        user.state = 10  # 管理员
        user.lastupdate = datetime.now()
        user.iplog = "127.0.0.1"
        return user
    
    @pytest.fixture
    def mock_auth_service(self):
        """创建模拟认证服务"""
        service = AsyncMock(spec=AuthService)
        service.access_token_expire_minutes = 15
        return service
    
    @pytest.fixture
    def mock_user_service(self):
        """创建模拟用户服务"""
        service = AsyncMock(spec=UserService)
        return service
    
    @pytest.fixture
    def login_request(self):
        """创建登录请求"""
        return LoginRequest(
            username_or_email="testuser",
            password="password123"
        )
    
    @pytest.fixture
    def refresh_request(self):
        """创建令牌刷新请求"""
        return TokenRefreshRequest(
            refresh_token="valid_refresh_token"
        )

    @pytest.mark.asyncio
    async def test_login_success(self, mock_user, mock_auth_service, login_request):
        """测试登录成功"""
        # 设置模拟返回值
        mock_auth_service.authenticate_user.return_value = mock_user
        mock_auth_service.create_access_token.return_value = "access_token"
        mock_auth_service.create_refresh_token.return_value = "refresh_token"
        
        # 模拟HTTP请求
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        # 导入并测试登录函数
        from src.controllers.auth import login
        
        result = await login(login_request, mock_auth_service, mock_request)
        
        # 验证结果
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        assert result.token_type == "bearer"
        assert result.expires_in == 900  # 15分钟
        assert result.user["id"] == 1
        assert result.user["name"] == "testuser"
        assert result.user["role"] == "admin"
        
        # 验证服务调用
        mock_auth_service.authenticate_user.assert_called_once_with(
            "testuser", "password123", "127.0.0.1"
        )
        mock_auth_service.create_access_token.assert_called_once()
        mock_auth_service.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_auth_service, login_request):
        """测试登录失败 - 无效凭据"""
        # 设置模拟返回值
        mock_auth_service.authenticate_user.return_value = None
        
        # 模拟HTTP请求
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        # 导入并测试登录函数
        from src.controllers.auth import login
        
        with pytest.raises(HTTPException) as exc_info:
            await login(login_request, mock_auth_service, mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "用户名或密码错误" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, mock_auth_service, refresh_request):
        """测试令牌刷新成功"""
        # 设置模拟返回值
        mock_auth_service.refresh_access_token.return_value = "new_access_token"
        mock_auth_service.get_user_from_token.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "admin"
        }
        mock_auth_service.create_refresh_token.return_value = "new_refresh_token"
        
        # 导入并测试刷新函数
        from src.controllers.auth import refresh_token
        
        result = await refresh_token(refresh_request, mock_auth_service)
        
        # 验证结果
        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"
        assert result.token_type == "bearer"
        assert result.expires_in == 900  # 15分钟
        
        # 验证服务调用
        mock_auth_service.refresh_access_token.assert_called_once_with("valid_refresh_token")
        mock_auth_service.get_user_from_token.assert_called_once_with("new_access_token")
        mock_auth_service.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, mock_auth_service, refresh_request):
        """测试令牌刷新失败 - 无效令牌"""
        # 设置模拟返回值
        mock_auth_service.refresh_access_token.return_value = None
        
        # 导入并测试刷新函数
        from src.controllers.auth import refresh_token
        
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(refresh_request, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "无效的刷新令牌" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_auth_service):
        """测试登出成功"""
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        # 导入并测试登出函数
        from src.controllers.auth import logout
        
        result = await logout(mock_credentials, mock_auth_service)
        
        # 验证结果
        assert result.message == "登出成功"

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user, mock_auth_service, mock_user_service):
        """测试获取当前用户信息成功"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "admin"
        }
        mock_user_service.get_user_by_id.return_value = mock_user
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        # 导入并测试获取用户信息函数
        from src.controllers.auth import get_current_user
        
        result = await get_current_user(mock_credentials, mock_auth_service, mock_user_service)
        
        # 验证结果
        assert result.id == 1
        assert result.name == "testuser"
        assert result.email == "test@example.com"
        assert result.state == 10
        assert result.role == "admin"
        
        # 验证服务调用
        mock_auth_service.get_user_from_token.assert_called_once_with("valid_token")
        mock_user_service.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_auth_service, mock_user_service):
        """测试获取当前用户信息失败 - 无效令牌"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = None
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        # 导入并测试获取用户信息函数
        from src.controllers.auth import get_current_user
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_auth_service, mock_user_service)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "无效的访问令牌" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_auth_service, mock_user_service):
        """测试获取当前用户信息失败 - 用户不存在"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = {
            "user_id": 999,
            "username": "nonexistent",
            "role": "user"
        }
        mock_user_service.get_user_by_id.return_value = None
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        # 导入并测试获取用户信息函数
        from src.controllers.auth import get_current_user
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials, mock_auth_service, mock_user_service)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "用户不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_token_success(self, mock_auth_service):
        """测试令牌验证成功"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "admin",
            "exp": datetime.now() + timedelta(hours=1)
        }
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        # 导入并测试令牌验证函数
        from src.controllers.auth import verify_token
        
        result = await verify_token(mock_credentials, mock_auth_service)
        
        # 验证结果
        assert result["valid"] is True
        assert result["user_id"] == 1
        assert result["username"] == "testuser"
        assert result["role"] == "admin"
        assert "expires_at" in result
        
        # 验证服务调用
        mock_auth_service.get_user_from_token.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, mock_auth_service):
        """测试令牌验证失败"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = None
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        # 导入并测试令牌验证函数
        from src.controllers.auth import verify_token
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "无效的访问令牌" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_token_success(self, mock_auth_service):
        """测试令牌验证（简化版）成功"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = {
            "user_id": 1,
            "username": "testuser",
            "role": "admin"
        }
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid_token"
        
        # 导入并测试令牌验证函数
        from src.controllers.auth import validate_token
        
        result = await validate_token(mock_credentials, mock_auth_service)
        
        # 验证结果
        assert result["valid"] is True
        
        # 验证服务调用
        mock_auth_service.get_user_from_token.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, mock_auth_service):
        """测试令牌验证（简化版）失败"""
        # 设置模拟返回值
        mock_auth_service.get_user_from_token.return_value = None
        
        # 模拟认证凭据
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"
        
        # 导入并测试令牌验证函数
        from src.controllers.auth import validate_token
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_token(mock_credentials, mock_auth_service)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "无效的访问令牌" in str(exc_info.value.detail)

    def test_get_auth_service_dependency(self):
        """测试认证服务依赖注入"""
        # 模拟用户服务
        mock_user_service = MagicMock()
        
        # 测试依赖注入函数
        auth_service = get_auth_service(mock_user_service)
        
        # 验证返回的是AuthService实例
        assert isinstance(auth_service, AuthService)
        assert auth_service.user_repo == mock_user_service.user_repo


class TestPasswordResetController:
    """密码重置接口测试：forgot-password、reset-password、validate-reset-token"""

    @pytest.fixture
    def mock_password_reset_service(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_forgot_password_success(self, mock_password_reset_service):
        """POST /forgot-password：成功时返回统一提示"""
        from src.controllers.auth import forgot_password

        request = ForgotPasswordRequest(email="user@example.com")
        mock_password_reset_service.request_reset.return_value = None

        result = await forgot_password(request, mock_password_reset_service)

        assert result.message == "若该邮箱已注册，将收到重置邮件"
        mock_password_reset_service.request_reset.assert_called_once_with("user@example.com")

    @pytest.mark.asyncio
    async def test_reset_password_success(self, mock_password_reset_service):
        """POST /reset-password：合法 token 时返回成功"""
        from src.controllers.auth import reset_password

        request = ResetPasswordRequest(token="valid_token_xyz", new_password="Newpass123")
        mock_password_reset_service.reset_password.return_value = None

        result = await reset_password(request, mock_password_reset_service)

        assert result.message == "密码重置成功"
        mock_password_reset_service.reset_password.assert_called_once_with("valid_token_xyz", "Newpass123")

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token_returns_400(self, mock_password_reset_service):
        """POST /reset-password：无效 token 时返回 400"""
        from src.controllers.auth import reset_password

        request = ResetPasswordRequest(token="invalid", new_password="Newpass123")
        mock_password_reset_service.reset_password.side_effect = ValueError("链接无效或已过期，请重新申请重置密码")

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(request, mock_password_reset_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "链接无效或已过期" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_reset_token_valid(self, mock_password_reset_service):
        """GET /validate-reset-token：有效 token 返回 valid=true"""
        from src.controllers.auth import validate_reset_token

        mock_password_reset_service.is_token_valid.return_value = True

        result = await validate_reset_token("valid_token", mock_password_reset_service)

        assert result.valid is True
        mock_password_reset_service.is_token_valid.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid(self, mock_password_reset_service):
        """GET /validate-reset-token：无效 token 返回 valid=false"""
        from src.controllers.auth import validate_reset_token

        mock_password_reset_service.is_token_valid.return_value = False

        result = await validate_reset_token("bad_token", mock_password_reset_service)

        assert result.valid is False
        mock_password_reset_service.is_token_valid.assert_called_once_with("bad_token")
