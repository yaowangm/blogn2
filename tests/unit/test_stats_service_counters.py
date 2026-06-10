"""
StatsService 计数逻辑单元测试（防重复更新回归）
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.post import Post
from src.models.project_item import ProjectItem
from src.services.stats_service import StatsService


def _exec_result(entity):
    mock = MagicMock()
    mock.first.return_value = entity
    return mock


@pytest.mark.unit
class TestStatsServiceCounters:
    @pytest.mark.asyncio
    async def test_handle_comment_creation_increments_once_per_level(self):
        """博文评论：文章/博客/分类各只 +1"""
        session = AsyncMock()
        article = MagicMock()
        article.projectid = 5
        article.folderid = 9

        comment = Post(
            folderid=0,
            projectitemid=100,
            userid=1,
            content="hi",
            rootid=0,
        )

        call_counts = {"article": 0, "project": 0, "folder": 0}

        async def track_article(article_id):
            call_counts["article"] += 1
            return True

        async def track_project(project_id):
            call_counts["project"] += 1
            return True

        async def track_folder(folder_id):
            call_counts["folder"] += 1
            return True

        service = StatsService(session)
        with patch.object(service, "increment_article_comment_count", side_effect=track_article), patch.object(
            service, "increment_project_comment_count", side_effect=track_project
        ), patch.object(service, "increment_folder_post_count", side_effect=track_folder), patch.object(
            session, "exec", new_callable=AsyncMock, return_value=_exec_result(article)
        ):
            ok = await service.handle_comment_creation(comment)

        assert ok is True
        assert call_counts == {"article": 1, "project": 1, "folder": 1}

    @pytest.mark.asyncio
    async def test_handle_article_creation_increments_project_folder_glovar_once(self):
        """发文：博客 recordcount、分类 recordcount、全局文章数各只 +1"""
        session = AsyncMock()
        article = ProjectItem(
            name="t",
            comment="b",
            projectid=3,
            folderid=7,
            userid=1,
        )

        call_counts = {"project": 0, "folder": 0, "glovar": 0}

        service = StatsService(session)
        with patch.object(
            service, "increment_project_record_count", side_effect=lambda *_: call_counts.__setitem__("project", call_counts["project"] + 1) or True
        ), patch.object(
            service, "increment_folder_record_count", side_effect=lambda *_: call_counts.__setitem__("folder", call_counts["folder"] + 1) or True
        ), patch.object(
            service, "increment_project_item_count", side_effect=lambda: call_counts.__setitem__("glovar", call_counts["glovar"] + 1) or True
        ):
            ok = await service.handle_article_creation(article)

        assert ok is True
        assert call_counts == {"project": 1, "folder": 1, "glovar": 1}

    @pytest.mark.asyncio
    async def test_increment_post_reply_count_sets_lastreplyid(self):
        session = AsyncMock()
        root = MagicMock()
        root.replycount = 0
        session.exec = AsyncMock(return_value=_exec_result(root))

        service = StatsService(session)
        ok = await service.increment_post_reply_count(10, reply_user_id=42)

        assert ok is True
        assert root.replycount == 1
        assert root.lastreplyid == 42
        assert root.lastreplytime is not None

    @pytest.mark.asyncio
    async def test_handle_article_comments_bulk_removal(self):
        session = AsyncMock()
        article = ProjectItem(name="t", comment="b", projectid=1, folderid=2, userid=1)
        deltas = []

        service = StatsService(session)
        with patch.object(
            service,
            "adjust_project_comment_count",
            side_effect=lambda pid, d: deltas.append(("project", pid, d)) or True,
        ), patch.object(
            service,
            "adjust_folder_post_count",
            side_effect=lambda fid, d: deltas.append(("folder", fid, d)) or True,
        ):
            ok = await service.handle_article_comments_bulk_removal(article, 3)

        assert ok is True
        assert deltas == [("project", 1, -3), ("folder", 2, -3)]
