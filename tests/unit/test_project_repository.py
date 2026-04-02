import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from src.repositories.project_repository import ProjectRepository
from src.models.project import Project


class TestProjectRepository:
    """ProjectRepository单元测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def project_repository(self, mock_session):
        """创建ProjectRepository实例"""
        return ProjectRepository(mock_session)
    
    @pytest.fixture
    def sample_project(self):
        """示例项目数据"""
        project = Project(
            id=1,
            name="测试项目",
            userid=123,
            createtime="2023-01-01 10:00:00",
            accesscount=1500,
            author_name="测试作者"
        )
        return project
    
    @pytest.mark.unit
    def test_init(self, mock_session):
        """测试ProjectRepository初始化"""
        repo = ProjectRepository(mock_session)
        assert repo.session == mock_session
    
    @pytest.mark.unit
    async def test_get_recent_projects_success(self, project_repository, mock_session):
        """测试获取最新项目成功"""
        # 模拟返回元组列表
        mock_result = MagicMock()
        mock_result.all.return_value = [(1, "测试项目", "2023-01-01 10:00:00", 123, "测试作者")]
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_recent_projects(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "测试项目"
        assert result[0]["userid"] == 123
        assert result[0]["author_name"] == "测试作者"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_popular_projects_success(self, project_repository, mock_session):
        """测试获取热门项目成功"""
        # 模拟返回元组列表
        mock_result = MagicMock()
        mock_result.all.return_value = [(1, "测试项目", 1500, 123, "2023-01-01 10:00:00", "测试作者")]
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_popular_projects(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "测试项目"
        assert result[0]["accesscount"] == 1500
        assert result[0]["userid"] == 123
        assert result[0]["author_name"] == "测试作者"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_count_success(self, project_repository, mock_session):
        """测试获取项目总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 100
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.count()
        
        assert result == 100
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_id_success(self, project_repository, mock_session, sample_project):
        """测试根据ID获取项目成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_project
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_by_id(1)
        
        assert result == sample_project
        assert result.id == 1
        assert result.name == "测试项目"
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_id_not_found(self, project_repository, mock_session):
        """测试根据ID获取项目不存在"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_by_id(999)
        
        assert result is None
    
    @pytest.mark.unit
    async def test_get_by_user_id_with_limit(self, project_repository, mock_session, sample_project):
        """测试根据用户ID获取项目（带限制）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project]
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_by_user_id(123, limit=5)
        
        assert len(result) == 1
        assert result[0] == sample_project
        mock_session.exec.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_by_user_id_no_limit(self, project_repository, mock_session, sample_project):
        """测试根据用户ID获取项目（无限制）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_project]
        mock_session.exec.return_value = mock_result
        
        result = await project_repository.get_by_user_id(123)
        
        assert len(result) == 1
        assert result[0] == sample_project
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    async def test_sync_updatetime_uses_max_coalesce_from_published_articles(
        self, project_repository, mock_session
    ):
        """sync_updatetime_from_latest_published_article 使用聚合查询结果更新 project.updatetime"""
        max_ts = datetime(2024, 6, 15, 12, 0, 0)
        mock_result = MagicMock()
        mock_result.first.return_value = max_ts
        mock_session.exec.return_value = mock_result

        project = Project(id=1, name="blog", userid=1)
        project.createtime = datetime(2023, 1, 1, 10, 0, 0)
        project.updatetime = datetime(2023, 1, 2, 10, 0, 0)

        await project_repository.sync_updatetime_from_latest_published_article(1, project)

        assert project.updatetime == max_ts
        mock_session.add.assert_called_once_with(project)

    @pytest.mark.unit
    async def test_sync_updatetime_fallback_to_project_createtime_when_no_posts(
        self, project_repository, mock_session
    ):
        """无已发布文章时，project.updatetime 回退为 project.createtime"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        ct = datetime(2022, 3, 1, 8, 0, 0)
        project = Project(id=2, name="blog", userid=1)
        project.createtime = ct

        await project_repository.sync_updatetime_from_latest_published_article(2, project)

        assert project.updatetime == ct
        mock_session.add.assert_called_once_with(project)

    @pytest.mark.unit
    async def test_sync_updatetime_noop_when_project_row_missing(
        self, project_repository, mock_session
    ):
        """项目不存在时不应写入 session"""
        mock_result = MagicMock()
        mock_result.first.return_value = datetime(2024, 1, 1)
        mock_session.exec.return_value = mock_result

        with patch.object(project_repository, "get_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            await project_repository.sync_updatetime_from_latest_published_article(99)
            mock_session.add.assert_not_called()