"""PageHandler 分享预览分支：_maybe_share_preview_html 单元测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from starlette.requests import Request

from src.utils.page_handlers import PageHandler
from src.utils.share_preview import ArticleShareMeta


def _http_scope(*, user_agent: str) -> dict:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/article/1",
        "raw_path": b"/article/1",
        "root_path": "",
        "scheme": "https",
        "query_string": b"",
        "headers": [
            (b"host", b"example.com"),
            (b"user-agent", user_agent.encode("utf-8")),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("example.com", 443),
    }


@pytest.mark.asyncio
async def test_maybe_share_preview_non_crawler_returns_file_response():
    """非爬虫：不调 load_share_meta，直接 FileResponse。"""
    request = Request(_http_scope(user_agent="Mozilla/5.0 Chrome/120.0"))
    session = MagicMock()
    load = AsyncMock()

    resp = await PageHandler._maybe_share_preview_html(
        request,
        session,
        static_filename="article.html",
        load_share_meta=load,
        resource_id=99,
        not_found_detail="文章不存在",
        og_type="article",
    )
    assert isinstance(resp, FileResponse)
    load.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_share_preview_crawler_returns_html_with_og():
    """爬虫：读真实 article.html 模板并注入 meta。"""
    request = Request(_http_scope(user_agent="Mozilla/5.0 MicroMessenger/8.0"))
    session = MagicMock()
    meta = ArticleShareMeta(
        page_title="UT标题",
        description="UT摘要",
        og_image_absolute="https://example.com/static/favicon.ico",
        canonical_url="https://example.com/article/99",
    )
    load = AsyncMock(return_value=meta)

    resp = await PageHandler._maybe_share_preview_html(
        request,
        session,
        static_filename="article.html",
        load_share_meta=load,
        resource_id=99,
        not_found_detail="文章不存在",
        og_type="article",
    )
    assert isinstance(resp, HTMLResponse)
    body = resp.body.decode("utf-8")
    assert "og:title" in body
    assert "UT标题" in body
    load.assert_called_once()


@pytest.mark.asyncio
async def test_maybe_share_preview_crawler_not_found_raises_404():
    """爬虫且 load_share_meta 返回 None：HTTPException 404。"""
    request = Request(_http_scope(user_agent="facebookexternalhit/1.1"))
    session = MagicMock()
    load = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await PageHandler._maybe_share_preview_html(
            request,
            session,
            static_filename="article.html",
            load_share_meta=load,
            resource_id=999,
            not_found_detail="文章不存在",
            og_type="article",
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "文章不存在"
