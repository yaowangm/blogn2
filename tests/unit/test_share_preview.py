"""分享预览 / 爬虫 UA：纯函数与 HTML 注入单元测试。"""

import pytest

from src.utils.share_preview import (
    ArticleShareMeta,
    get_request_public_base_url,
    inject_article_share_preview,
    is_share_preview_crawler,
)


def test_is_share_preview_crawler_wechat():
    assert is_share_preview_crawler("Mozilla/5.0 MicroMessenger/8.0")
    assert is_share_preview_crawler("facebookexternalhit/1.1")
    assert not is_share_preview_crawler("Mozilla/5.0 Chrome/120.0.0.0")
    assert not is_share_preview_crawler(None)
    assert not is_share_preview_crawler("")


def test_get_request_public_base_url_forwarded():
    base = get_request_public_base_url(
        url_scheme="http",
        url_netloc="internal:8000",
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "blog.example.com"},
    )
    assert base == "https://blog.example.com"


def test_get_request_public_base_url_fallback_netloc():
    base = get_request_public_base_url(
        url_scheme="https",
        url_netloc="localhost:8000",
        headers={},
    )
    assert base == "https://localhost:8000"


def test_inject_article_share_preview():
    meta = ArticleShareMeta(
        page_title='标题 "引号" <>&',
        description="摘要一行",
        og_image_absolute="https://example.com/static/a.png",
        canonical_url="https://example.com/article/42",
    )
    template = """<html><head>
    <title>博客文章 - BlogN</title>
    <meta name="description" content="old">
    </head><body></body></html>"""
    out = inject_article_share_preview(template, meta)
    assert "<title>标题 \"引号\" &lt;&gt;&amp;</title>" in out
    assert 'property="og:type" content="article"' in out
    assert 'property="og:title"' in out
    assert "https://example.com/article/42" in out
    assert "https://example.com/static/a.png" in out
    assert 'name="description" content="摘要一行"' in out


def test_inject_article_share_preview_website_og_type():
    meta = ArticleShareMeta(
        page_title="某博客",
        description="简介",
        og_image_absolute="https://example.com/favicon.ico",
        canonical_url="https://example.com/blog/1",
    )
    template = """<head><title>x</title><meta name="description" content="y"></head>"""
    out = inject_article_share_preview(template, meta, og_type="website")
    assert 'property="og:type" content="website"' in out
