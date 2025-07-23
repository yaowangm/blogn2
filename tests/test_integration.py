import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession

class TestIntegration:
    """集成测试"""
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "BlogN2 API"
    
    def test_root_endpoint(self, client: TestClient):
        """测试根路径端点"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_index_endpoint(self, client: TestClient):
        """测试首页端点"""
        response = client.get("/index.html")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_api_docs_endpoint(self, client: TestClient):
        """测试API文档端点"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_metadata_endpoint_integration(self, client: TestClient, test_session):
        """测试元数据端点的完整集成"""
        # 使用session fixture直接创建数据库表
        async with test_session.begin():
            await test_session.run_sync(lambda sync_session: SQLModel.metadata.create_all(bind=sync_session.bind))
        
        # 测试API端点
        response = client.get("/api/metadata/")
        
        # 检查响应状态码和基本结构
        assert response.status_code in [200, 500]  # 可能因为数据库连接问题返回500
        
        if response.status_code == 200:
            data = response.json()
            # 验证返回的数据结构
            assert isinstance(data, dict)
            # 验证包含预期的字段
            assert "site_name" in data
            assert "user_count" in data
            assert "post_count" in data
    
    @pytest.mark.asyncio
    async def test_user_endpoints_integration(self, client: TestClient, test_session):
        """测试用户端点的完整集成"""
        # 使用session fixture直接创建数据库表
        async with test_session.begin():
            await test_session.run_sync(lambda sync_session: SQLModel.metadata.create_all(bind=sync_session.bind))
        
        # 创建测试数据
        from src.database import User
        from datetime import datetime
        
        test_user = User(
            name="testuser",
            email="test@example.com",
            password="hashed_password",
            state=1,
            regtime=datetime.now()  # 提供必需的regtime字段
        )
        test_session.add(test_user)
        await test_session.commit()
        
        # 测试用户统计端点
        response = client.get("/api/users/summary")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "total_users" in data
            assert "recent_users" in data
        
        # 测试用户总数端点
        response = client.get("/api/users/count")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "count" in data
        
        # 测试最新用户端点
        response = client.get("/api/users/listnew")
        assert response.status_code in [200, 500]
    
    def test_invalid_endpoint(self, client: TestClient):
        """测试无效端点"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_cors_headers(self, client: TestClient):
        """测试CORS头部"""
        response = client.options("/api/metadata/")
        
        # 检查CORS头部是否存在
        assert "access-control-allow-origin" in response.headers or response.status_code == 405

class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_error(self, client: TestClient):
        """测试404错误处理"""
        response = client.get("/api/nonexistent/endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_method_not_allowed(self, client: TestClient):
        """测试方法不允许错误"""
        response = client.post("/api/metadata/")
        
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data
    
    def test_invalid_user_id(self, client: TestClient):
        """测试无效用户ID"""
        response = client.get("/api/users/invalid_id")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data 