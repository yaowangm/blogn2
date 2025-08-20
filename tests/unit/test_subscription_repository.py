"""
订阅仓库单元测试

测试SubscriptionRepository的各种方法
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import select
from src.repositories.subscription_repository import SubscriptionRepository
from src.models.subscription import Subscription
from src.models.project_item import ProjectItem
from src.models.project import Project
from src.models.user import User


class TestSubscriptionRepository:
    """订阅仓库测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        session.exec = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """创建仓库实例"""
        return SubscriptionRepository(mock_session)

    @pytest.fixture
    def mock_project_item(self):
        """模拟项目项"""
        return ProjectItem(
            id=1,
            name="测试文章",
            comment="测试内容",
            userid=1,
            createtime="2024-01-01T00:00:00",
            status=1
        )

    @pytest.mark.asyncio
    async def test_get_subscription_posts_by_project_success(self, repository, mock_session, mock_project_item):
        """测试成功获取订阅文章列表"""
        # 模拟查询结果 - 第一次调用返回文章列表
        mock_result1 = MagicMock()
        # 确保result对象本身是可迭代的
        mock_result1.__iter__ = MagicMock(return_value=iter([
            (mock_project_item, "测试博客", "测试用户")
        ]))
        
        # 第二次调用返回总数
        mock_result2 = MagicMock()
        mock_result2.first.return_value = 1
        
        # 使用side_effect来为不同的调用返回不同的值
        mock_session.exec.side_effect = [mock_result1, mock_result2]

        # 执行测试
        result = await repository.get_subscription_posts_by_project(1, 1, 10)

        # 验证结果
        assert "posts" in result
        assert "total" in result
        assert "page" in result
        assert "limit" in result
        assert "total_pages" in result
        assert len(result["posts"]) == 1
        assert result["posts"][0]["name"] == "测试文章"
        assert result["posts"][0]["blog_name"] == "测试博客"
        assert result["posts"][0]["author_name"] == "测试用户"
        assert result["posts"][0]["avatar"] == "/avatar/1/s_1.jpg"

    @pytest.mark.asyncio
    async def test_get_subscription_posts_by_project_empty(self, repository, mock_session):
        """测试获取空订阅文章列表"""
        # 模拟空结果 - 第一次调用返回空文章列表
        mock_result1 = MagicMock()
        mock_result1.__iter__ = MagicMock(return_value=iter([]))
        
        # 第二次调用返回总数0
        mock_result2 = MagicMock()
        mock_result2.first.return_value = 0
        
        # 设置side_effect
        mock_session.exec.side_effect = [mock_result1, mock_result2]

        # 执行测试
        result = await repository.get_subscription_posts_by_project(1, 1, 10)

        # 验证结果
        assert "posts" in result
        assert "total" in result
        assert len(result["posts"]) == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_count_subscriptions_by_project(self, repository, mock_session):
        """测试统计订阅数量"""
        # 模拟计数结果
        mock_result = MagicMock()
        mock_result.first.return_value = 10
        mock_session.exec.return_value = mock_result

        # 执行测试
        count = await repository.count_subscriptions_by_project(1)

        # 验证结果
        assert count == 10
        mock_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_subscriptions_by_project_zero(self, repository, mock_session):
        """测试统计订阅数量为零"""
        # 模拟零结果
        mock_result = MagicMock()
        mock_result.first.return_value = 0
        mock_session.exec.return_value = mock_result

        # 执行测试
        count = await repository.count_subscriptions_by_project(1)

        # 验证结果
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_subscription_posts_by_project_with_avatar(self, repository, mock_session, mock_project_item):
        """测试订阅文章包含头像信息"""
        # 模拟查询结果
        mock_result1 = MagicMock()
        mock_result1.__iter__ = MagicMock(return_value=iter([
            (mock_project_item, "测试博客", "测试用户")
        ]))
        
        mock_result2 = MagicMock()
        mock_result2.first.return_value = 1
        
        mock_session.exec.side_effect = [mock_result1, mock_result2]

        # 执行测试
        result = await repository.get_subscription_posts_by_project(1, 1, 10)

        # 验证头像路径生成
        assert len(result["posts"]) == 1
        assert result["posts"][0]["avatar"] == "/avatar/1/s_1.jpg"

    @pytest.mark.asyncio
    async def test_get_subscription_posts_by_project_no_userid(self, repository, mock_session):
        """测试没有用户ID的订阅文章"""
        # 创建没有userid的项目项
        project_item_no_user = ProjectItem(
            id=2,
            name="无用户文章",
            comment="无用户内容",
            userid=None,
            createtime="2024-01-01T00:00:00",
            status=1
        )

        # 模拟查询结果
        mock_result1 = MagicMock()
        mock_result1.__iter__ = MagicMock(return_value=iter([
            (project_item_no_user, "测试博客", "未知用户")
        ]))
        
        mock_result2 = MagicMock()
        mock_result2.first.return_value = 1
        
        mock_session.exec.side_effect = [mock_result1, mock_result2]

        # 执行测试
        result = await repository.get_subscription_posts_by_project(1, 1, 10)

        # 验证结果
        assert len(result["posts"]) == 1
        assert result["posts"][0]["avatar"] is None
        assert result["posts"][0]["userid"] is None
