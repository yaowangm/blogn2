import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import select, func
from src.repositories.user_repository import UserRepository
from src.models.user import User


class TestUserRepository:
    """UserRepository单元测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def user_repository(self, mock_session):
        """创建UserRepository实例"""
        return UserRepository(mock_session)
    
    @pytest.fixture
    def sample_user(self):
        """示例用户数据"""
        from datetime import datetime
        user = User(
            id=1,
            name="testuser",
            email="test@example.com",
            state=1,
            point=100,
            regtime=datetime(2023, 1, 1, 10, 0, 0)
        )
        return user
    
    @pytest.mark.unit
    def test_init(self, mock_session):
        """测试UserRepository初始化"""
        repo = UserRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.unit
    async def test_count_success(self, user_repository, mock_session):
        """测试获取用户总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 150
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.count()
        
        assert result == 150
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_count_zero(self, user_repository, mock_session):
        """测试获取用户总数为0"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.count()
        
        assert result == 0
    
    @pytest.mark.unit
    async def test_get_by_id_success(self, user_repository, mock_session, sample_user):
        """测试根据ID获取用户成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_user
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_id(1)
        
        assert result == sample_user
        assert result.id == 1
        assert result.name == "testuser"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_id_not_found(self, user_repository, mock_session):
        """测试根据ID获取用户不存在"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_id(999)
        
        assert result is None
    
    @pytest.mark.unit
    async def test_get_by_email_success(self, user_repository, mock_session, sample_user):
        """测试根据邮箱获取用户成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_user
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_email("test@example.com")
        
        assert result == sample_user
        assert result.email == "test@example.com"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_email_not_found(self, user_repository, mock_session):
        """测试根据邮箱获取用户不存在"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_email("nonexistent@example.com")
        
        assert result is None
    
    @pytest.mark.unit
    async def test_get_by_name_success(self, user_repository, mock_session, sample_user):
        """测试根据用户名获取用户成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_user
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_name("testuser")
        
        assert result == sample_user
        assert result.name == "testuser"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_name_not_found(self, user_repository, mock_session):
        """测试根据用户名获取用户不存在"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_by_name("nonexistent")
        
        assert result is None
    
    @pytest.mark.unit
    async def test_get_active_users_with_limit(self, user_repository, mock_session):
        """测试获取活跃用户（带限制）"""
        users = [
            User(id=1, name="user1", state=1),
            User(id=2, name="user2", state=1),
            User(id=3, name="user3", state=1)
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = users[:2]  # 只返回前2个
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_active_users(limit=2)
        
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_active_users_no_limit(self, user_repository, mock_session):
        """测试获取活跃用户（无限制）"""
        users = [
            User(id=1, name="user1", state=1),
            User(id=2, name="user2", state=1)
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_active_users()
        
        assert len(result) == 2
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_active_users_empty(self, user_repository, mock_session):
        """测试获取活跃用户为空"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_active_users()
        
        assert len(result) == 0
    
    @pytest.mark.unit
    async def test_get_recent_users_success(self, user_repository, mock_session):
        """测试获取最近注册用户成功"""
        from datetime import datetime
        users = [
            User(id=1, name="user1", regtime=datetime(2023, 1, 3, 10, 0, 0)),
            User(id=2, name="user2", regtime=datetime(2023, 1, 2, 10, 0, 0)),
            User(id=3, name="user3", regtime=datetime(2023, 1, 1, 10, 0, 0))
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_recent_users(limit=3)
        
        assert len(result) == 3
        assert result[0].id == 1  # 最新的用户
        assert result[2].id == 3  # 最旧的用户
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_recent_users_default_limit(self, user_repository, mock_session):
        """测试获取最近注册用户使用默认限制"""
        from datetime import datetime
        users = [User(id=1, name="user1", regtime=datetime(2023, 1, 1, 10, 0, 0))]
        mock_result = MagicMock()
        mock_result.all.return_value = users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_recent_users()
        
        assert len(result) == 1
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_popular_users_success(self, user_repository, mock_session):
        """测试获取热门用户成功"""
        from datetime import datetime
        mock_users = [
            MagicMock(id=1, name="user1", point=1000, regtime=datetime(2023, 1, 1, 10, 0, 0)),
            MagicMock(id=2, name="user2", point=500, regtime=datetime(2023, 1, 2, 10, 0, 0)),
            MagicMock(id=3, name="user3", point=None, regtime=datetime(2023, 1, 3, 10, 0, 0))
        ]
        # 设置name属性的返回值
        mock_users[0].name = "user1"
        mock_users[1].name = "user2"
        mock_users[2].name = "user3"
        mock_result = MagicMock()
        mock_result.all.return_value = mock_users
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_popular_users(limit=3)
        
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[0]["name"] == "user1"
        assert result[0]["point"] == 1000
        assert result[2]["point"] == 0  # None值转换为0
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_popular_users_empty(self, user_repository, mock_session):
        """测试获取热门用户为空"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result
        
        result = await user_repository.get_popular_users()
        
        assert len(result) == 0 