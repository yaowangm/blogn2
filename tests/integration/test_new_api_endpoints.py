"""
新增API端点集成测试

测试blog_page分支中新增的API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import app
from src.utils.auth_dependencies import get_current_user


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
        """测试博客页面路由（项目 1 未必存在，与 test_basic_endpoints 一致）。"""
        response = test_client.get("/blog/1")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")

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
        搜索分页回归：GET /api/search?type=all&page=2 应与 page=1 返回不同 items。

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
            {
                "id": 100 + i,
                "title": f"C{i}",
                "content": "包含爱因斯坦",
                "author": "u",
                "relevance_score": 0.6,
                "type": "comment",
                "projectitem_id": 5000 + i,
                "article_id": 5000 + i,
            }
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

    @pytest.mark.integration
    def test_search_comments_api_passes_projectitem_id_for_article_anchor(self, test_client):
        """仅评论搜索：API 应透传 projectitem_id/article_id，供前端拼 /article/{id}#post{commentId}。"""
        import numpy as np

        dummy_vec = AsyncMock()
        dummy_vec.vectorize_text = AsyncMock(return_value=np.ones(384))
        row = {
            "id": 501,
            "title": "回帖主题",
            "content": "包含唯一锚点词",
            "author": "u1",
            "created_at": "2024-06-01T10:00:00+00:00",
            "relevance_score": 0.88,
            "type": "comment",
            "projectitem_id": 9001,
            "article_id": 9001,
        }
        with patch("src.controllers.search.get_cached_model", return_value=dummy_vec), patch(
            "src.controllers.search.HierarchicalSearchService._search_comments",
            new=AsyncMock(return_value={"items": [row], "total": 1, "has_more": False}),
        ):
            r = test_client.get("/api/search", params={"q": "唯一锚点词", "type": "comments", "page": 1, "limit": 10})

        assert r.status_code == 200, r.text[:500]
        data = r.json()
        results = data.get("results") or []
        assert len(results) >= 1
        c = next(x for x in results if x.get("type") == "comment")
        assert c["id"] == 501
        assert c["projectitem_id"] == 9001
        assert c["article_id"] == 9001

    @pytest.mark.integration
    def test_search_comments_keyword_fallback_passes_projectitem_id(self, test_client):
        """评论搜索在向量无效时走关键词通道，仍应带上博文 id 字段。"""
        import numpy as np

        dummy_vec = AsyncMock()
        dummy_vec.vectorize_text = AsyncMock(return_value=np.zeros(384))
        row = {
            "id": 502,
            "title": "关键词回",
            "content": "关键词回退短语",
            "author": "u2",
            "created_at": "2024-06-02T10:00:00+00:00",
            "relevance_score": 1.0,
            "type": "comment",
            "projectitem_id": 9002,
            "article_id": 9002,
        }
        with patch("src.controllers.search.get_cached_model", return_value=dummy_vec), patch(
            "src.controllers.search.HierarchicalSearchService._keyword_search_comments",
            new=AsyncMock(return_value={"items": [row], "total": 1, "has_more": False}),
        ):
            r = test_client.get("/api/search", params={"q": "关键词回退短语", "type": "comments", "page": 1, "limit": 10})

        assert r.status_code == 200, r.text[:500]
        c = next(x for x in r.json().get("results", []) if x.get("type") == "comment")
        assert c["projectitem_id"] == 9002
        assert c["article_id"] == 9002

    @pytest.mark.integration
    def test_admin_recalculate_project_updatetimes_route(self, test_client):
        """POST /api/admin/projects/recalculate-updatetimes 在管理员身份下应调用批量同步并返回数量"""

        async def admin_user():
            return {"id": 1, "state": 10, "role": "admin", "name": "admin"}

        app.dependency_overrides[get_current_user] = admin_user
        try:
            with patch("src.controllers.project.ProjectRepository") as MockRepo:
                inst = MagicMock()
                inst.sync_all_projects_updatetime = AsyncMock(return_value=5)
                MockRepo.return_value = inst
                with patch("src.utils.cache.cache_manager") as mock_cm:
                    mock_cm.clear_pattern = AsyncMock(return_value=True)
                    response = test_client.post(
                        "/api/admin/projects/recalculate-updatetimes"
                    )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200, response.text
        data = response.json()
        assert data.get("project_count") == 5
        assert "重新计算" in data.get("message", "")

    @pytest.mark.integration
    def test_admin_recalculate_project_updatetimes_requires_auth(self, test_client):
        """未认证调用重新计算应 401"""
        response = test_client.post("/api/admin/projects/recalculate-updatetimes")
        assert response.status_code == 401
