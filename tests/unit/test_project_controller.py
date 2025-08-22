"""
项目控制器单元测试

测试project.py中的各种API端点
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from src.controllers.project import get_project, get_project_posts, get_project_recent_comments


class TestProjectController:
    """项目控制器测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_project_success(self, mock_session):
        """测试成功获取项目信息"""
        # 模拟项目仓库
        with patch('src.controllers.project.ProjectRepository') as mock_repo_class:
            mock_repo = MagicMock()
            # 创建正确的mock对象
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.name = "测试博客"
            mock_project.comment = "测试描述"
            mock_project.recordcount = 10
            mock_project.accesscount = 100
            mock_project.userid = 1
            mock_project.createtime = "2024-01-01T00:00:00"
            mock_project.updatetime = "2024-01-01T00:00:00"
            mock_project.commentcount = 5
            
            mock_repo.get_by_id = AsyncMock(return_value=mock_project)
            mock_repo_class.return_value = mock_repo

            # 执行测试
            result = await get_project(1, mock_session)

            # 验证结果
            assert result["id"] == 1
            assert result["name"] == "测试博客"
            assert result["comment"] == "测试描述"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, mock_session):
        """测试获取不存在的项目"""
        # 模拟项目仓库返回None
        with patch('src.controllers.project.ProjectRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            mock_repo_class.return_value = mock_repo

            # 执行测试并验证异常
            with pytest.raises(HTTPException) as exc_info:
                await get_project(999, mock_session)

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "项目不存在"

    @pytest.mark.asyncio
    async def test_get_project_posts_original_success(self, mock_session):
        """测试成功获取原创文章列表"""
        # 模拟项目项仓库
        with patch('src.controllers.project.ProjectItemRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_project_id_and_folder = AsyncMock(return_value=[])
            mock_repo.get_count_from_folder_recordcount = AsyncMock(return_value=0)
            mock_repo_class.return_value = mock_repo

            # 执行测试
            result = await get_project_posts(1, 1, 10, "original", None, None, mock_session)

            # 验证结果
            assert "posts" in result
            assert "total" in result

    @pytest.mark.asyncio
    async def test_get_project_posts_subscription_success(self, mock_session):
        """测试成功获取订阅文章列表"""
        # 模拟订阅仓库
        with patch('src.repositories.subscription_repository.SubscriptionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_subscription_posts_by_project = AsyncMock(return_value={
                "posts": [],
                "total": 0
            })
            mock_repo_class.return_value = mock_repo

            # 执行测试
            result = await get_project_posts(1, 1, 10, "subscription", None, None, mock_session)

            # 验证结果
            assert "posts" in result
            assert "total" in result

    @pytest.mark.asyncio
    async def test_get_project_posts_invalid_type(self, mock_session):
        """测试无效的文章类型"""
        # 模拟项目项仓库
        with patch('src.controllers.project.ProjectItemRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_project_id_and_folder = AsyncMock(return_value=[])
            mock_repo.get_count_from_folder_recordcount = AsyncMock(return_value=0)
            mock_repo_class.return_value = mock_repo

            # 执行测试 - invalid类型应该当作original处理
            result = await get_project_posts(1, 1, 10, "invalid", None, None, mock_session)

            # 验证结果
            assert "posts" in result
            assert "total" in result

    @pytest.mark.asyncio
    async def test_get_project_recent_comments_success(self, mock_session):
        """测试成功获取项目最近评论"""
        # 模拟评论仓库
        with patch('src.controllers.project.PostRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_recent_comments_by_project = AsyncMock(return_value=[])
            mock_repo_class.return_value = mock_repo

            # 执行测试
            result = await get_project_recent_comments(1, 5, mock_session)

            # 验证结果
            assert isinstance(result, list)
