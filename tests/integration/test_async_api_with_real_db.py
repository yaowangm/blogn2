"""
异步API端点测试 - 使用真实PostgreSQL数据库
正确处理异步数据库连接
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlmodel import Session
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem


class TestAsyncAPIEndpointsWithRealDB:
    """使用真实PostgreSQL数据库的异步API端点测试类"""

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
    def test_get_user_summary_async(self, test_client, real_sync_session):
        """测试获取用户摘要 - 使用异步数据库连接"""
        # 创建测试用户数据
        user1 = User(
            id=4001,
            name="async_user1",
            email="async1@example.com",
            password="hashed_password",
            regtime="2024-01-01 10:00:00"
        )
        user2 = User(
            id=4002,
            name="async_user2", 
            email="async2@example.com",
            password="hashed_password",
            regtime="2024-01-02 10:00:00"
        )
        
        real_sync_session.add(user1)
        real_sync_session.add(user2)
        real_sync_session.commit()
        
        response = test_client.get("/api/users/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert data["total_users"] >= 2

    @pytest.mark.integration
    def test_get_user_count_async(self, test_client, real_sync_session):
        """测试获取用户总数 - 使用异步数据库连接"""
        # 确保有测试数据
        user = User(
            id=4003,
            name="async_user3",
            email="async3@example.com",
            password="hashed_password",
            regtime="2024-01-03 10:00:00"
        )
        real_sync_session.add(user)
        real_sync_session.commit()
        
        response = test_client.get("/api/users/count")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert data["count"] >= 1

    @pytest.mark.integration
    def test_get_user_by_id_async(self, test_client, real_sync_session):
        """测试根据ID获取用户 - 使用异步数据库连接"""
        # 创建测试用户
        user = User(
            id=4004,
            name="async_user4",
            email="async4@example.com",
            password="hashed_password",
            regtime="2024-01-04 10:00:00"
        )
        real_sync_session.add(user)
        real_sync_session.commit()
        
        response = test_client.get("/api/users/4004")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 4004
        # 处理数据库中的尾随空格
        assert data["name"].strip() == "async_user4"

    @pytest.mark.integration
    def test_get_user_by_id_not_found_async(self, test_client):
        """测试根据ID获取用户不存在 - 使用异步数据库连接"""
        response = test_client.get("/api/users/99999")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_recent_blogs_async(self, test_client, real_sync_session):
        """测试获取最新博客 - 使用异步数据库连接"""
        # 创建测试项目
        project = Project(
            id=5001,
            name="Async Test Project",
            userid=4001,
            createtime="2024-01-01 10:00:00",
            state=0,
            accesscount=10
        )
        real_sync_session.add(project)
        real_sync_session.commit()
        
        response = test_client.get("/api/blogs/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_popular_blogs_async(self, test_client, real_sync_session):
        """测试获取热门博客 - 使用异步数据库连接"""
        # 创建测试项目
        project = Project(
            id=5002,
            name="Async Popular Project",
            userid=4001,
            createtime="2024-01-01 10:00:00",
            state=0,
            accesscount=100
        )
        real_sync_session.add(project)
        real_sync_session.commit()
        
        response = test_client.get("/api/blogs/popular")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_about_content_async(self, test_client, real_sync_session):
        """测试获取关于内容 - 使用异步数据库连接"""
        # 创建测试项目项
        project_item = ProjectItem(
            id=5486,
            projectid=5001,
            name="Async About Page",
            comment="This is the async about page content",
            itemtype=1,
            userid=4001,
            createtime="2024-01-01 10:00:00",
            status=1
        )
        real_sync_session.add(project_item)
        real_sync_session.commit()
        
        response = test_client.get("/api/blogs/about")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["id"] == 5486

    @pytest.mark.integration
    def test_get_site_metadata_async(self, test_client, real_sync_session):
        """测试获取站点元数据 - 使用异步数据库连接"""
        # 确保有用户数据
        user = User(
            id=4005,
            name="async_user5",
            email="async5@example.com",
            password="hashed_password",
            regtime="2024-01-05 10:00:00"
        )
        real_sync_session.add(user)
        real_sync_session.commit()
        
        response = test_client.get("/api/metadata/site")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_count" in data
        assert data["user_count"] >= 1

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