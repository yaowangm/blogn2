"""
设为个人介绍功能集成测试
"""

import pytest
from unittest.mock import patch, mock_open
import tempfile
import os
from fastapi.testclient import TestClient
from src.main import app
from src.database import User, ProjectItem
from src.utils.cache import cache_manager


class TestSetIntroIntegration:
    """设为个人介绍功能集成测试类"""

    @pytest.fixture
    def test_client(self, test_client):
        """测试客户端"""
        return test_client

    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            "name": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "state": 1
        }

    @pytest.fixture
    def sample_article_data(self):
        """示例文章数据"""
        return {
            "name": "测试个人介绍文章",
            "content": "这是一篇用于测试个人介绍功能的文章",
            "attachment": "test_avatar.jpg"
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_intro_complete_flow(self, test_client, sample_user_data, sample_article_data, test_data_tracker):
        """测试完整的设为个人介绍流程"""
        # 1. 注册用户
        register_response = test_client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 200
        user_data = register_response.json()
        user_id = user_data["user_id"]
        test_data_tracker.add_user(user_id)

        # 2. 登录获取token
        login_response = test_client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]

        # 3. 创建博客项目
        project_response = test_client.post("/api/projects", 
            json={"name": "测试博客", "description": "测试博客描述"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert project_response.status_code == 200
        project_data = project_response.json()
        project_id = project_data["id"]
        test_data_tracker.add_project(project_id)

        # 4. 创建文章
        article_response = test_client.post(f"/api/projects/{project_id}/items",
            json=sample_article_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert article_response.status_code == 200
        article_data = article_response.json()
        article_id = article_data["id"]
        test_data_tracker.add_article(article_id)

        # 5. 模拟文件上传（创建测试图片文件）
        test_image_path = None
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # 创建一个简单的测试图片
            from PIL import Image
            img = Image.new('RGB', (400, 300), color='blue')
            img.save(tmp_file.name, 'JPEG')
            test_image_path = tmp_file.name

        try:
            # 6. 上传附件图片
            with open(test_image_path, 'rb') as f:
                upload_response = test_client.post("/api/upload",
                    files={"file": ("test_avatar.jpg", f, "image/jpeg")},
                    headers={"Authorization": f"Bearer {token}"}
                )
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            attachment_filename = upload_data["filename"]

            # 7. 更新文章添加附件
            update_article_response = test_client.put(f"/api/projects/{project_id}/items/{article_id}",
                json={
                    "name": sample_article_data["name"],
                    "content": sample_article_data["content"],
                    "attachment": attachment_filename
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert update_article_response.status_code == 200

            # 8. 设置个人介绍
            with patch('os.path.exists', return_value=True), \
                 patch('os.makedirs'), \
                 patch('os.path.join') as mock_join, \
                 patch('src.utils.image_utils.ImageProcessor') as mock_image_processor_class:
                
                # 模拟路径拼接
                mock_join.side_effect = lambda *args: "/".join(args)
                
                # 模拟图片处理器
                mock_image_processor = patch('src.utils.image_utils.ImageProcessor').start()
                mock_image_processor.return_value.resize_and_save_image = patch('src.utils.image_utils.ImageProcessor.resize_and_save_image').start()
                
                # 模拟配置
                with patch('src.config.app.validate_app_config') as mock_config:
                    mock_config.return_value = {
                        "upload_dir": "../pic/blogn_img/upload",
                        "avatar_dir": "../pic/blogn_img/userlogo"
                    }
                    
                    set_intro_response = test_client.post("/api/users/set-intro",
                        json={"article_id": article_id},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    assert set_intro_response.status_code == 200
                    set_intro_data = set_intro_response.json()
                    assert set_intro_data["success"] is True
                    assert set_intro_data["article_id"] == article_id
                    assert set_intro_data["article_title"] == sample_article_data["name"]

        finally:
            # 清理测试图片文件
            if test_image_path and os.path.exists(test_image_path):
                os.unlink(test_image_path)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_intro_unauthorized_user(self, test_client, sample_user_data, test_data_tracker):
        """测试未授权用户设置个人介绍"""
        # 1. 注册用户
        register_response = test_client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 200
        user_data = register_response.json()
        user_id = user_data["user_id"]
        test_data_tracker.add_user(user_id)

        # 2. 登录获取token
        login_response = test_client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]

        # 3. 尝试设置不存在的文章为个人介绍
        set_intro_response = test_client.post("/api/users/set-intro",
            json={"article_id": 99999},  # 不存在的文章ID
            headers={"Authorization": f"Bearer {token}"}
        )
        assert set_intro_response.status_code == 404
        assert "文章不存在" in set_intro_response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_intro_no_authentication(self, test_client):
        """测试未认证用户设置个人介绍"""
        set_intro_response = test_client.post("/api/users/set-intro",
            json={"article_id": 1}
        )
        assert set_intro_response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_intro_missing_article_id(self, test_client, sample_user_data, test_data_tracker):
        """测试缺少文章ID参数"""
        # 1. 注册用户
        register_response = test_client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 200
        user_data = register_response.json()
        user_id = user_data["user_id"]
        test_data_tracker.add_user(user_id)

        # 2. 登录获取token
        login_response = test_client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]

        # 3. 尝试设置个人介绍但缺少article_id
        set_intro_response = test_client.post("/api/users/set-intro",
            json={},  # 缺少article_id
            headers={"Authorization": f"Bearer {token}"}
        )
        assert set_intro_response.status_code == 400
        assert "缺少文章ID参数" in set_intro_response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_intro_other_user_article(self, test_client, test_data_tracker):
        """测试设置其他用户的文章为个人介绍"""
        # 1. 注册第一个用户
        user1_data = {
            "name": "user1",
            "email": "user1@example.com",
            "password": "password123",
            "state": 1
        }
        register_response = test_client.post("/api/auth/register", json=user1_data)
        assert register_response.status_code == 200
        user1_id = register_response.json()["user_id"]
        test_data_tracker.add_user(user1_id)

        # 2. 注册第二个用户
        user2_data = {
            "name": "user2",
            "email": "user2@example.com",
            "password": "password123",
            "state": 1
        }
        register_response = test_client.post("/api/auth/register", json=user2_data)
        assert register_response.status_code == 200
        user2_id = register_response.json()["user_id"]
        test_data_tracker.add_user(user2_id)

        # 3. 用户1登录
        login_response = test_client.post("/api/auth/login", json={
            "email": user1_data["email"],
            "password": user1_data["password"]
        })
        assert login_response.status_code == 200
        user1_token = login_response.json()["access_token"]

        # 4. 用户2登录
        login_response = test_client.post("/api/auth/login", json={
            "email": user2_data["email"],
            "password": user2_data["password"]
        })
        assert login_response.status_code == 200
        user2_token = login_response.json()["access_token"]

        # 5. 用户1创建博客和文章
        project_response = test_client.post("/api/projects", 
            json={"name": "用户1的博客", "description": "用户1的博客描述"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]
        test_data_tracker.add_project(project_id)

        article_response = test_client.post(f"/api/projects/{project_id}/items",
            json={"name": "用户1的文章", "content": "用户1的文章内容"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert article_response.status_code == 200
        article_id = article_response.json()["id"]
        test_data_tracker.add_article(article_id)

        # 6. 用户2尝试设置用户1的文章为个人介绍
        set_intro_response = test_client.post("/api/users/set-intro",
            json={"article_id": article_id},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert set_intro_response.status_code == 403
        assert "只有文章作者可以设置个人介绍" in set_intro_response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_intro_article_without_attachment(self, test_client, sample_user_data, test_data_tracker):
        """测试设置没有附件的文章为个人介绍"""
        # 1. 注册用户
        register_response = test_client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 200
        user_data = register_response.json()
        user_id = user_data["user_id"]
        test_data_tracker.add_user(user_id)

        # 2. 登录获取token
        login_response = test_client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]

        # 3. 创建博客项目
        project_response = test_client.post("/api/projects", 
            json={"name": "测试博客", "description": "测试博客描述"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]
        test_data_tracker.add_project(project_id)

        # 4. 创建没有附件的文章
        article_response = test_client.post(f"/api/projects/{project_id}/items",
            json={"name": "无附件文章", "content": "没有附件的文章内容"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert article_response.status_code == 200
        article_id = article_response.json()["id"]
        test_data_tracker.add_article(article_id)

        # 5. 尝试设置没有附件的文章为个人介绍
        set_intro_response = test_client.post("/api/users/set-intro",
            json={"article_id": article_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert set_intro_response.status_code == 400
        assert "文章没有附件图片，无法设为个人介绍" in set_intro_response.json()["detail"]
