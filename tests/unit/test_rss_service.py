"""
RSS服务单元测试
测试RSS数据生成和格式化功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.rss_service import RSSService


class TestRSSService:
    """RSS服务测试类"""
    
    @pytest.fixture
    def sample_projects(self):
        """创建示例项目数据"""
        return [
            {
                "id": 1,
                "name": "测试博客1",
                "comment": "这是测试博客1的描述",
                "createtime": "2024-01-01T10:00:00",
                "updatetime": "2024-01-02T10:00:00"
            }
        ]
    
    @pytest.fixture
    def sample_articles(self):
        """创建示例文章数据"""
        return [
            {
                "id": 101,
                "title": "测试文章1",
                "content": "这是测试文章1的内容",
                "createtime": "2024-01-01T10:00:00",
                "updatetime": "2024-01-01T10:00:00",
                "project": {"id": 1, "name": "测试博客1"}
            }
        ]
    
    @pytest.fixture
    def mock_project_repository(self):
        """创建模拟的项目仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_project_item_repository(self):
        """创建模拟的项目项仓库"""
        return AsyncMock()
    
    def test_get_site_rss_data(self, sample_projects, sample_articles, mock_project_repository, mock_project_item_repository):
        """测试获取站点RSS数据"""
        # 模拟仓库方法
        mock_project_repository.get_all_projects.return_value = sample_projects
        mock_project_item_repository.get_all_project_items.return_value = sample_articles
        
        # 创建RSS服务实例
        rss_service = RSSService(mock_project_repository, mock_project_item_repository)
        
        # 执行测试
        result = rss_service.get_site_rss_data()
        
        # 验证结果结构
        assert "title" in result
        assert "description" in result
        assert "link" in result
        assert "items" in result
        
        # 验证文章链接格式（应该是 /article/{id} 而不是 /blog/{project_id}/article/{id}）
        first_article = result["items"][0]
        assert first_article["link"] == "/article/101"
        assert first_article["guid"] == "/article/101"
    
    def test_get_blog_rss_data(self, sample_articles, mock_project_repository, mock_project_item_repository):
        """测试获取博客RSS数据"""
        # 模拟仓库方法
        mock_project_item_repository.get_project_items_by_project_id.return_value = sample_articles
        
        # 创建RSS服务实例
        rss_service = RSSService(mock_project_repository, mock_project_item_repository)
        
        # 执行测试
        result = rss_service.get_blog_rss_data(1)
        
        # 验证文章链接格式
        first_article = result["items"][0]
        assert first_article["link"] == "/article/101"
        assert first_article["guid"] == "/article/101"
