"""分享预览 / 爬虫 UA：纯函数与 HTML 注入单元测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.constants import ArticleStatus
from src.utils.share_preview import (
    ArticleShareMeta,
    SITE_ICON_PATH,
    SITE_NAME,
    absolute_url_from_site_base,
    get_request_public_base_url,
    inject_article_share_preview,
    is_share_preview_crawler,
    load_article_share_meta,
    load_blog_share_meta,
    load_thread_share_meta,
    merge_public_base_with_config,
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


def test_merge_public_base_https_from_config_same_host():
    assert merge_public_base_with_config(
        "http://bloggern.com",
        "https://bloggern.com",
    ) == "https://bloggern.com"


def test_merge_public_base_upgrades_inferred_when_config_other_host():
    assert merge_public_base_with_config(
        "http://bloggern.com",
        "http://localhost:8000",
    ) == "https://bloggern.com"


def test_merge_public_base_empty_inferred_uses_config_origin():
    assert merge_public_base_with_config("", "https://bloggern.com/") == "https://bloggern.com"


def test_merge_public_base_empty_inferred_upgrades_http_config_origin():
    assert merge_public_base_with_config("", "http://bloggern.com/") == "https://bloggern.com"


def test_merge_public_base_invalid_config_ignored():
    assert merge_public_base_with_config("https://x.com", "") == "https://x.com"
    assert merge_public_base_with_config("https://x.com", "not-a-url") == "https://x.com"
    assert merge_public_base_with_config("http://x.com", "") == "https://x.com"
    assert merge_public_base_with_config("http://x.com", "not-a-url") == "https://x.com"


def test_merge_same_host_both_http_non_loopback_becomes_https():
    assert (
        merge_public_base_with_config("http://bloggern.com", "http://bloggern.com")
        == "https://bloggern.com"
    )


def test_merge_same_host_both_http_respects_og_allow(monkeypatch):
    monkeypatch.setenv("OG_ALLOW_HTTP_PUBLIC_BASE", "1")
    assert (
        merge_public_base_with_config("http://bloggern.com", "http://bloggern.com")
        == "http://bloggern.com"
    )


def test_merge_localhost_both_http_stays_http():
    assert (
        merge_public_base_with_config(
            "http://localhost:8000",
            "http://localhost:8000",
        )
        == "http://localhost:8000"
    )


def test_merge_public_base_matches_by_hostname_port_insensitive():
    assert merge_public_base_with_config(
        "http://bloggern.com:443",
        "https://bloggern.com",
    ) == "https://bloggern.com"


def test_absolute_url_from_site_base():
    assert absolute_url_from_site_base("", "/a") == "/a"
    assert absolute_url_from_site_base("https://x.com", "/a") == "https://x.com/a"
    assert absolute_url_from_site_base("https://x.com/", "/a") == "https://x.com/a"
    assert absolute_url_from_site_base("https://x.com", "https://y/z") == "https://y/z"
    assert absolute_url_from_site_base("https://x.com", "http://y/z") == "https://y/z"


def test_inject_article_share_preview_absolute_og_when_public_base():
    meta = ArticleShareMeta(
        page_title="T",
        description="D",
        canonical_path="/article/42",
        image_path="/upload/cover.jpg",
    )
    template = """<html><head>
    <title>x</title>
    <meta name="description" content="old">
    </head></html>"""
    out = inject_article_share_preview(
        template, meta, public_base_url="https://bloggern.com"
    )
    assert '<link rel="canonical" href="https://bloggern.com/article/42">' in out
    assert (
        f'<link rel="icon" type="image/png" href="https://bloggern.com{SITE_ICON_PATH}" sizes="32x32">'
        in out
    )
    assert (
        f'<link rel="apple-touch-icon" href="https://bloggern.com{SITE_ICON_PATH}">'
        in out
    )
    assert (
        f'<link rel="shortcut icon" type="image/png" href="https://bloggern.com{SITE_ICON_PATH}">'
        in out
    )
    assert 'property="og:url" content="https://bloggern.com/article/42"' in out
    assert f'property="og:site_name" content="{SITE_NAME}"' in out
    assert (
        'property="og:image" content="https://bloggern.com/upload/cover.jpg"' in out
    )
    assert (
        'property="og:image:secure_url" content="https://bloggern.com/upload/cover.jpg"'
        in out
    )


def test_inject_article_share_preview_og_image_is_site_logo():
    meta = ArticleShareMeta(
        page_title='标题 "引号" <>&',
        description="摘要一行",
        canonical_path="/article/42",
        image_path="/upload/a.png",
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
    assert f'property="og:site_name" content="{SITE_NAME}"' in out
    assert 'property="og:image" content="/upload/a.png"' in out
    assert 'property="og:image:alt" content="标题 &quot;引号&quot; &lt;&gt;&amp;"' in out
    assert 'name="description" content="摘要一行"' in out
    assert "twitter:" not in out
    assert "itemprop=" not in out


def test_inject_article_share_preview_omits_og_image_without_content_image():
    meta = ArticleShareMeta(
        page_title="某博客",
        description="简介",
        canonical_path="/blog/1",
    )
    template = """<head><title>x</title><meta name="description" content="y"></head>"""
    out = inject_article_share_preview(template, meta)
    assert 'property="og:image"' not in out
    assert 'property="og:image:secure_url"' not in out
    assert '<link rel="apple-touch-icon" href="/static/favicon.png">' in out
    assert '<link rel="shortcut icon" type="image/png" href="/static/favicon.png">' in out


def test_inject_article_share_preview_website_og_type():
    meta = ArticleShareMeta(
        page_title="某博客",
        description="简介",
        canonical_path="/blog/1",
        image_path="/avatar/1/s_7.jpg",
    )
    template = """<head><title>x</title><meta name="description" content="y"></head>"""
    out = inject_article_share_preview(template, meta, og_type="website")
    assert 'property="og:type" content="website"' in out
    assert 'property="og:image" content="/avatar/1/s_7.jpg"' in out
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
    article.attachment = "cover.jpg"

    project = MagicMock()
    project.name = "博客甲"

    with patch("src.utils.share_preview.ProjectItemRepository") as PIR, patch(
        "src.utils.share_preview.ProjectRepository"
    ) as PR, patch("src.utils.share_preview.AttachmentRepository") as AR:
        PIR.return_value.get_by_id = AsyncMock(return_value=article)
        PR.return_value.get_by_id = AsyncMock(return_value=project)
        AR.return_value.get_by_project_item_id = AsyncMock(return_value=[])

        meta = await load_article_share_meta(session, 42)
    assert meta is not None
    assert meta.page_title == "标题A - 博客甲 · BlogN"
    assert "正文" in meta.description
    assert meta.canonical_path == "/article/42"
    assert meta.image_path == "/upload/cover.jpg"


@pytest.mark.asyncio
async def test_load_article_share_meta_uses_first_image_attachment_table_fallback():
    session = MagicMock()
    article = MagicMock()
    article.itemtype = ArticleStatus.NORMAL
    article.name = "标题A"
    article.projectid = None
    article.comment = "正文"
    article.attachment = None

    non_image = MagicMock()
    non_image.linkstr = "/upload/doc.pdf"
    image = MagicMock()
    image.linkstr = "/upload/pic.webp"

    with patch("src.utils.share_preview.ProjectItemRepository") as PIR, patch(
        "src.utils.share_preview.ProjectRepository"
    ) as PR, patch("src.utils.share_preview.AttachmentRepository") as AR:
        PIR.return_value.get_by_id = AsyncMock(return_value=article)
        PR.return_value.get_by_id = AsyncMock(return_value=None)
        AR.return_value.get_by_project_item_id = AsyncMock(
            return_value=[non_image, image]
        )

        meta = await load_article_share_meta(session, 42)

    assert meta is not None
    assert meta.image_path == "/upload/pic.webp"


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

    with patch("src.utils.share_preview.ProjectRepository") as PR, patch(
        "src.utils.share_preview.check_avatar_exists", return_value="/avatar/1/s_1.jpg"
    ):
        PR.return_value.get_by_id = AsyncMock(return_value=project)
        meta = await load_blog_share_meta(session, 7)

    assert meta is not None
    assert meta.page_title == "N - BlogN"
    assert meta.description == "简介一行"
    assert meta.canonical_path == "/blog/7"
    assert meta.image_path == "/avatar/1/s_1.jpg"


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
