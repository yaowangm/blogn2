"""
基础API端点测试 - 快速验证基本功能
不创建测试数据，仅验证API响应格式和状态码
"""

import pytest
from fastapi.testclient import TestClient


class TestBasicEndpoints:
    """基础API端点测试类 - 快速验证基本功能"""

    @pytest.fixture(autouse=True)
    def _integration_ignore_share_preview_html_always(self, monkeypatch):
        """本地若开启 SHARE_PREVIEW_HTML_ALWAYS，Chrome UA 仍会查库；无 id=1 等数据时静态页用例会 404。"""
        monkeypatch.delenv("SHARE_PREVIEW_HTML_ALWAYS", raising=False)

    @pytest.mark.integration
    def test_health_check(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.integration
    def test_root_endpoint(self, test_client):
        """测试根端点"""
        response = test_client.get("/")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_index_html_endpoint(self, test_client):
        """测试index.html端点 - 重构后已移除，应返回404"""
        response = test_client.get("/index.html")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_user_summary(self, test_client):
        """测试获取用户摘要"""
        response = test_client.get("/api/users/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert isinstance(data["total_users"], int)

    @pytest.mark.integration
    def test_get_user_count(self, test_client):
        """测试获取用户总数"""
        response = test_client.get("/api/users/count")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    @pytest.mark.integration
    def test_get_recent_blogs(self, test_client):
        """测试获取最新博客"""
        response = test_client.get("/api/blogs/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_popular_blogs(self, test_client):
        """测试获取热门博客"""
        response = test_client.get("/api/blogs/popular")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_site_metadata(self, test_client):
        """测试获取站点元数据"""
        response = test_client.get("/api/metadata/")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_count" in data
        assert isinstance(data["user_count"], int)

    @pytest.mark.integration
    def test_static_upload_file_not_found(self, test_client):
        """测试静态上传文件不存在"""
        response = test_client.get("/upload/nonexistent.jpg")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_avatar_file_not_found(self, test_client):
        """测试头像文件不存在"""
        response = test_client.get("/avatar/123/nonexistent.jpg")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_invalid_endpoint(self, test_client):
        """测试无效端点"""
        response = test_client.get("/api/invalid/endpoint")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_article_page_normal_browser(self, test_client):
        """文章页：普通浏览器仍返回静态 article.html"""
        response = test_client.get(
            "/article/1",
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "博客文章 - BlogN" in response.text

    @pytest.mark.integration
    def test_article_page_share_crawler_nonexistent_404(self, test_client):
        """文章页：分享爬虫请求不存在的文章返回 404"""
        response = test_client.get(
            "/article/999999999",
            headers={"User-Agent": "Mozilla/5.0 MicroMessenger/8.0"},
        )
        assert response.status_code == 404

    @pytest.mark.integration
    def test_blog_page_normal_browser(self, test_client):
        """博客首页：普通浏览器仍返回静态 blog.html"""
        response = test_client.get(
            "/blog/1",
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "博客页面 - BlogN" in response.text

    @pytest.mark.integration
    def test_blog_page_share_crawler_nonexistent_404(self, test_client):
        """博客首页：分享爬虫请求不存在的项目返回 404"""
        response = test_client.get(
            "/blog/999999999",
            headers={"User-Agent": "Mozilla/5.0 MicroMessenger/8.0"},
        )
        assert response.status_code == 404

    @pytest.mark.integration
    def test_thread_page_normal_browser(self, test_client):
        """留言主题页：普通浏览器仍返回静态 thread.html"""
        response = test_client.get(
            "/thread/1",
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "留言本主题 - BlogN" in response.text

    @pytest.mark.integration
    def test_thread_page_share_crawler_nonexistent_404(self, test_client):
        """留言主题页：分享爬虫请求不存在的主题返回 404"""
        response = test_client.get(
            "/thread/999999999",
            headers={"User-Agent": "Mozilla/5.0 MicroMessenger/8.0"},
        )
        assert response.status_code == 404