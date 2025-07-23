import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app

client = TestClient(app)

class TestMetadataController:
    """测试元数据控制器"""
    
    def test_get_site_metadata_success(self, client: TestClient):
        """测试成功获取网站元数据"""
        with patch('src.controllers.metadata.get_metadata_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_service.return_value.get_metadata = AsyncMock(
                return_value={
                    "site_name": "BlogN2",
                    "version": "1.0.0",
                    "logo_url": "/static/images/logo.svg"
                }
            )
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/metadata/")
            
            assert response.status_code == 200
            data = response.json()
            assert "site_name" in data
            assert "version" in data
            assert "logo_url" in data
    
    def test_get_site_metadata_error(self, client: TestClient):
        """测试获取网站元数据时发生错误"""
        with patch('src.controllers.metadata.get_metadata_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_service.return_value.get_metadata = AsyncMock(
                side_effect=Exception("数据库错误")
            )
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/metadata/")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "获取网站元数据失败" in data["detail"]

class TestUserController:
    """测试用户控制器"""
    
    def test_get_user_summary_success(self, client: TestClient):
        """测试成功获取用户统计信息"""
        with patch('src.controllers.user.get_user_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_service.return_value.get_user_summary = AsyncMock(
                return_value={
                    "total_users": 100,
                    "active_users": 85,
                    "new_users_today": 5
                }
            )
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/users/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_users" in data
            assert "active_users" in data
            assert "new_users_today" in data
    
    def test_get_user_summary_error(self, client: TestClient):
        """测试获取用户统计信息时发生错误"""
        with patch('src.controllers.user.get_user_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_service.return_value.get_user_summary = AsyncMock(
                side_effect=Exception("数据库错误")
            )
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/users/summary")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "获取用户摘要失败" in data["detail"]
    
    def test_get_recent_users_success(self, client: TestClient):
        """测试成功获取最新用户"""
        with patch('src.controllers.user.get_user_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_users = [
                {"id": 1, "name": "user1", "email": "user1@example.com"},
                {"id": 2, "name": "user2", "email": "user2@example.com"}
            ]
            mock_service.return_value.get_top_users = AsyncMock(
                return_value=mock_users
            )
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/users/listnew")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "user1"
            assert data[1]["name"] == "user2"
    
    def test_get_user_count_success(self, client: TestClient):
        """测试成功获取用户总数"""
        with patch('src.controllers.user.get_user_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_service.return_value.get_user_count = AsyncMock(return_value=150)
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/users/count")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 150
    
    def test_get_user_by_id_success(self, client: TestClient):
        """测试成功根据ID获取用户"""
        with patch('src.controllers.user.get_user_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_user = {
                "id": 1,
                "name": "testuser",
                "email": "test@example.com",
                "state": 1
            }
            mock_service.return_value.get_user_by_id = AsyncMock(
                return_value=mock_user
            )
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/users/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "testuser"
    
    def test_get_user_by_id_not_found(self, client: TestClient):
        """测试获取不存在的用户"""
        with patch('src.controllers.user.get_user_service') as mock_dependency:
            mock_service = AsyncMock()
            mock_service.return_value.get_user_by_id = AsyncMock(return_value=None)
            mock_dependency.return_value = mock_service.return_value
            
            response = client.get("/api/users/999")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "用户不存在" in data["detail"] 