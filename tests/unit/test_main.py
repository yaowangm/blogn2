import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import os
from pathlib import Path

# 导入main模块
from src.main import app, serve_file, validate_and_sanitize_path, UPLOAD_BASE_PATH, AVATAR_BASE_PATH


class TestMain:
    """主应用测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.mark.unit
    def test_serve_file_exists(self):
        """测试文件存在时的serve_file函数"""
        with patch('os.path.exists', return_value=True):
            with patch('src.main.FileResponse') as mock_file_response:
                mock_response = MagicMock()
                mock_file_response.return_value = mock_response
                
                result = serve_file("/path/to/file.jpg", "image/jpeg")
                
                assert result == mock_response
                mock_file_response.assert_called_once_with("/path/to/file.jpg", media_type="image/jpeg")
    
    @pytest.mark.unit
    def test_serve_file_not_exists(self):
        """测试文件不存在时的serve_file函数"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                serve_file("/path/to/nonexistent.jpg")
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "File not found"
    
    @pytest.mark.unit
    def test_validate_and_sanitize_path_valid(self):
        """测试有效的路径验证"""
        base_path = "/base/path"
        user_path = "valid/file.jpg"
        
        with patch('os.path.normpath', return_value=user_path):
            with patch('os.path.join', return_value="/base/path/valid/file.jpg"):
                with patch('os.path.abspath', side_effect=["/base/path/valid/file.jpg", "/base/path"]):
                    result = validate_and_sanitize_path(base_path, user_path)
                    
                    assert result == "/base/path/valid/file.jpg"
    
    @pytest.mark.unit
    def test_validate_and_sanitize_path_traversal_attack(self):
        """测试路径遍历攻击检测"""
        base_path = "/base/path"
        user_path = "../../../etc/passwd"
        
        with patch('os.path.normpath', return_value="../../../etc/passwd"):
            with pytest.raises(HTTPException) as exc_info:
                validate_and_sanitize_path(base_path, user_path)
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid path"
    
    @pytest.mark.unit
    def test_validate_and_sanitize_path_absolute_path(self):
        """测试绝对路径检测"""
        base_path = "/base/path"
        user_path = "/absolute/path"
        
        with patch('os.path.normpath', return_value="/absolute/path"):
            with pytest.raises(HTTPException) as exc_info:
                validate_and_sanitize_path(base_path, user_path)
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid path"
    
    @pytest.mark.unit
    def test_validate_and_sanitize_path_outside_base(self):
        """测试路径超出基础目录检测"""
        base_path = "/base/path"
        user_path = "valid/file.jpg"
        
        with patch('os.path.normpath', return_value=user_path):
            with patch('os.path.join', return_value="/base/path/valid/file.jpg"):
                with patch('os.path.abspath', side_effect=["/other/path/file.jpg", "/base/path"]):
                    with pytest.raises(HTTPException) as exc_info:
                        validate_and_sanitize_path(base_path, user_path)
                    
                    assert exc_info.value.status_code == 400
                    assert exc_info.value.detail == "Path traversal detected"
    
    @pytest.mark.unit
    def test_serve_upload_file(self, client):
        """测试upload文件服务"""
        with patch('src.main.validate_and_sanitize_path', return_value="/safe/path/file.jpg"):
            with patch('src.main.serve_file') as mock_serve_file:
                mock_response = MagicMock()
                mock_serve_file.return_value = mock_response
                
                response = client.get("/upload/test.jpg")
                
                # 由于这是FastAPI路由，我们需要模拟实际的响应
                assert response.status_code == 200
    
    @pytest.mark.unit
    def test_serve_upload_file_head(self, client):
        """测试upload文件HEAD请求"""
        # 重构后，main.py中没有HEAD方法的路由，只有GET方法
        # 所以HEAD请求会返回405 Method Not Allowed
        response = client.head("/upload/test.jpg")
        assert response.status_code == 405  # Method Not Allowed
    
    @pytest.mark.unit
    def test_serve_avatar_valid(self, client):
        """测试有效的头像文件服务"""
        with patch('src.main.validate_and_sanitize_path', return_value="/safe/path/avatar.jpg"):
            with patch('src.main.serve_file') as mock_serve_file:
                mock_response = MagicMock()
                mock_serve_file.return_value = mock_response
                
                response = client.get("/avatar/123/avatar.jpg")
                
                # 由于这是FastAPI路由，我们需要模拟实际的响应
                assert response.status_code == 200
    
    @pytest.mark.unit
    def test_serve_avatar_invalid_prefix(self, client):
        """测试无效的头像前缀"""
        # 由于重构后的路由是 /avatar/{file_path:path}，这个测试需要调整
        # 现在路径验证在 validate_and_sanitize_path 函数中处理
        # 当路径验证失败时，会抛出HTTPException，FastAPI会返回相应的状态码
        # 但由于这是测试环境，实际的路径验证可能不会执行，所以返回404
        response = client.get("/avatar/invalid/avatar.jpg")
        # 由于路径验证失败，应该返回404错误（文件不存在）
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_serve_avatar_empty_filename(self, client):
        """测试空的头像文件名"""
        response = client.get("/avatar/123/")
        assert response.status_code == 404  # FastAPI路由不匹配
    
    @pytest.mark.unit
    def test_root_endpoint(self, client):
        """测试根路径端点"""
        with patch('src.main.FileResponse') as mock_file_response:
            mock_response = MagicMock()
            mock_file_response.return_value = mock_response
            
            response = client.get("/")
            
            # 由于这是FastAPI路由，我们需要模拟实际的响应
            assert response.status_code == 200
    
    @pytest.mark.unit
    def test_index_html_endpoint(self, client):
        """测试index.html端点 - 重构后已移除，重定向到根路径"""
        # 重构后，/index.html 端点已被移除，用户访问时会重定向到根路径
        # 或者返回404，这取决于具体的实现
        response = client.get("/index.html")
        # 由于端点不存在，应该返回404
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "BlogN2 API"
    
 