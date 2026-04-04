import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.dialects import postgresql
from sqlalchemy import update

from src.repositories.project_repository import (
    ProjectRepository,
    _blog_updatetime_from_articles_expr,
)
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.constants import ArticleStatus


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
    def test_sync_updatetime_sql_uses_max_create_max_modify_greatest(self):
        """blog updatetime = GREATEST(MAX(createtime), MAX(lastmodifytime))，不使用 projectitem.updatetime"""
        rhs = _blog_updatetime_from_articles_expr()
        stmt = update(Project).where(Project.id == 7).values(updatetime=rhs)
        compiled = str(
            stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": False},
            )
        ).lower()
        assert "greatest" in compiled
        assert compiled.count("max(") >= 2
        assert "lastmodifytime" in compiled
        assert "projectitem.updatetime" not in compiled
        assert "is null" in compiled
        assert "update project" in compiled

    @pytest.mark.unit
    async def test_sync_updatetime_executes_update_and_refreshes_when_project_passed(
        self, project_repository, mock_session
    ):
        mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))
        mock_session.refresh = AsyncMock()

        project = Project(id=1, name="blog", userid=1)
        project.createtime = datetime(2020, 1, 1)

        await project_repository.sync_updatetime_from_latest_published_article(1, project)

        mock_session.execute.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(
            project, attribute_names=["updatetime"]
        )

    @pytest.mark.unit
    async def test_sync_updatetime_executes_update_only_when_no_project_instance(
        self, project_repository, mock_session
    ):
        mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

        await project_repository.sync_updatetime_from_latest_published_article(1)

        mock_session.execute.assert_awaited_once()
        mock_session.refresh.assert_not_called()

    @pytest.mark.unit
    async def test_sync_updatetime_no_refresh_when_project_row_missing(
        self, project_repository, mock_session
    ):
        """仅传 project_id 时只发 UPDATE，不 refresh"""
        mock_session.execute = AsyncMock(return_value=MagicMock(rowcount=0))

        await project_repository.sync_updatetime_from_latest_published_article(99)

        mock_session.execute.assert_awaited_once()
        mock_session.refresh.assert_not_called()

    @pytest.mark.unit
    async def test_sync_all_projects_updatetime_one_update_and_commit(
        self, project_repository, mock_session
    ):
        mock_result = MagicMock()
        mock_result.rowcount = 42
        mock_session.execute = AsyncMock(return_value=mock_result)

        n = await project_repository.sync_all_projects_updatetime()

        assert n == 42
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()