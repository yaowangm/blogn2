"""
博客控制器单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.controllers.blog import (
    get_recent_blogs,
    get_popular_blogs,
    get_recent_comments,
    get_about_content,
    get_recent_messages,
    get_latest_posts
)
from src.services.blog_service import BlogService


class TestBlogController:
    """博客控制器测试类"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_recent_blogs_success(self, mock_async_session):
        """测试获取最新博客成功"""
        # 准备测试数据
        expected_blogs = [
            {"id": 1, "title": "最新博客1", "author": "作者1"},
            {"id": 2, "title": "最新博客2", "author": "作者2"}
        ]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_recent_blogs.return_value = expected_blogs
        
        # 执行测试
        result = await get_recent_blogs(limit=10, blog_service=mock_service)
        
        # 验证结果
        assert result == expected_blogs
        mock_service.get_recent_blogs.assert_called_once_with(10)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_recent_blogs_default_limit(self, mock_async_session):
        """测试获取最新博客使用默认限制"""
        # 准备测试数据
        expected_blogs = [{"id": 1, "title": "测试博客"}]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_recent_blogs.return_value = expected_blogs
        
        # 执行测试（不传limit参数）
        result = await get_recent_blogs(blog_service=mock_service)
        
        # 验证结果
        assert result == expected_blogs
        mock_service.get_recent_blogs.assert_called_once_with(10)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_popular_blogs_success(self, mock_async_session):
        """测试获取热门博客成功"""
        # 准备测试数据
        expected_blogs = [
            {"id": 1, "title": "热门博客1", "views": 1000},
            {"id": 2, "title": "热门博客2", "views": 800}
        ]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_popular_blogs.return_value = expected_blogs
        
        # 执行测试
        result = await get_popular_blogs(limit=10, blog_service=mock_service)
        
        # 验证结果
        assert result == expected_blogs
        mock_service.get_popular_blogs.assert_called_once_with(10)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_recent_comments_success(self, mock_async_session):
        """测试获取最新评论成功"""
        # 准备测试数据
        expected_comments = [
            {"id": 1, "content": "评论1", "author": "用户1"},
            {"id": 2, "content": "评论2", "author": "用户2"}
        ]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_recent_comments.return_value = expected_comments
        
        # 执行测试
        result = await get_recent_comments(limit=5, blog_service=mock_service)
        
        # 验证结果
        assert result == expected_comments
        mock_service.get_recent_comments.assert_called_once_with(5)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_about_content_success(self, mock_async_session):
        """测试获取关于页面内容成功"""
        # 准备测试数据
        expected_content = {
            "id": 486,
            "title": "关于我们",
            "content": "这是关于页面的内容"
        }
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_about_content.return_value = expected_content
        
        # 执行测试
        result = await get_about_content(blog_service=mock_service)
        
        # 验证结果
        assert result == expected_content
        mock_service.get_about_content.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_recent_messages_success(self, mock_async_session):
        """测试获取最新留言成功"""
        # 准备测试数据
        expected_messages = [
            {"id": 1, "message": "留言1", "author": "访客1"},
            {"id": 2, "message": "留言2", "author": "访客2"}
        ]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_recent_messages.return_value = expected_messages
        
        # 执行测试
        result = await get_recent_messages(limit=5, blog_service=mock_service)
        
        # 验证结果
        assert result == expected_messages
        mock_service.get_recent_messages.assert_called_once_with(5)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_latest_posts_success(self, mock_async_session):
        """测试获取最新博文成功"""
        # 准备测试数据
        expected_posts = [
            {"id": 1, "title": "博文1", "content": "内容1"},
            {"id": 2, "title": "博文2", "content": "内容2"}
        ]
        
        # 模拟服务方法
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_latest_posts.return_value = expected_posts
        
        # 执行测试
        result = await get_latest_posts(limit=10, blog_service=mock_service)
        
        # 验证结果
        assert result == expected_posts
        mock_service.get_latest_posts.assert_called_once_with(10)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_recent_blogs_empty_list(self, mock_async_session):
        """测试获取最新博客返回空列表"""
        # 模拟服务方法返回空列表
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_recent_blogs.return_value = []
        
        # 执行测试
        result = await get_recent_blogs(blog_service=mock_service)
        
        # 验证结果
        assert result == []
        assert len(result) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_popular_blogs_service_error(self, mock_async_session):
        """测试获取热门博客服务错误"""
        # 模拟服务方法抛出异常
        mock_service = AsyncMock(spec=BlogService)
        mock_service.get_popular_blogs.side_effect = Exception("数据库错误")
        
        # 执行测试并验证异常
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_popular_blogs(blog_service=mock_service)
        
        # 验证异常信息
        assert exc_info.value.status_code == 500
        assert "数据库错误" in exc_info.value.detail 