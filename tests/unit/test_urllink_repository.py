"""
友情链接仓库单元测试

测试UrlLinkRepository的各种方法
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import select
from src.repositories.urllink_repository import UrlLinkRepository
from src.models.urllink import UrlLink


class TestUrlLinkRepository:
    """友情链接仓库测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        session.exec = AsyncMock()
        return session

    @pytest.fixture
    def mock_url_links(self):
        """模拟友情链接列表"""
        return [
            UrlLink(
                id=1,
                subject="测试链接1",
                linkstr="https://example1.com",
                projectid=1,
                ordernum=1
            ),
            UrlLink(
                id=2,
                subject="测试链接2",
                linkstr="https://example2.com",
                projectid=1,
                ordernum=2
            ),
            UrlLink(
                id=3,
                subject="测试链接3",
                linkstr="https://example3.com",
                projectid=1,
                ordernum=3
            )
        ]

    @pytest.mark.asyncio
    async def test_get_friend_links_by_project_success(self, mock_session, mock_url_links):
        """测试成功获取指定项目的友情链接"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = mock_url_links
        mock_session.exec.return_value = mock_result

        # 执行测试
        repo = UrlLinkRepository(mock_session)
        result = await repo.get_friend_links_by_project(1)

        # 验证结果
        assert len(result) == 3
        assert result[0].subject == "测试链接1"
        assert result[0].linkstr == "https://example1.com"
        assert result[0].ordernum == 1
        assert result[1].subject == "测试链接2"
        assert result[2].subject == "测试链接3"

        # 验证方法调用
        mock_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_friend_links_by_project_empty(self, mock_session):
        """测试获取空友情链接列表"""
        # 模拟空结果
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        # 执行测试
        repo = UrlLinkRepository(mock_session)
        result = await repo.get_friend_links_by_project(1)

        # 验证结果
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_all_friend_links_success(self, mock_session, mock_url_links):
        """测试成功获取所有友情链接"""
        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = mock_url_links
        mock_session.exec.return_value = mock_result

        # 执行测试
        repo = UrlLinkRepository(mock_session)
        result = await repo.get_all_friend_links()

        # 验证结果
        assert len(result) == 3
        assert result[0].subject == "测试链接1"
        assert result[0].linkstr == "https://example1.com"
        assert result[1].subject == "测试链接2"
        assert result[2].subject == "测试链接3"

        # 验证方法调用
        mock_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_friend_links_empty(self, mock_session):
        """测试获取空友情链接列表"""
        # 模拟空结果
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        # 执行测试
        repo = UrlLinkRepository(mock_session)
        result = await repo.get_all_friend_links()

        # 验证结果
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_all_friend_links_limit(self, mock_session):
        """测试友情链接数量限制"""
        # 模拟超过限制的结果
        many_links = [
            UrlLink(id=i, subject=f"链接{i}", linkstr=f"https://example{i}.com", ordernum=i)
            for i in range(1, 15)  # 14个链接
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = many_links[:10]  # 只返回前10个
        mock_session.exec.return_value = mock_result

        # 执行测试
        repo = UrlLinkRepository(mock_session)
        result = await repo.get_all_friend_links()

        # 验证结果
        assert len(result) == 10
        assert result[0].id == 1
        assert result[9].id == 10
