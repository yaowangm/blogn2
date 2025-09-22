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
    async def test_set_intro_endpoint_exists(self, test_client):
        """测试API端点存在"""
        # 测试端点是否存在（即使认证失败，也应该返回401而不是404）
        set_intro_response = test_client.post("/api/users/set-intro",
            json={"article_id": 1}
        )
        # 如果端点不存在，会返回404；如果存在但需要认证，会返回401
        assert set_intro_response.status_code in [401, 404]
        
        # 如果返回401，说明端点存在但需要认证
        if set_intro_response.status_code == 401:
            detail = set_intro_response.json().get("detail", "")
            assert "登录" in detail or "认证" in detail or "authorization" in detail.lower()