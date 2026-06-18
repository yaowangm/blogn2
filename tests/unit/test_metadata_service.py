import pytest
from unittest.mock import AsyncMock
from src.services.metadata_service import MetadataService


class TestMetadataService:
    """MetadataService单元测试类"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """模拟用户仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_post_repo(self):
        """模拟博文仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def metadata_service(self, mock_user_repo, mock_post_repo):
        """创建MetadataService实例"""
        return MetadataService(mock_user_repo, mock_post_repo)
    
    @pytest.mark.unit
    def test_init(self, mock_user_repo, mock_post_repo):
        """测试MetadataService初始化"""
        service = MetadataService(mock_user_repo, mock_post_repo)
        
        assert service.user_repo == mock_user_repo
        assert service.post_repo == mock_post_repo
    
    @pytest.mark.unit
    async def test_get_metadata_dict_success(self, metadata_service, mock_user_repo, mock_post_repo):
        """测试获取元数据成功"""
        mock_user_repo.count.return_value = 150
        mock_post_repo.count.return_value = 300
        
        result = await metadata_service.get_metadata_dict()
        
        assert result["site_name"] == "BlogN"
        assert result["version"] == "V1"
        assert result["logo_url"] == "/static/favicon.svg"
        assert result["user_count"] == 150
        assert result["post_count"] == 300
        
        mock_user_repo.count.assert_called_once()
        mock_post_repo.count.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_metadata_dict_zero_counts(self, metadata_service, mock_user_repo, mock_post_repo):
        """测试获取元数据时计数为0"""
        mock_user_repo.count.return_value = 0
        mock_post_repo.count.return_value = 0
        
        result = await metadata_service.get_metadata_dict()
        
        assert result["user_count"] == 0
        assert result["post_count"] == 0
    
    @pytest.mark.unit
    async def test_get_metadata_dict_large_counts(self, metadata_service, mock_user_repo, mock_post_repo):
        """测试获取元数据时计数很大"""
        mock_user_repo.count.return_value = 999999
        mock_post_repo.count.return_value = 1234567
        
        result = await metadata_service.get_metadata_dict()
        
        assert result["user_count"] == 999999
        assert result["post_count"] == 1234567 
