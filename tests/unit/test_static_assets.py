"""静态资源版本与 HTML 缓存破除测试。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.utils import static_assets
from src.utils.middleware_handlers import MiddlewareHandler
from src.utils.page_handlers import PageHandler


@pytest.fixture(autouse=True)
def clear_static_version_cache():
    static_assets.get_static_version.cache_clear()
    yield
    static_assets.get_static_version.cache_clear()


class TestStaticAssets:
    def test_append_static_version_adds_query_param(self, monkeypatch):
        monkeypatch.setenv("STATIC_VERSION", "testver")
        static_assets.get_static_version.cache_clear()
        assert (
            static_assets.append_static_version("/static/css/main.css")
            == "/static/css/main.css?v=testver"
        )

    def test_reads_static_version_file(self, monkeypatch, tmp_path):
        monkeypatch.delenv("STATIC_VERSION", raising=False)
        static_assets.get_static_version.cache_clear()
        version_file = tmp_path / ".static_version"
        version_file.write_text("20250609120000\n", encoding="utf-8")
        monkeypatch.setattr(static_assets, "_STATIC_VERSION_FILE", version_file)
        assert static_assets.get_static_version() == "20250609120000"

    def test_append_static_version_skips_when_present(self, monkeypatch):
        monkeypatch.setenv("STATIC_VERSION", "testver")
        static_assets.get_static_version.cache_clear()
        url = "/static/css/main.css?v=existing"
        assert static_assets.append_static_version(url) == url

    def test_inject_static_version_into_html(self, monkeypatch):
        monkeypatch.setenv("STATIC_VERSION", "abc123")
        static_assets.get_static_version.cache_clear()
        html = '<link rel="stylesheet" href="/static/css/main.css">'
        result = static_assets.inject_static_version_into_html(html)
        assert 'href="/static/css/main.css?v=abc123"' in result

    def test_build_versioned_html_response(self, monkeypatch):
        monkeypatch.setenv("STATIC_VERSION", "rel1")
        static_assets.get_static_version.cache_clear()
        html = (
            "<html><head><title>x</title></head>"
            '<body><script src="/static/js/app.js"></script></body></html>'
        )
        response = static_assets.build_versioned_html_response(html)
        body = response.body.decode("utf-8")
        assert 'window.__BLOGN_STATIC_VERSION__="rel1"' in body
        assert '/static/js/utils/static-url.js?v=rel1' in body
        assert '/static/js/app.js?v=rel1' in body
        assert response.headers["Cache-Control"] == "no-cache, must-revalidate"


class TestPageHandlerVersionedHtml:
    def test_serve_index_html_includes_version(self, monkeypatch):
        monkeypatch.setenv("STATIC_VERSION", "idx99")
        static_assets.get_static_version.cache_clear()
        response = PageHandler._serve_static_html("index.html")
        body = response.body.decode("utf-8")
        assert 'window.__BLOGN_STATIC_VERSION__="idx99"' in body
        assert "/static/css/main.css?v=idx99" in body


class TestStaticCacheMiddleware:
    @pytest.fixture
    def app(self):
        app = FastAPI()
        MiddlewareHandler.setup_cache_control_middleware(app)
        MiddlewareHandler.setup_static_files(app)

        @app.get("/page")
        async def html_page():
            return static_assets.build_versioned_html_response("<html><head></head><body></body></html>")

        return app

    def test_versioned_static_asset_is_long_cache(self, app, monkeypatch):
        monkeypatch.setenv("STATIC_VERSION", "mw1")
        static_assets.get_static_version.cache_clear()
        client = TestClient(app)
        resp = client.get("/static/css/main.css?v=mw1")
        assert resp.status_code == 200
        assert "immutable" in resp.headers.get("Cache-Control", "")
        assert resp.headers.get("ETag")

    def test_unversioned_static_asset_must_revalidate(self, app):
        client = TestClient(app)
        resp = client.get("/static/css/main.css")
        assert resp.status_code == 200
        assert resp.headers.get("Cache-Control") == "public, max-age=0, must-revalidate"
        assert resp.headers.get("ETag")
