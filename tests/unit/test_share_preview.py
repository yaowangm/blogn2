"""分享预览 / 爬虫 UA：纯函数与 HTML 注入单元测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.constants import ArticleStatus
from src.utils.share_preview import (
    ArticleShareMeta,
    SITE_OG_IMAGE_PATH,
    absolute_url_from_site_base,
    get_request_public_base_url,
    inject_article_share_preview,
    is_share_preview_crawler,
    load_article_share_meta,
    load_blog_share_meta,
    load_thread_share_meta,
)


def test_is_share_preview_crawler_wechat():
    assert is_share_preview_crawler("Mozilla/5.0 MicroMessenger/8.0")
    assert is_share_preview_crawler("Mozilla/5.0 ... mpcrawler")
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


def test_absolute_url_from_site_base():
    assert absolute_url_from_site_base("", "/a") == "/a"
    assert absolute_url_from_site_base("https://x.com", "/a") == "https://x.com/a"
    assert absolute_url_from_site_base("https://x.com/", "/a") == "https://x.com/a"
    assert absolute_url_from_site_base("https://x.com", "https://y/z") == "https://y/z"


def test_inject_article_share_preview_absolute_og_when_public_base():
    meta = ArticleShareMeta(
        page_title="T",
        description="D",
        canonical_path="/article/42",
    )
    template = """<html><head>
    <title>x</title>
    <meta name="description" content="old">
    </head></html>"""
    out = inject_article_share_preview(
        template, meta, public_base_url="https://bloggern.com"
    )
    assert 'property="og:url" content="https://bloggern.com/article/42"' in out
    assert (
        f'property="og:image" content="https://bloggern.com{SITE_OG_IMAGE_PATH}"' in out
    )


def test_inject_article_share_preview_og_image_is_site_logo():
    meta = ArticleShareMeta(
        page_title='标题 "引号" <>&',
        description="摘要一行",
        canonical_path="/article/42",
    )
    template = """<html><head>
    <title>博客文章 - BlogN</title>
    <meta name="description" content="old">
    </head><body></body></html>"""
    out = inject_article_share_preview(template, meta)
    assert "<title>标题 \"引号\" &lt;&gt;&amp;</title>" in out
    assert 'property="og:type" content="article"' in out
    assert 'property="og:title"' in out
    assert 'property="og:url" content="/article/42"' in out
    assert f'property="og:image" content="{SITE_OG_IMAGE_PATH}"' in out
    assert 'name="description" content="摘要一行"' in out
    assert "twitter:" not in out
    assert "itemprop=" not in out


def test_inject_article_share_preview_website_og_type():
    meta = ArticleShareMeta(
        page_title="某博客",
        description="简介",
        canonical_path="/blog/1",
    )
    template = """<head><title>x</title><meta name="description" content="y"></head>"""
    out = inject_article_share_preview(template, meta, og_type="website")
    assert 'property="og:type" content="website"' in out
    assert f'property="og:image" content="{SITE_OG_IMAGE_PATH}"' in out
    assert "itemprop=" not in out


@pytest.mark.asyncio
async def test_load_article_share_meta_not_found():
    session = MagicMock()
    with patch("src.utils.share_preview.ProjectItemRepository") as PIR:
        PIR.return_value.get_by_id = AsyncMock(return_value=None)
        assert await load_article_share_meta(session, 999) is None


@pytest.mark.asyncio
async def test_load_article_share_meta_deleted_invisible():
    session = MagicMock()
    article = MagicMock()
    article.itemtype = ArticleStatus.DELETED
    article.name = "gone"
    with patch("src.utils.share_preview.ProjectItemRepository") as PIR:
        PIR.return_value.get_by_id = AsyncMock(return_value=article)
        assert await load_article_share_meta(session, 1) is None


@pytest.mark.asyncio
async def test_load_article_share_meta_ok_title_and_canonical():
    session = MagicMock()
    article = MagicMock()
    article.itemtype = ArticleStatus.NORMAL
    article.name = "标题A"
    article.projectid = 10
    article.comment = "# x\n正文"
    article.attachment = None

    project = MagicMock()
    project.name = "博客甲"

    with patch("src.utils.share_preview.ProjectItemRepository") as PIR, patch(
        "src.utils.share_preview.ProjectRepository"
    ) as PR:
        PIR.return_value.get_by_id = AsyncMock(return_value=article)
        PR.return_value.get_by_id = AsyncMock(return_value=project)

        meta = await load_article_share_meta(session, 42)
    assert meta is not None
    assert meta.page_title == "标题A - 博客甲 · BlogN"
    assert "正文" in meta.description
    assert meta.canonical_path == "/article/42"


@pytest.mark.asyncio
async def test_load_blog_share_meta_not_found():
    session = MagicMock()
    with patch("src.utils.share_preview.ProjectRepository") as PR:
        PR.return_value.get_by_id = AsyncMock(return_value=None)
        assert await load_blog_share_meta(session, 888) is None


@pytest.mark.asyncio
async def test_load_blog_share_meta_ok():
    session = MagicMock()
    project = MagicMock()
    project.name = "N"
    project.comment = "简介一行"
    project.userid = 1

    with patch("src.utils.share_preview.ProjectRepository") as PR:
        PR.return_value.get_by_id = AsyncMock(return_value=project)
        meta = await load_blog_share_meta(session, 7)

    assert meta is not None
    assert meta.page_title == "N - BlogN"
    assert meta.description == "简介一行"
    assert meta.canonical_path == "/blog/7"


@pytest.mark.asyncio
async def test_load_thread_share_meta_not_found():
    session = MagicMock()
    with patch("src.utils.share_preview.PostRepository") as PR:
        PR.return_value.get_thread_messages = AsyncMock(side_effect=ValueError("主题 1 不存在"))
        assert await load_thread_share_meta(session, 1) is None


@pytest.mark.asyncio
async def test_load_thread_share_meta_ok_from_main_post():
    session = MagicMock()
    main = {
        "id": 5,
        "subject": "主贴标题",
        "content": "正文内容",
        "userid": 2,
        "author_name": "张三",
        "is_main_post": True,
    }
    with patch("src.utils.share_preview.PostRepository") as PR:
        PR.return_value.get_thread_messages = AsyncMock(return_value=[main, {"is_main_post": False}])
        meta = await load_thread_share_meta(session, 5)
    assert meta is not None
    assert meta.page_title == "主贴标题 - 留言本 · BlogN"
    assert "正文内容" in meta.description
    assert meta.canonical_path == "/thread/5"
