import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import select, func
from src.repositories.project_item_repository import ProjectItemRepository
from src.models.project_item import ProjectItem


class TestProjectItemRepository:
    """ProjectItemRepository单元测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def project_item_repository(self, mock_session):
        """创建ProjectItemRepository实例"""
        return ProjectItemRepository(mock_session)
    
    @pytest.fixture
    def sample_project_item(self):
        """示例项目项数据"""
        project_item = ProjectItem(
            id=1,
            name="测试项目项",
            comment="测试内容",
            userid=123,
            createtime="2023-01-01 10:00:00",
            author_name="测试作者",
            attachment="test.jpg"
        )
        return project_item
    
    @pytest.mark.unit
    def test_init(self, mock_session):
        """测试ProjectItemRepository初始化"""
        repo = ProjectItemRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.unit
    async def test_get_by_id_success(self, project_item_repository, mock_session, sample_project_item):
        """测试根据ID获取项目项成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_project_item
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_by_id(1)
        
        assert result == sample_project_item
        assert result.id == 1
        assert result.name == "测试项目项"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_id_not_found(self, project_item_repository, mock_session):
        """测试根据ID获取项目项不存在"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_by_id(999)
        
        assert result is None
    
    @pytest.mark.unit
    async def test_get_latest_posts_success(self, project_item_repository, mock_session, sample_project_item):
        """测试获取最新博文成功"""
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [(sample_project_item, "测试作者", "测试博客")]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_latest_posts(5, None, None, 0)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "测试项目项"
        assert result[0]["comment"] == "测试内容"
        assert result[0]["author_name"] == "测试作者"
        assert result[0]["blog_name"] == "测试博客"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_posts_count_success(self, project_item_repository, mock_session):
        """测试获取博文总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 100
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_posts_count()
        
        assert result == 100
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_posts_count_with_blogid(self, project_item_repository, mock_session):
        """测试获取指定博客的博文总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 25
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_posts_count(blogid=123)
        
        assert result == 25
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_count_success(self, project_item_repository, mock_session):
        """测试获取项目项总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 200
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.count()
        
        assert result == 200
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_user_id_with_limit(self, project_item_repository, mock_session, sample_project_item):
        """测试根据用户ID获取项目项（带限制）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project_item]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_by_user_id(123, limit=5)
        
        assert len(result) == 1
        assert result[0] == sample_project_item
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_user_id_no_limit(self, project_item_repository, mock_session, sample_project_item):
        """测试根据用户ID获取项目项（无限制）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project_item]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_by_user_id(123)
        
        assert len(result) == 1
        assert result[0] == sample_project_item
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_project_id_with_limit(self, project_item_repository, mock_session, sample_project_item):
        """测试根据项目ID获取项目项（带限制）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project_item]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_by_project_id(456, limit=5)
        
        assert len(result) == 1
        assert result[0] == sample_project_item
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_project_id_no_limit(self, project_item_repository, mock_session, sample_project_item):
        """测试根据项目ID获取项目项（无限制）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project_item]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_by_project_id(456)
        
        assert len(result) == 1
        assert result[0] == sample_project_item
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_recent_items_success(self, project_item_repository, mock_session, sample_project_item):
        """测试获取最近创建的项目项成功"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project_item]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_recent_items(5)
        
        assert len(result) == 1
        assert result[0] == sample_project_item
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_popular_items_success(self, project_item_repository, mock_session, sample_project_item):
        """测试获取最受欢迎的项目项成功"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project_item]
        mock_session.exec.return_value = mock_result
        
        result = await project_item_repository.get_popular_items(5)
        
        assert len(result) == 1
        assert result[0] == sample_project_item
        mock_session.exec.assert_called_once() 