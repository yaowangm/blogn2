"""
StatsService 中与 project.updatetime 同步相关的单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.stats_service import StatsService


@pytest.mark.unit
class TestStatsServiceProjectUpdatetime:
    @pytest.mark.asyncio
    async def test_increment_project_record_count_syncs_updatetime(self):
        """增加文章数后应调用 ProjectRepository.sync_updatetime_from_latest_published_article"""
        session = AsyncMock()
        mock_project = MagicMock()
        mock_project.recordcount = 0
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = mock_project
        session.exec = AsyncMock(return_value=mock_exec_result)

        with patch("src.services.stats_service.ProjectRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.sync_updatetime_from_latest_published_article = AsyncMock()
            mock_repo_class.return_value = mock_repo

            service = StatsService(session)
            ok = await service.increment_project_record_count(42)

        assert ok is True
        assert mock_project.recordcount == 1
        mock_repo.sync_updatetime_from_latest_published_article.assert_called_once_with(
            42, mock_project
        )
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_decrement_project_record_count_syncs_updatetime(self):
        """减少文章数后应同步博客 updatetime"""
        session = AsyncMock()
        mock_project = MagicMock()
        mock_project.recordcount = 2
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = mock_project
        session.exec = AsyncMock(return_value=mock_exec_result)

        with patch("src.services.stats_service.ProjectRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.sync_updatetime_from_latest_published_article = AsyncMock()
            mock_repo_class.return_value = mock_repo

            service = StatsService(session)
            ok = await service.decrement_project_record_count(7)

        assert ok is True
        assert mock_project.recordcount == 1
        mock_repo.sync_updatetime_from_latest_published_article.assert_called_once_with(
            7, mock_project
        )
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_increment_project_comment_count_does_not_instantiate_project_repo_for_sync(self):
        """评论数变化不应通过 ProjectRepository 同步博客 updatetime"""
        session = AsyncMock()
        mock_project = MagicMock()
        mock_project.commentcount = 1
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = mock_project
        session.exec = AsyncMock(return_value=mock_exec_result)

        with patch("src.services.stats_service.ProjectRepository") as mock_repo_class:
            service = StatsService(session)
            ok = await service.increment_project_comment_count(3)

        assert ok is True
        mock_repo_class.assert_not_called()
