"""
文章控制器增强测试模块

测试文章控制器的更新功能，包括：
- 改进的API文档
- 缓存功能
- 权限验证
- 错误处理
- 性能优化
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from src.controllers.article import (
    get_article_detail,
    get_article_comments,
    create_article_comment,
    get_article_attachments,
    update_article,
    delete_article,
    permanently_delete_article,
    delete_article_images
)


class TestArticleControllerEnhanced:
    """文章控制器增强功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_session = AsyncMock(spec=AsyncSession)
        self.mock_user = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }
        self.mock_article = {
            "id": 1,
            "title": "测试文章",
            "content": "测试内容",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "views": 100,
            "project_id": 1
        }
        self.mock_comment = {
            "id": 1,
            "content": "测试评论",
            "created_at": datetime.now(),
            "user_id": 1,
            "article_id": 1
        }
        self.mock_attachment = {
            "id": 1,
            "filename": "test.jpg",
            "file_path": "/uploads/test.jpg",
            "file_size": 1024,
            "mime_type": "image/jpeg",
            "article_id": 1
        }
    
    @patch('src.controllers.article.ProjectItemRepository')
    @patch('src.controllers.article.cache_article_detail')
    async def test_get_article_detail_success(self, mock_cache, mock_repo_class):
        """测试获取文章详情成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = self.mock_article
        
        # 执行测试
        result = await get_article_detail(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "测试文章"
        assert result["content"] == "测试内容"
        
        # 验证缓存被调用
        mock_cache.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_get_article_detail_not_found(self, mock_repo_class):
        """测试获取文章详情失败 - 文章不存在"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await get_article_detail(
                article_id=999,
                session=self.mock_session,
                current_user=self.mock_user
            )
        
        assert exc_info.value.status_code == 404
        assert "文章不存在" in str(exc_info.value.detail)
    
    @patch('src.controllers.article.ProjectItemRepository')
    @patch('src.controllers.article.cache_article_comments')
    async def test_get_article_comments_success(self, mock_cache, mock_repo_class):
        """测试获取文章评论成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_article_comments.return_value = [self.mock_comment]
        
        # 执行测试
        result = await get_article_comments(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["content"] == "测试评论"
        
        # 验证缓存被调用
        mock_cache.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    @patch('src.controllers.article.UserRepository')
    async def test_create_article_comment_success(self, mock_user_repo_class, mock_repo_class):
        """测试创建文章评论成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = self.mock_article
        
        mock_user_repo = AsyncMock()
        mock_user_repo_class.return_value = mock_user_repo
        mock_user_repo.get_by_id.return_value = self.mock_user
        
        mock_repo.create_comment.return_value = self.mock_comment
        
        # 执行测试
        result = await create_article_comment(
            article_id=1,
            content="新评论",
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is not None
        assert result["content"] == "新评论"
        
        # 验证方法被调用
        mock_repo.create_comment.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_create_article_comment_article_not_found(self, mock_repo_class):
        """测试创建文章评论失败 - 文章不存在"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await create_article_comment(
                article_id=999,
                content="新评论",
                session=self.mock_session,
                current_user=self.mock_user
            )
        
        assert exc_info.value.status_code == 404
        assert "文章不存在" in str(exc_info.value.detail)
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_update_article_success(self, mock_repo_class):
        """测试更新文章成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = self.mock_article
        mock_repo.update.return_value = {**self.mock_article, "title": "更新后的标题"}
        
        # 执行测试
        result = await update_article(
            article_id=1,
            title="更新后的标题",
            content="更新后的内容",
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is not None
        assert result["title"] == "更新后的标题"
        
        # 验证方法被调用
        mock_repo.update.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_update_article_not_found(self, mock_repo_class):
        """测试更新文章失败 - 文章不存在"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await update_article(
                article_id=999,
                title="更新后的标题",
                content="更新后的内容",
                session=self.mock_session,
                current_user=self.mock_user
            )
        
        assert exc_info.value.status_code == 404
        assert "文章不存在" in str(exc_info.value.detail)
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_delete_article_success(self, mock_repo_class):
        """测试删除文章成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = self.mock_article
        mock_repo.soft_delete.return_value = True
        
        # 执行测试
        result = await delete_article(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is True
        
        # 验证方法被调用
        mock_repo.soft_delete.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_delete_article_not_found(self, mock_repo_class):
        """测试删除文章失败 - 文章不存在"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await delete_article(
                article_id=999,
                session=self.mock_session,
                current_user=self.mock_user
            )
        
        assert exc_info.value.status_code == 404
        assert "文章不存在" in str(exc_info.value.detail)
    
    @patch('src.controllers.article.AttachmentRepository')
    @patch('src.controllers.article.cache_article_attachments')
    async def test_get_article_attachments_success(self, mock_cache, mock_repo_class):
        """测试获取文章附件成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_article_id.return_value = [self.mock_attachment]
        
        # 执行测试
        result = await get_article_attachments(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["filename"] == "test.jpg"
        
        # 验证缓存被调用
        mock_cache.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_permanently_delete_article_success(self, mock_repo_class):
        """测试永久删除文章成功"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = self.mock_article
        mock_repo.delete.return_value = True
        
        # 执行测试
        result = await permanently_delete_article(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is True
        
        # 验证方法被调用
        mock_repo.delete.assert_called_once()
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_permanently_delete_article_not_found(self, mock_repo_class):
        """测试永久删除文章失败 - 文章不存在"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await permanently_delete_article(
                article_id=999,
                session=self.mock_session,
                current_user=self.mock_user
            )
        
        assert exc_info.value.status_code == 404
        assert "文章不存在" in str(exc_info.value.detail)
    
    async def test_delete_article_images_success(self):
        """测试删除文章图片成功"""
        # 执行测试
        result = await delete_article_images(
            attachment_path="/uploads/test.jpg",
            article_id=1,
            session=self.mock_session
        )
        
        # 验证结果
        assert result is None  # 函数没有返回值


class TestArticleControllerCache:
    """文章控制器缓存测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_session = AsyncMock(spec=AsyncSession)
        self.mock_user = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }
    
    @patch('src.controllers.article.cache_article_detail')
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_article_detail_caching(self, mock_repo_class, mock_cache):
        """测试文章详情缓存"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = {"id": 1, "title": "测试文章"}
        
        # 执行测试
        await get_article_detail(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证缓存被调用
        mock_cache.assert_called_once()
    
    @patch('src.controllers.article.cache_article_comments')
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_article_comments_caching(self, mock_repo_class, mock_cache):
        """测试文章评论缓存"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_article_comments.return_value = [{"id": 1, "content": "测试评论"}]
        
        # 执行测试
        await get_article_comments(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证缓存被调用
        mock_cache.assert_called_once()
    
    @patch('src.controllers.article.cache_article_attachments')
    @patch('src.controllers.article.AttachmentRepository')
    async def test_article_attachments_caching(self, mock_repo_class, mock_cache):
        """测试文章附件缓存"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_article_id.return_value = [{"id": 1, "filename": "test.jpg"}]
        
        # 执行测试
        await get_article_attachments(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证缓存被调用
        mock_cache.assert_called_once()


class TestArticleControllerPermissions:
    """文章控制器权限测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_session = AsyncMock(spec=AsyncSession)
        self.mock_user = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }
        self.mock_anonymous_user = None
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_get_article_detail_with_user(self, mock_repo_class):
        """测试有用户时获取文章详情"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = {"id": 1, "title": "测试文章"}
        
        # 执行测试
        result = await get_article_detail(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_user
        )
        
        # 验证结果
        assert result is not None
        assert result["id"] == 1
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_get_article_detail_without_user(self, mock_repo_class):
        """测试无用户时获取文章详情"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = {"id": 1, "title": "测试文章"}
        
        # 执行测试
        result = await get_article_detail(
            article_id=1,
            session=self.mock_session,
            current_user=self.mock_anonymous_user
        )
        
        # 验证结果
        assert result is not None
        assert result["id"] == 1
    
    @patch('src.controllers.article.ProjectItemRepository')
    async def test_create_comment_requires_user(self, mock_repo_class):
        """测试创建评论需要用户"""
        # 设置模拟对象
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = {"id": 1, "title": "测试文章"}
        
        # 执行测试并验证异常
        with pytest.raises(HTTPException) as exc_info:
            await create_article_comment(
                article_id=1,
                content="新评论",
                session=self.mock_session,
                current_user=self.mock_anonymous_user
            )
        
        assert exc_info.value.status_code == 401
        assert "需要登录" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__])
