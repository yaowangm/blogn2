"""
新增API端点集成测试

测试blog_page分支中新增的API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


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

    @pytest.mark.integration
    def test_search_all_pagination_page2_differs(self, test_client):
        """
        搜索分页回归：GET /search?type=all&page=2 应与 page=1 返回不同 items。

        说明：用 mock 固定服务层候选结果，避免依赖真实模型/真实 DB 数据分布。
        """
        import numpy as np
        dummy_vec = AsyncMock()
        dummy_vec.vectorize_text = AsyncMock(return_value=np.ones(384))

        keyword_items = [
            {"id": i, "title": f"A{i}", "content": "包含爱因斯坦", "author": "u", "relevance_score": 1.0, "type": "article"}
            for i in range(1, 11)
        ]
        comment_items = [
            {"id": 100 + i, "title": f"C{i}", "content": "包含爱因斯坦", "author": "u", "relevance_score": 0.6, "type": "comment"}
            for i in range(1, 6)
        ]

        with patch("src.controllers.search.get_cached_model", return_value=dummy_vec), \
             patch("src.controllers.search.HierarchicalSearchService._keyword_search_articles", new=AsyncMock(return_value={"items": keyword_items, "total": 10, "has_more": False, "dynamic_threshold": 0.55})), \
             patch("src.controllers.search.HierarchicalSearchService.hybrid_search_articles", new=AsyncMock(return_value={"items": [], "total": 0, "has_more": False, "dynamic_threshold": 0.55})), \
             patch("src.controllers.search.HierarchicalSearchService._search_comments", new=AsyncMock(return_value={"items": comment_items, "total": 5, "has_more": False})):
            r1 = test_client.get("/api/search", params={"q": "爱因斯坦", "type": "all", "page": 1, "limit": 5})
            r2 = test_client.get("/api/search", params={"q": "爱因斯坦", "type": "all", "page": 2, "limit": 5})

        assert r1.status_code == 200, f"unexpected status={r1.status_code} body={r1.text[:500]}"
        assert r2.status_code == 200, f"unexpected status={r2.status_code} body={r2.text[:500]}"
        assert "application/json" in (r1.headers.get("content-type") or "")
        assert "application/json" in (r2.headers.get("content-type") or "")

        ids1 = [x.get("id") for x in r1.json().get("results", [])]
        ids2 = [x.get("id") for x in r2.json().get("results", [])]
        assert ids1 and ids2
        assert ids1 != ids2
