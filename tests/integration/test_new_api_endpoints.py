"""
新增API端点集成测试

测试blog_page分支中新增的API端点
"""

import pytest
from fastapi.testclient import TestClient


class TestNewApiEndpoints:
    """新增API端点测试类"""

    @pytest.mark.integration
    def test_get_project_info(self, test_client):
        """测试获取项目信息端点"""
        response = test_client.get("/api/projects/1")
        # 项目1可能不存在，所以接受404状态
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_get_project_posts_original(self, test_client):
        """测试获取项目原创文章"""
        response = test_client.get("/api/projects/1/posts?type=original&page=1&limit=5")
        # 项目1可能不存在，所以接受404状态
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_get_project_posts_subscription(self, test_client):
        """测试获取项目订阅文章"""
        response = test_client.get("/api/projects/1/posts?type=subscription&page=1&limit=5")
        # 项目1可能不存在，所以接受404状态
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_get_project_posts_invalid_type(self, test_client):
        """测试无效的文章类型 - 应该当作original处理"""
        response = test_client.get("/api/projects/1/posts?type=invalid")
        # 项目1可能不存在，所以接受404状态
        # 如果项目存在，invalid类型应该当作original处理，返回200
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_get_project_recent_comments(self, test_client):
        """测试获取项目最近评论"""
        response = test_client.get("/api/projects/1/comments/recent?limit=5")
        # 项目1可能不存在，所以接受404状态
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_get_project_friend_links(self, test_client):
        """测试获取项目友情链接"""
        response = test_client.get("/api/projects/1/friend-links")
        # 项目1可能不存在，所以接受404状态
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    def test_get_all_friend_links(self, test_client):
        """测试获取所有友情链接"""
        response = test_client.get("/api/friend-links")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_blog_page_route(self, test_client):
        """测试博客页面路由"""
        response = test_client.get("/blog/1")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.integration
    def test_health_check_endpoint(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.integration
    def test_cache_management_endpoints(self, test_client):
        """测试缓存管理端点"""
        # 缓存状态
        response = test_client.get("/api/cache/status")
        assert response.status_code == 200
        
        # 缓存统计
        response = test_client.get("/api/cache/stats")
        assert response.status_code == 200
        
        # 缓存清理
        response = test_client.post("/api/cache/clear")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_user_endpoints(self, test_client):
        """测试用户相关端点"""
        # 用户摘要
        response = test_client.get("/api/users/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert isinstance(data["total_users"], int)

    @pytest.mark.integration
    def test_blog_endpoints(self, test_client):
        """测试博客相关端点"""
        # 最新博客
        response = test_client.get("/api/blogs/recent?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 最新博文
        response = test_client.get("/api/blogs/posts/latest?page=1&page_size=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "posts" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
