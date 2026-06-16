"""
认证服务测试
测试JWT令牌生成、验证、密码验证等认证服务功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
import jwt
import hashlib

from src.services.auth_service import AuthService
from src.models.user import User
from src.repositories.user_repository import UserRepository


class TestAuthService:
    """认证服务测试类"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """创建模拟用户仓库"""
        repo = AsyncMock(spec=UserRepository)
        return repo
    
    @pytest.fixture
    def auth_service(self, mock_user_repo):
        """创建认证服务实例"""
        return AuthService(mock_user_repo, "test-secret-key")
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = User()
        user.id = 1
        user.name = "testuser"
        user.email = "test@example.com"
        user.password = "$2b$12$test_hash"  # bcrypt格式
        user.state = 1
        user.lastupdate = datetime.now()
        user.iplog = "127.0.0.1"
        return user
    
    @pytest.fixture
    def admin_user(self):
        """创建管理员用户"""
        user = User()
        user.id = 2
        user.name = "admin"
        user.email = "admin@example.com"
        user.password = "$2b$12$admin_hash"
        user.state = 10
        user.lastupdate = datetime.now()
        user.iplog = "127.0.0.1"
        return user

    def test_init(self, mock_user_repo):
        """测试认证服务初始化"""
        service = AuthService(mock_user_repo, "test-secret")
        
        assert service.user_repo == mock_user_repo
        assert service.secret_key == "test-secret"
        assert service.algorithm == "HS256"
        assert service.access_token_expire_minutes == 30  # 默认值
        assert service.refresh_token_expire_days == 7  # 默认值

    def test_init_with_custom_config(self, mock_user_repo):
        """测试认证服务初始化（自定义配置）"""
        with patch.dict('os.environ', {
            'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
            'REFRESH_TOKEN_EXPIRE_DAYS': '14'
        }):
            service = AuthService(mock_user_repo, "test-secret")
            
            assert service.access_token_expire_minutes == 30
            assert service.refresh_token_expire_days == 14

    def test_verify_password_bcrypt_direct(self, auth_service):
        """测试密码验证 - 直接bcrypt格式"""
        plain_password = "password123"
        bcrypt_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzK5K2"
        
        with patch('src.services.auth_service.bcrypt_verify') as mock_verify:
            mock_verify.return_value = True
            
            result = auth_service.verify_password(plain_password, bcrypt_hash)
            
            assert result is True
            mock_verify.assert_called_once_with(plain_password, bcrypt_hash)

    def test_verify_password_bcrypt_md5_fallback(self, auth_service):
        """测试密码验证 - bcrypt格式，MD5回退"""
        plain_password = "password123"
        bcrypt_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzK5K2"
        md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
        
        with patch('src.services.auth_service.bcrypt_verify') as mock_verify:
            # 第一次调用返回False（直接验证失败）
            # 第二次调用返回True（MD5+bcrypt验证成功）
            mock_verify.side_effect = [False, True]
            
            result = auth_service.verify_password(plain_password, bcrypt_hash)
            
            assert result is True
            assert mock_verify.call_count == 2
            mock_verify.assert_any_call(plain_password, bcrypt_hash)
            mock_verify.assert_any_call(md5_hash, bcrypt_hash)

    def test_verify_password_non_bcrypt_format(self, auth_service):
        """测试密码验证 - 非bcrypt格式"""
        plain_password = "password123"
        non_bcrypt_hash = "some_other_hash_format"
        md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
        
        with patch('src.services.auth_service.bcrypt_verify') as mock_verify:
            mock_verify.return_value = True
            
            result = auth_service.verify_password(plain_password, non_bcrypt_hash)
            
            assert result is True
            mock_verify.assert_called_once_with(md5_hash, non_bcrypt_hash)

    def test_verify_password_failure(self, auth_service):
        """测试密码验证失败"""
        plain_password = "wrong_password"
        bcrypt_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzK5K2"
        md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
        
        with patch('src.services.auth_service.bcrypt_verify') as mock_verify:
            mock_verify.return_value = False
            
            result = auth_service.verify_password(plain_password, bcrypt_hash)
            
            assert result is False
            assert mock_verify.call_count == 2

    @pytest.mark.asyncio
    async def test_authenticate_user_success_by_username(self, auth_service, mock_user_repo, mock_user):
        """测试用户认证成功 - 通过用户名"""
        # 设置模拟返回值
        mock_user_repo.get_by_name.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            result = await auth_service.authenticate_user("testuser", "password123", "127.0.0.1")
            
            assert result == mock_user
            mock_user_repo.get_by_name.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_authenticate_user_success_by_email(self, auth_service, mock_user_repo, mock_user):
        """测试用户认证成功 - 通过邮箱"""
        # 设置模拟返回值
        mock_user_repo.get_by_name.return_value = None
        mock_user_repo.get_by_email.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            result = await auth_service.authenticate_user("test@example.com", "password123", "127.0.0.1")
            
            assert result == mock_user
            mock_user_repo.get_by_name.assert_called_once_with("test@example.com")
            mock_user_repo.get_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_user_repo, mock_user):
        """测试用户认证失败 - 密码错误"""
        # 设置模拟返回值
        mock_user_repo.get_by_name.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=False):
            result = await auth_service.authenticate_user("testuser", "wrong_password", "127.0.0.1")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_user_not_found(self, auth_service, mock_user_repo):
        """测试用户认证失败 - 用户不存在"""
        # 设置模拟返回值
        mock_user_repo.get_by_name.return_value = None
        mock_user_repo.get_by_email.return_value = None
        
        result = await auth_service.authenticate_user("nonexistent", "password123", "127.0.0.1")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_frozen_account(self, auth_service, mock_user_repo):
        """测试用户认证失败 - 账户被冻结"""
        from fastapi import HTTPException
        
        # 创建冻结用户
        frozen_user = User()
        frozen_user.id = 3
        frozen_user.name = "frozen"
        frozen_user.state = 0  # 冻结状态
        
        # 设置模拟返回值
        mock_user_repo.get_by_name.return_value = frozen_user
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.authenticate_user("frozen", "password123", "127.0.0.1")
            
            assert exc_info.value.status_code == 403
            assert "该用户已经被冻结" in str(exc_info.value.detail)

    def test_create_access_token(self, auth_service):
        """测试创建访问令牌"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = auth_service.create_access_token(user_data)
        
        # 验证令牌格式
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 解码令牌验证内容
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded["user_id"] == 1
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_create_refresh_token(self, auth_service):
        """测试创建刷新令牌"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = auth_service.create_refresh_token(user_data)
        
        # 验证令牌格式
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 解码令牌验证内容
        decoded = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded["user_id"] == 1
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"
        assert "exp" in decoded
        assert "iat" in decoded
        assert decoded["type"] == "refresh"

    def test_get_user_from_token_valid(self, auth_service):
        """测试从令牌获取用户信息 - 有效令牌"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = auth_service.create_access_token(user_data)
        result = auth_service.get_user_from_token(token)
        
        # 验证返回的数据结构
        assert result is not None
        assert result["user_id"] == 1
        assert result["username"] == "testuser"
        assert result["role"] == "user"
        assert "exp" in result

    def test_get_user_from_token_invalid(self, auth_service):
        """测试从令牌获取用户信息 - 无效令牌"""
        invalid_token = "invalid.token.here"
        
        result = auth_service.get_user_from_token(invalid_token)
        
        assert result is None

    def test_get_user_from_token_expired(self, auth_service):
        """测试从令牌获取用户信息 - 过期令牌"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        # 创建过期的令牌
        expired_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        payload = {
            **user_data,
            "exp": expired_time,
            "iat": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        expired_token = jwt.encode(payload, auth_service.secret_key, algorithm=auth_service.algorithm)
        
        result = auth_service.get_user_from_token(expired_token)
        
        assert result is None

    def test_refresh_access_token_valid(self, auth_service):
        """测试刷新访问令牌 - 有效刷新令牌"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        refresh_token = auth_service.create_refresh_token(user_data)
        new_access_token = auth_service.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        assert isinstance(new_access_token, str)
        
        # 验证新令牌内容
        decoded = jwt.decode(new_access_token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        assert decoded["user_id"] == 1
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"

    def test_refresh_access_token_invalid(self, auth_service):
        """测试刷新访问令牌 - 无效刷新令牌"""
        invalid_token = "invalid.refresh.token"
        
        result = auth_service.refresh_access_token(invalid_token)
        
        assert result is None

    def test_refresh_access_token_wrong_type(self, auth_service):
        """测试刷新访问令牌 - 错误的令牌类型"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        # 创建访问令牌（不是刷新令牌）
        access_token = auth_service.create_access_token(user_data)
        
        result = auth_service.refresh_access_token(access_token)
        
        assert result is None

    def test_refresh_access_token_expired(self, auth_service):
        """测试刷新访问令牌 - 过期刷新令牌"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        # 创建过期的刷新令牌
        expired_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        payload = {
            **user_data,
            "type": "refresh",
            "exp": expired_time,
            "iat": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        expired_refresh_token = jwt.encode(payload, auth_service.secret_key, algorithm=auth_service.algorithm)
        
        result = auth_service.refresh_access_token(expired_refresh_token)
        
        assert result is None

    def test_token_expiration_times(self, auth_service):
        """测试令牌过期时间设置"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(user_data)
        access_decoded = jwt.decode(access_token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        
        # 创建刷新令牌
        refresh_token = auth_service.create_refresh_token(user_data)
        refresh_decoded = jwt.decode(refresh_token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        
        # 验证令牌包含过期时间
        assert "exp" in access_decoded
        assert "exp" in refresh_decoded
        
        # 验证过期时间在未来
        access_exp = datetime.fromtimestamp(access_decoded["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_decoded["exp"])
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        assert access_exp > now
        assert refresh_exp > now
        
        # 验证刷新令牌过期时间比访问令牌长
        assert refresh_exp > access_exp

    def test_different_algorithm(self, mock_user_repo):
        """测试不同算法"""
        service = AuthService(mock_user_repo, "test-secret", "HS512")
        
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = service.create_access_token(user_data)
        
        # 验证令牌可以用相同算法解码
        decoded = jwt.decode(token, service.secret_key, algorithms=[service.algorithm])
        assert decoded["user_id"] == 1

    def test_secret_key_validation(self, mock_user_repo):
        """测试密钥验证"""
        # 使用不同的密钥创建和验证令牌
        service1 = AuthService(mock_user_repo, "secret1")
        service2 = AuthService(mock_user_repo, "secret2")
        
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "role": "user"
        }
        
        token = service1.create_access_token(user_data)
        
        # 使用不同密钥应该无法解码
        result = service2.get_user_from_token(token)
        assert result is None
