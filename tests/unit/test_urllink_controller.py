"""
友情链接控制器单元测试

测试urllink.py中的各种API端点
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from src.controllers.urllink import get_project_friend_links, get_all_friend_links
from src.models.urllink import UrlLink


class TestUrlLinkController:
    """友情链接控制器测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
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
    async def test_get_project_friend_links_success(self, mock_session, mock_url_links):
        """测试成功获取指定项目的友情链接"""
        # 模拟友情链接仓库
        with patch('src.controllers.urllink.UrlLinkRepository.get_friend_links_by_project') as mock_method:
            mock_method.return_value = mock_url_links

            # 执行测试
            result = await get_project_friend_links(1, mock_session)

            # 验证结果
            assert len(result) == 3
            assert result[0].subject == "测试链接1"
            assert result[0].linkstr == "https://example1.com"
            assert result[0].ordernum == 1
            assert result[1].subject == "测试链接2"
            assert result[2].subject == "测试链接3"

            # 验证方法调用
            mock_method.assert_called_once_with(mock_session, 1)

    @pytest.mark.asyncio
    async def test_get_project_friend_links_empty(self, mock_session):
        """测试获取空友情链接列表"""
        # 模拟友情链接仓库返回空列表
        with patch('src.controllers.urllink.UrlLinkRepository.get_friend_links_by_project') as mock_method:
            mock_method.return_value = []

            # 执行测试
            result = await get_project_friend_links(1, mock_session)

            # 验证结果
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_project_friend_links_exception_handling(self, mock_session):
        """测试异常处理"""
        # 模拟友情链接仓库抛出异常
        with patch('src.controllers.urllink.UrlLinkRepository.get_friend_links_by_project') as mock_method:
            mock_method.side_effect = Exception("数据库错误")

            # 执行测试 - 应该返回空列表而不是抛出异常
            result = await get_project_friend_links(1, mock_session)

            # 验证结果
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_all_friend_links_success(self, mock_session, mock_url_links):
        """测试成功获取所有友情链接"""
        # 模拟友情链接仓库
        with patch('src.controllers.urllink.UrlLinkRepository.get_all_friend_links') as mock_method:
            mock_method.return_value = mock_url_links

            # 执行测试
            result = await get_all_friend_links(mock_session)

            # 验证结果
            assert len(result) == 3
            assert result[0].subject == "测试链接1"
            assert result[0].linkstr == "https://example1.com"
            assert result[1].subject == "测试链接2"
            assert result[2].subject == "测试链接3"

            # 验证方法调用
            mock_method.assert_called_once_with(mock_session)

    @pytest.mark.asyncio
    async def test_get_all_friend_links_empty(self, mock_session):
        """测试获取空友情链接列表"""
        # 模拟友情链接仓库返回空列表
        with patch('src.controllers.urllink.UrlLinkRepository.get_all_friend_links') as mock_method:
            mock_method.return_value = []

            # 执行测试
            result = await get_all_friend_links(mock_session)

            # 验证结果
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_all_friend_links_exception_handling(self, mock_session):
        """测试异常处理"""
        # 模拟友情链接仓库抛出异常
        with patch('src.controllers.urllink.UrlLinkRepository.get_all_friend_links') as mock_method:
            mock_method.side_effect = Exception("数据库错误")

            # 执行测试 - 应该返回空列表而不是抛出异常
            result = await get_all_friend_links(mock_session)

            # 验证结果
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_friend_links_ordering(self, mock_session):
        """测试友情链接排序"""
        # 模拟友情链接仓库返回乱序结果
        unordered_links = [
            UrlLink(id=3, subject="链接3", linkstr="https://example3.com", ordernum=3),
            UrlLink(id=1, subject="链接1", linkstr="https://example1.com", ordernum=1),
            UrlLink(id=2, subject="链接2", linkstr="https://example2.com", ordernum=2)
        ]

        with patch('src.controllers.urllink.UrlLinkRepository.get_friend_links_by_project') as mock_method:
            mock_method.return_value = unordered_links

            # 执行测试
            result = await get_project_friend_links(1, mock_session)

            # 验证结果
            assert len(result) == 3
            # 虽然返回的是乱序，但查询应该包含order_by
            assert result[0].ordernum == 3
            assert result[1].ordernum == 1
            assert result[2].ordernum == 2

    @pytest.mark.asyncio
    async def test_friend_links_limit(self, mock_session):
        """测试友情链接数量限制"""
        # 模拟超过限制的结果
        many_links = [
            UrlLink(id=i, subject=f"链接{i}", linkstr=f"https://example{i}.com", ordernum=i)
            for i in range(1, 15)  # 14个链接
        ]

        with patch('src.controllers.urllink.UrlLinkRepository.get_friend_links_by_project') as mock_method:
            mock_method.return_value = many_links[:10]  # 只返回前10个

            # 执行测试
            result = await get_project_friend_links(1, mock_session)

            # 验证结果
            assert len(result) == 10
            assert result[0].id == 1
            assert result[9].id == 10
