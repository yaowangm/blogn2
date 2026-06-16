"""
POST /api/auth/login 集成测试：真实 PostgreSQL + 完整认证链。

覆盖密码哈希校验、User 仓储、AuthSecurityService 读写 user_auth_security_state。
与 tests/unit/test_auth_controller.py（mock 依赖、不测真实登录）互补。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session

from src.models.user import User
from src.services.auth_service import AuthService


def _unique_username() -> str:
    return f"itest_login_{uuid.uuid4().hex[:16]}"


@pytest.mark.integration
class TestAuthLoginIntegration:
    """真实 HTTP + 数据库的登录流程。"""

    def test_login_success_returns_tokens(
        self, test_client, real_sync_session_with_commit: Session
    ):
        username = _unique_username()
        plain_password = "IntegrationTest_Pw1!"
        hasher = AuthService(AsyncMock(), "test-secret-for-hash-only")
        user = User(
            name=username,
            email=f"{username}@example.invalid",
            password=hasher.hash_password(plain_password),
            regtime=datetime(2024, 1, 1, 12, 0, 0),
            state=1,
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        real_sync_session_with_commit.commit()

        response = test_client.post(
            "/api/auth/login",
            json={"username_or_email": username, "password": plain_password},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data.get("token_type") == "bearer"
        assert data.get("access_token")
        assert data.get("refresh_token")
        # 库中 name 可能为定长填充，与 strip 后比较
        assert (data.get("user") or {}).get("name", "").strip() == username

    def test_login_wrong_password_returns_401(
        self, test_client, real_sync_session_with_commit: Session
    ):
        username = _unique_username()
        plain_password = "Right_Pw_1!"
        hasher = AuthService(AsyncMock(), "x")
        user = User(
            name=username,
            email=f"{username}@example.invalid",
            password=hasher.hash_password(plain_password),
            regtime=datetime(2024, 1, 1, 12, 0, 0),
            state=1,
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        real_sync_session_with_commit.commit()

        response = test_client.post(
            "/api/auth/login",
            json={"username_or_email": username, "password": "wrong_password"},
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json().get("detail", "")

    def test_login_by_email(
        self, test_client, real_sync_session_with_commit: Session
    ):
        username = _unique_username()
        email = f"{username}@mail.example.invalid"
        plain_password = "EmailLogin_Pw1!"
        hasher = AuthService(AsyncMock(), "x")
        user = User(
            name=username,
            email=email,
            password=hasher.hash_password(plain_password),
            regtime=datetime(2024, 1, 1, 12, 0, 0),
            state=1,
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        real_sync_session_with_commit.commit()

        response = test_client.post(
            "/api/auth/login",
            json={"username_or_email": email, "password": plain_password},
        )
        assert response.status_code == 200, response.text
        assert (response.json().get("user") or {}).get("email", "").strip() == email
