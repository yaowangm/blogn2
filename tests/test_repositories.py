import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel.ext.asyncio.session import AsyncSession
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.database import User, ProjectItem

class TestUserRepository:
    """测试用户仓库"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = MagicMock(spec=AsyncSession)
        session.exec = AsyncMock()
        return session
    
    @pytest.fixture
    def user_repository(self, mock_session):
        """创建用户仓库实例"""
        return UserRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_count_success(self, user_repository, mock_session):
        """测试成功获取用户总数"""
        mock_result = MagicMock()
        mock_result.first.return_value = 100
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.count()
        
        assert result == 100
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_empty(self, user_repository, mock_session):
        """测试获取用户总数时返回0"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.count()
        
        assert result == 0
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository, mock_session):
        """测试成功根据ID获取用户"""
        mock_user = User(id=1, name="testuser", email="test@example.com")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_user
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_id(1)
        
        assert result == mock_user
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository, mock_session):
        """测试获取不存在的用户"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_id(999)
        
        assert result is None
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_email_success(self, user_repository, mock_session):
        """测试成功根据邮箱获取用户"""
        mock_user = User(id=1, name="testuser", email="test@example.com")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_user
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_email("test@example.com")
        
        assert result == mock_user
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_name_success(self, user_repository, mock_session):
        """测试成功根据用户名获取用户"""
        mock_user = User(id=1, name="testuser", email="test@example.com")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_user
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_name("testuser")
        
        assert result == mock_user
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_users_success(self, user_repository, mock_session):
        """测试成功获取活跃用户"""
        mock_users = [
            User(id=1, name="user1", email="user1@example.com"),
            User(id=2, name="user2", email="user2@example.com")
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_active_users(limit=2)
        
        assert len(result) == 2
        assert result[0].name == "user1"
        assert result[1].name == "user2"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_users_no_limit(self, user_repository, mock_session):
        """测试获取活跃用户时不限制数量"""
        mock_users = [User(id=1, name="user1", email="user1@example.com")]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_active_users()
        
        assert len(result) == 1
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_users_success(self, user_repository, mock_session):
        """测试成功获取最新用户"""
        mock_users = [
            User(id=1, name="user1", email="user1@example.com"),
            User(id=2, name="user2", email="user2@example.com")
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_recent_users(limit=2)
        
        assert len(result) == 2
        assert result[0].name == "user1"
        assert result[1].name == "user2"
        mock_session.exec.assert_called_once()

class TestProjectItemRepository:
    """测试项目条目仓库"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = MagicMock(spec=AsyncSession)
        session.exec = AsyncMock()
        return session
    
    @pytest.fixture
    def project_repository(self, mock_session):
        """创建项目条目仓库实例"""
        return ProjectItemRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_count_success(self, project_repository, mock_session):
        """测试成功获取项目条目总数"""
        mock_result = MagicMock()
        mock_result.first.return_value = 50
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.count()
        
        assert result == 50
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, project_repository, mock_session):
        """测试成功根据ID获取项目条目"""
        mock_item = ProjectItem(id=1, name="测试项目", comment="描述")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_item
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_by_id(1)
        
        assert result == mock_item
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_items_success(self, project_repository, mock_session):
        """测试成功获取最近项目条目"""
        mock_items = [
            ProjectItem(id=1, name="项目1", comment="描述1"),
            ProjectItem(id=2, name="项目2", comment="描述2")
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_items
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_recent_items(limit=2)
        
        assert len(result) == 2
        assert result[0].name == "项目1"
        assert result[1].name == "项目2"
        mock_session.exec.assert_called_once() 