"""
安全相关中间件与配置测试
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config.app import (
    get_cors_allow_origins,
    get_cors_allow_methods,
    get_cors_allow_headers,
    get_cors_allow_credentials,
)
from src.utils.middleware_handlers import MiddlewareHandler


class TestCorsConfigFunctions:
    def test_get_cors_allow_origins_from_env(self, monkeypatch):
        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://a.com, https://b.com")
        assert get_cors_allow_origins() == ["https://a.com", "https://b.com"]

    def test_get_cors_allow_methods_default(self, monkeypatch):
        monkeypatch.delenv("CORS_ALLOW_METHODS", raising=False)
        assert get_cors_allow_methods() == ["*"]

    def test_get_cors_allow_headers_from_env(self, monkeypatch):
        monkeypatch.setenv("CORS_ALLOW_HEADERS", "Authorization, Content-Type")
        assert get_cors_allow_headers() == ["Authorization", "Content-Type"]

    def test_get_cors_allow_credentials(self, monkeypatch):
        monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "true")
        assert get_cors_allow_credentials() is True


class TestSecurityMiddleware:
    @pytest.fixture
    def app(self):
        app = FastAPI()
        MiddlewareHandler.setup_cache_control_middleware(app)

        @app.get("/reset-password")
        async def reset_password_page():
            return {"ok": True}

        @app.get("/api/users/me")
        async def me():
            return {"ok": True}

        @app.get("/public")
        async def public():
            return {"ok": True}

        return app

    def test_reset_password_has_no_referrer_policy(self, app):
        client = TestClient(app)
        resp = client.get("/reset-password")
        assert resp.status_code == 200
        assert resp.headers.get("Referrer-Policy") == "no-referrer"

    def test_users_api_has_no_cache_headers(self, app):
        client = TestClient(app)
        resp = client.get("/api/users/me")
        assert resp.status_code == 200
        assert "no-store" in resp.headers.get("Cache-Control", "")
        assert resp.headers.get("Pragma") == "no-cache"
        assert resp.headers.get("Expires") == "0"

    def test_public_path_not_forced_no_cache(self, app):
        client = TestClient(app)
        resp = client.get("/public")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") is None
