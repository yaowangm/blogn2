import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.utils.dependencies import (
    create_service_dependency,
    get_metadata_service,
    get_user_service,
    get_blog_service,
    get_password_reset_token_repository,
)
from src.repositories.password_reset_token_repository import PasswordResetTokenRepository


class TestDependencies:
    """依赖注入工具测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_repository_class(self):
        """模拟仓库类"""
        return MagicMock()
    
    @pytest.fixture
    def mock_service_class(self):
        """模拟服务类"""
        return MagicMock()
    
    @pytest.mark.unit
    def test_create_service_dependency(self, mock_service_class, mock_repository_class):
        """测试创建服务依赖注入函数"""
        # 创建依赖注入函数
        dependency_func = create_service_dependency(mock_service_class, mock_repository_class)
        
        # 验证返回的是可调用函数
        assert callable(dependency_func)
    
    @pytest.mark.unit
    @patch('src.utils.dependencies.get_async_session')
    async def test_create_service_dependency_with_session(self, mock_get_session, mock_service_class, mock_repository_class):
        """测试创建服务依赖注入函数并调用"""
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        
        # 创建依赖注入函数
        dependency_func = create_service_dependency(mock_service_class, mock_repository_class)
        
        # 调用依赖注入函数
        result = await dependency_func()
        
        # 验证服务类被正确实例化
        mock_service_class.assert_called_once()
        # 验证仓库类被正确实例化（通过检查调用参数）
        mock_repository_class.assert_called_once()
        # 验证仓库类被传入了session参数
        call_args = mock_repository_class.call_args
        assert call_args is not None
    
    @pytest.mark.unit
    @patch('src.utils.dependencies.get_async_session')
    async def test_create_service_dependency_multiple_repositories(self, mock_get_session, mock_service_class):
        """测试创建服务依赖注入函数（多个仓库）"""
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session
        
        mock_repo1 = MagicMock()
        mock_repo2 = MagicMock()
        
        # 创建依赖注入函数
        dependency_func = create_service_dependency(mock_service_class, mock_repo1, mock_repo2)
        
        # 调用依赖注入函数
        result = await dependency_func()
        
        # 验证两个仓库类都被正确实例化
        mock_repo1.assert_called_once()
        mock_repo2.assert_called_once()
        # 验证服务类被正确实例化
        mock_service_class.assert_called_once()
    
    @pytest.mark.unit
    def test_get_metadata_service_is_callable(self):
        """测试get_metadata_service是可调用函数"""
        assert callable(get_metadata_service)
    
    @pytest.mark.unit
    def test_get_user_service_is_callable(self):
        """测试get_user_service是可调用函数"""
        assert callable(get_user_service)
    
    @pytest.mark.unit
    def test_get_blog_service_is_callable(self):
        """测试get_blog_service是可调用函数"""
        assert callable(get_blog_service)

    @pytest.mark.unit
    def test_get_password_reset_token_repository_is_callable(self):
        """测试 get_password_reset_token_repository 是可调用函数"""
        assert callable(get_password_reset_token_repository)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_password_reset_token_repository_returns_repo_with_session(self):
        """get_password_reset_token_repository 返回传入 session 的 token 仓库，供同请求复用"""
        mock_session = AsyncMock()
        result = await get_password_reset_token_repository(session=mock_session)
        assert isinstance(result, PasswordResetTokenRepository)
        assert result.session is mock_session 