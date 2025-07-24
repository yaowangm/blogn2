"""
基本API端点测试 - 使用真实PostgreSQL数据库
"""

import pytest
from fastapi.testclient import TestClient


class TestBasicAPIEndpointsWithRealPostgreSQL:
    """使用真实PostgreSQL数据库的基本API端点测试类"""

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
        """测试index.html端点"""
        response = test_client.get("/index.html")
        assert response.status_code == 200

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
        response = test_client.get("/api/metadata/site")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_count" in data
        assert isinstance(data["user_count"], int)

    @pytest.mark.integration
    def test_static_upload_file_not_found(self, test_client):
        """测试静态上传文件不存在"""
        response = test_client.get("/static/upload/nonexistent.jpg")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_avatar_file_not_found(self, test_client):
        """测试头像文件不存在"""
        response = test_client.get("/avatars/123/nonexistent.jpg")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_invalid_endpoint(self, test_client):
        """测试无效端点"""
        response = test_client.get("/api/invalid/endpoint")
        assert response.status_code == 404 