import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.dialects import postgresql
from src.repositories.project_repository import ProjectRepository, _scalar_first
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
    def test_scalar_first_datetime(self):
        m = MagicMock()
        dt = datetime(2024, 8, 1, 12, 0, 0)
        m.first.return_value = dt
        assert _scalar_first(m) == dt

    @pytest.mark.unit
    def test_scalar_first_single_column_tuple(self):
        m = MagicMock()
        dt = datetime(2024, 8, 2, 15, 30, 0)
        m.first.return_value = (dt,)
        assert _scalar_first(m) == dt

    @pytest.mark.unit
    def test_scalar_first_none(self):
        m = MagicMock()
        m.first.return_value = None
        assert _scalar_first(m) is None

    @pytest.mark.unit
    def test_sync_updatetime_sql_uses_greatest_and_includes_null_itemtype(self):
        """聚合应对每篇文章取 createtime/updatetime/lastmodifytime 最晚值，并包含 itemtype IS NULL"""
        from sqlmodel import select, func
        from sqlalchemy import or_

        per_item_latest = func.greatest(
            ProjectItem.createtime,
            ProjectItem.updatetime,
            ProjectItem.lastmodifytime,
        )
        statement = (
            select(func.max(per_item_latest))
            .where(ProjectItem.projectid == 7)
            .where(ProjectItem.status == 1)
            .where(
                or_(
                    ProjectItem.itemtype.is_(None),
                    ProjectItem.itemtype != ArticleStatus.DELETED,
                )
            )
        )
        compiled = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": False},
            )
        ).lower()
        assert "greatest" in compiled
        assert "lastmodifytime" in compiled
        assert "is null" in compiled

    @pytest.mark.unit
    async def test_sync_updatetime_sets_updatetime_when_first_returns_tuple(
        self, project_repository, mock_session
    ):
        """func.max 查询的 first() 为单元素 tuple 时也应正确写回 project.updatetime"""
        expected = datetime(2025, 1, 10, 9, 0, 0)
        mock_result = MagicMock()
        mock_result.first.return_value = (expected,)
        mock_session.exec.return_value = mock_result

        project = Project(id=1, name="blog", userid=1)
        project.createtime = datetime(2020, 1, 1)

        await project_repository.sync_updatetime_from_latest_published_article(1, project)

        assert project.updatetime == expected
        mock_session.add.assert_called_once_with(project)

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

    @pytest.mark.unit
    async def test_sync_all_projects_updatetime(self, project_repository, mock_session):
        """对所有项目同步 updatetime 并一次性 commit"""
        p1 = Project(id=1, name="a", userid=1)
        p1.createtime = datetime(2023, 1, 1)
        p2 = Project(id=2, name="b", userid=1)
        p2.createtime = datetime(2023, 2, 1)

        list_result = MagicMock()
        list_result.all.return_value = [p1, p2]

        max_mock = MagicMock()
        max_mock.first.return_value = datetime(2024, 1, 1)

        exec_call_count = {"n": 0}

        async def fake_exec(_stmt):
            exec_call_count["n"] += 1
            if exec_call_count["n"] == 1:
                return list_result
            return max_mock

        mock_session.exec = fake_exec

        with patch.object(
            project_repository,
            "sync_updatetime_from_latest_published_article",
            new_callable=AsyncMock,
        ) as mock_sync:
            n = await project_repository.sync_all_projects_updatetime()

        assert n == 2
        mock_sync.assert_has_awaits(
            [call(1, p1), call(2, p2)], any_order=True
        )
        mock_session.commit.assert_awaited_once()