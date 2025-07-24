"""
API端点集成测试 - 使用真实数据库
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.post import Post


class TestAPIEndpointsWithRealDB:
    """使用真实数据库的API端点测试类"""

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
    def test_get_user_summary_with_real_db(self, test_client, test_session):
        """测试获取用户摘要 - 使用真实数据库"""
        # 创建测试用户数据
        user1 = User(
            id=1,
            name="testuser1",
            email="user1@example.com",
            password="hashed_password",
            regtime="2024-01-01 10:00:00"
        )
        user2 = User(
            id=2,
            name="testuser2", 
            email="user2@example.com",
            password="hashed_password",
            regtime="2024-01-02 10:00:00"
        )
        
        test_session.add(user1)
        test_session.add(user2)
        test_session.commit()
        
        response = test_client.get("/api/users/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert data["total_users"] >= 2

    @pytest.mark.integration
    def test_get_user_count_with_real_db(self, test_client, test_session):
        """测试获取用户总数 - 使用真实数据库"""
        # 确保有测试数据
        user = User(
            id=3,
            name="testuser3",
            email="user3@example.com",
            password="hashed_password",
            regtime="2024-01-03 10:00:00"
        )
        test_session.add(user)
        test_session.commit()
        
        response = test_client.get("/api/users/count")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert data["count"] >= 1

    @pytest.mark.integration
    def test_get_user_by_id_with_real_db(self, test_client, test_session):
        """测试根据ID获取用户 - 使用真实数据库"""
        # 创建测试用户
        user = User(
            id=4,
            name="testuser4",
            email="user4@example.com",
            password="hashed_password",
            regtime="2024-01-04 10:00:00"
        )
        test_session.add(user)
        test_session.commit()
        
        response = test_client.get("/api/users/4")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 4
        assert data["name"] == "testuser4"

    @pytest.mark.integration
    def test_get_user_by_id_not_found_with_real_db(self, test_client):
        """测试根据ID获取用户不存在 - 使用真实数据库"""
        response = test_client.get("/api/users/99999")
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_recent_blogs_with_real_db(self, test_client, test_session):
        """测试获取最新博客 - 使用真实数据库"""
        # 创建测试项目
        project = Project(
            id=1,
            name="Test Project",
            userid=1,
            createtime="2024-01-01 10:00:00",
            state=0,
            accesscount=10
        )
        test_session.add(project)
        test_session.commit()
        
        response = test_client.get("/api/blogs/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_popular_blogs_with_real_db(self, test_client, test_session):
        """测试获取热门博客 - 使用真实数据库"""
        # 创建测试项目
        project = Project(
            id=2,
            name="Popular Project",
            userid=1,
            createtime="2024-01-01 10:00:00",
            state=0,
            accesscount=100
        )
        test_session.add(project)
        test_session.commit()
        
        response = test_client.get("/api/blogs/popular")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_about_content_with_real_db(self, test_client, test_session):
        """测试获取关于内容 - 使用真实数据库"""
        # 创建测试项目项
        project_item = ProjectItem(
            id=486,
            projectid=1,
            name="About Page",
            comment="This is the about page content",
            itemtype=1,
            userid=1,
            createtime="2024-01-01 10:00:00",
            status=1
        )
        test_session.add(project_item)
        test_session.commit()
        
        response = test_client.get("/api/blogs/about")
        assert response.status_code == 200
        
        data = response.json()
        assert "title" in data
        assert "content" in data
        assert "link" in data
        assert data["title"] == "Why Blogn"

    @pytest.mark.integration
    def test_get_site_metadata_with_real_db(self, test_client, test_session):
        """测试获取站点元数据 - 使用真实数据库"""
        # 确保有用户数据
        user = User(
            id=5,
            name="testuser5",
            email="user5@example.com",
            password="hashed_password",
            regtime="2024-01-05 10:00:00"
        )
        test_session.add(user)
        test_session.commit()
        
        response = test_client.get("/api/metadata/")
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