import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.metadata_service import MetadataService
from src.services.user_service import UserService
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository

class TestMetadataService:
    """测试元数据服务"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """模拟用户仓库"""
        repo = MagicMock(spec=UserRepository)
        repo.count = AsyncMock(return_value=100)
        return repo
    
    @pytest.fixture
    def mock_project_repo(self):
        """模拟项目仓库"""
        repo = MagicMock(spec=ProjectItemRepository)
        repo.count = AsyncMock(return_value=50)
        return repo
    
    @pytest.fixture
    def metadata_service(self, mock_user_repo, mock_project_repo):
        """创建元数据服务实例"""
        return MetadataService(mock_user_repo, mock_project_repo)
    
    @pytest.mark.asyncio
    async def test_get_metadata_dict_success(self, metadata_service, mock_user_repo, mock_project_repo):
        """测试成功获取元数据字典"""
        result = await metadata_service.get_metadata_dict()
        
        assert isinstance(result, dict)
        assert "user_count" in result
        assert "post_count" in result
        assert result["user_count"] == 100
        assert result["post_count"] == 50
        
        # 验证方法被调用
        mock_user_repo.count.assert_called_once()
        mock_project_repo.count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_metadata_dict_with_error(self, mock_user_repo, mock_project_repo):
        """测试获取元数据时发生错误"""
        mock_user_repo.count = AsyncMock(side_effect=Exception("数据库错误"))
        
        metadata_service = MetadataService(mock_user_repo, mock_project_repo)
        
        with pytest.raises(Exception, match="数据库错误"):
            await metadata_service.get_metadata_dict()

class TestUserService:
    """测试用户服务"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """模拟用户仓库"""
        repo = MagicMock(spec=UserRepository)
        return repo
    
    @pytest.fixture
    def user_service(self, mock_user_repo):
        """创建用户服务实例"""
        return UserService(mock_user_repo)
    
    @pytest.mark.asyncio
    async def test_get_user_summary_success(self, user_service, mock_user_repo):
        """测试成功获取用户统计信息"""
        mock_user_repo.count = AsyncMock(return_value=100)
        mock_user_repo.get_recent_users = AsyncMock(return_value=[MagicMock() for _ in range(3)])
        
        result = await user_service.get_user_summary()
        
        assert isinstance(result, dict)
        assert "total_users" in result
        assert "recent_users" in result
        assert result["total_users"] == 100
        assert isinstance(result["recent_users"], list)
        
        mock_user_repo.count.assert_called_once()
        mock_user_repo.get_recent_users.assert_called_once_with(3)
    
    @pytest.mark.asyncio
    async def test_get_user_count_success(self, user_service, mock_user_repo):
        """测试成功获取用户总数"""
        mock_user_repo.count = AsyncMock(return_value=150)
        
        result = await user_service.get_user_count()
        
        assert result == 150
        mock_user_repo.count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_users_success(self, user_service, mock_user_repo):
        """测试成功获取最新用户"""
        mock_users = [
            MagicMock(id=1, name="user1", email="user1@example.com"),
            MagicMock(id=2, name="user2", email="user2@example.com")
        ]
        # 设置MagicMock的name属性
        mock_users[0].name = "user1"
        mock_users[1].name = "user2"
        mock_user_repo.get_recent_users = AsyncMock(return_value=mock_users)
        
        result = await user_service.get_recent_users(limit=2)
        
        assert len(result) == 2
        assert result[0].name == "user1"
        assert result[1].name == "user2"
        mock_user_repo.get_recent_users.assert_called_once_with(2)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_repo):
        """测试成功根据ID获取用户"""
        mock_user = MagicMock(id=1, name="testuser", email="test@example.com")
        mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)
        
        result = await user_service.get_user_by_id(1)
        
        assert result == mock_user
        mock_user_repo.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repo):
        """测试获取不存在的用户"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)
        
        result = await user_service.get_user_by_id(999)
        
        assert result is None
        mock_user_repo.get_by_id.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_with_error(self, user_service, mock_user_repo):
        """测试获取用户时发生错误"""
        mock_user_repo.get_by_id = AsyncMock(side_effect=Exception("数据库错误"))
        
        with pytest.raises(Exception, match="数据库错误"):
            await user_service.get_user_by_id(1) 