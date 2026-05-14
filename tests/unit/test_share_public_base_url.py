"""get_share_public_base_url：分享用站点根与 BASE_URL 解耦。"""

from src.config.app import get_share_public_base_url


def test_get_share_public_base_url_prefers_share_over_base(monkeypatch):
    monkeypatch.setenv("SHARE_BASE_URL", "https://bloggern.com")
    monkeypatch.setenv("BASE_URL", "http://localhost:8000")
    assert get_share_public_base_url() == "https://bloggern.com"


def test_get_share_public_base_url_public_url_fallback(monkeypatch):
    monkeypatch.delenv("SHARE_BASE_URL", raising=False)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://x.example")
    monkeypatch.setenv("BASE_URL", "http://localhost:8000")
    assert get_share_public_base_url() == "https://x.example"


def test_get_share_public_base_url_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("SHARE_BASE_URL", "https://bloggern.com/")
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    assert get_share_public_base_url() == "https://bloggern.com"


def test_get_share_public_base_url_ignores_empty_share(monkeypatch):
    monkeypatch.delenv("SHARE_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.setenv("BASE_URL", "https://y.example")
    assert get_share_public_base_url() == "https://y.example"
