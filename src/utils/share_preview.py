"""
社交分享 / 爬虫预览：在首包 HTML 中替换标题、摘要，并注入 Open Graph。

微信等不执行 JavaScript，只读首包 HTML；普通浏览器仍走 SPA。
``property="og:image"`` 使用 PNG；注入时若可解析站点前缀则写 **绝对 URL**（微信等抓取常不认相对路径）。
站内 ``<link rel="icon">`` 仍为 ``/static/...`` 相对路径。不注入 ``itemprop``。
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from typing import Mapping, Optional
from urllib.parse import urlparse

from sqlmodel.ext.asyncio.session import AsyncSession

from src.constants import ArticleStatus
from src.repositories.post_repository import PostRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.project_repository import ProjectRepository
from src.utils.permission_manager import permission_manager

# User-Agent 子串（大小写不敏感），覆盖微信与常见社交/预览爬虫
_SHARE_PREVIEW_UA_MARKERS: tuple[str, ...] = (
    "micromessenger",  # 微信内置浏览器
    "mpcrawler",  # 微信链接预览/收录等场景常见（UA 未必含 MicroMessenger）
    "facebookexternalhit",
    "facebot",
    "twitterbot",
    "linkedinbot",
    "slackbot",
    "slack-imgproxy",
    "telegrambot",
    "whatsapp",
    "discordbot",
    "pinterest",
    "vkshare",
    "quora link preview",
)

# 分享预览 og:image：PNG（由 logo-light.svg 栅格化，便于微信等；路径见静态文件）
SITE_OG_IMAGE_PATH = "/static/images/site-share-icon.png"


def is_share_preview_crawler(user_agent: Optional[str]) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(marker in ua for marker in _SHARE_PREVIEW_UA_MARKERS)


def get_request_public_base_url(
    *,
    url_scheme: str,
    url_netloc: str,
    headers: Mapping[str, str],
) -> str:
    """
    生成对外绝对 URL 前缀（其它需要完整 URL 的场景可用）。
    优先使用反向代理常见的 X-Forwarded-*，否则回退到请求 URL。
    """
    h = {k.lower(): v for k, v in headers.items()}
    proto = (h.get("x-forwarded-proto") or url_scheme or "http").strip()
    host = (h.get("x-forwarded-host") or h.get("host") or url_netloc or "").strip()
    if host and proto:
        return f"{proto}://{host}".rstrip("/")
    if url_netloc and url_scheme:
        return f"{url_scheme}://{url_netloc}".rstrip("/")
    return ""


def merge_public_base_with_config(inferred: str, config_base: str) -> str:
    """
    将 ``get_request_public_base_url`` 的结果与 ``get_share_public_base_url()`` 等配置合并。

    反向代理若未传 ``X-Forwarded-Proto``，推断结果常为 ``http://``。当配置中的主机名与推断一致时，
    采用配置中的 scheme；任一侧为 ``https`` 时结果固定为 ``https``。

    若两侧仍为 ``http`` 且主机非 loopback（典型生产域名），默认升级为 ``https://…``，避免
    ``og:image`` 使用 HTTP 导致微信等无法拉图。纯 HTTP 内网需设置环境变量
    ``OG_ALLOW_HTTP_PUBLIC_BASE=1`` 关闭该行为。
    """
    inferred = (inferred or "").strip().rstrip("/")
    config_base = (config_base or "").strip().rstrip("/")
    if not config_base.startswith(("http://", "https://")):
        return inferred
    pc = urlparse(config_base)
    if not pc.scheme or not pc.netloc:
        return inferred
    conf_origin = f"{pc.scheme}://{pc.netloc}".rstrip("/")
    if not inferred:
        return conf_origin
    pi = urlparse(inferred)
    if not pi.scheme or not pi.netloc:
        return inferred
    inf_origin = f"{pi.scheme}://{pi.netloc}".rstrip("/")
    hi = pi.hostname.lower() if pi.hostname else ""
    hc = pc.hostname.lower() if pc.hostname else ""
    if not hi or not hc or hi != hc:
        return inf_origin

    allow_http = os.getenv("OG_ALLOW_HTTP_PUBLIC_BASE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    loopback = hi in ("localhost", "127.0.0.1", "[::1]")
    if loopback or allow_http:
        return conf_origin
    if pi.scheme == "https" or pc.scheme == "https":
        return f"https://{pc.netloc}".rstrip("/")
    if pi.scheme == "http" and pc.scheme == "http":
        return f"https://{pc.netloc}".rstrip("/")
    return conf_origin


def absolute_url_from_site_base(public_base_url: str, path: str) -> str:
    """在 ``public_base_url`` 非空时，把站内路径 ``path`` 拼成绝对 URL；否则原样返回 ``path``。"""
    base = (public_base_url or "").strip().rstrip("/")
    p = (path or "").strip()
    if not base or not p:
        return p
    if p.startswith(("http://", "https://", "//")):
        return p
    if p.startswith("/"):
        return f"{base}{p}"
    return f"{base}/{p.lstrip('/')}"


def _markdown_to_plain_preview(
    text: Optional[str],
    max_len: int = 200,
    empty_fallback: str = "BlogN2 博客文章",
) -> str:
    if not text or not str(text).strip():
        return empty_fallback
    s = str(text).strip()
    s = re.sub(r"```[\s\S]*?```", " ", s)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"^#+\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[*_]{1,3}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[: max_len - 1].rstrip() + "…"
    return s or empty_fallback


@dataclass
class ArticleShareMeta:
    """分享注入用元数据（文章 / 博客首页 / 留言主题）。

    ``canonical_path`` 为以 ``/`` 开头的站内路径。预览图 URL 由注入函数固定为 ``SITE_OG_IMAGE_PATH``（PNG）。
    """

    page_title: str
    description: str
    canonical_path: str


async def load_article_share_meta(
    session: AsyncSession,
    article_id: int,
) -> Optional[ArticleShareMeta]:
    """
    读取用于分享预览的元数据（与公开文章 API 一致的可见性：已删除对爬虫不可见）。
    """
    item_repo = ProjectItemRepository(session)
    project_repo = ProjectRepository(session)

    article = await item_repo.get_by_id(article_id)
    if not article:
        return None
    if article.itemtype == ArticleStatus.DELETED and not permission_manager.can_manage_system(None):
        return None

    project_name = None
    if article.projectid:
        project = await project_repo.get_by_id(article.projectid)
        if project:
            project_name = project.name

    title = (article.name or "").strip() or "博客文章"
    if project_name:
        page_title = f"{title} - {project_name} · BlogN"
    else:
        page_title = f"{title} - BlogN"

    description = _markdown_to_plain_preview(article.comment)
    canonical_path = f"/article/{article_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        canonical_path=canonical_path,
    )


async def load_thread_share_meta(
    session: AsyncSession,
    thread_id: int,
) -> Optional[ArticleShareMeta]:
    """
    留言本主题页 /thread/{id} 的分享元数据（主贴不存在则 None，与 /api/thread/{id} 一致）。
    """
    post_repo = PostRepository(session)
    try:
        messages = await post_repo.get_thread_messages(thread_id)
    except ValueError:
        return None

    main = messages[0] if messages else None
    if not main or not main.get("is_main_post"):
        return None

    subject = (main.get("subject") or "").strip() or "无标题"
    page_title = f"{subject} - 留言本 · BlogN"
    author = (main.get("author_name") or "").strip() or "用户"
    empty_desc = f"留言本主题「{subject}」，{author} · BlogN"
    description = _markdown_to_plain_preview(
        main.get("content"),
        empty_fallback=empty_desc,
    )

    canonical_path = f"/thread/{thread_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        canonical_path=canonical_path,
    )


async def load_blog_share_meta(
    session: AsyncSession,
    project_id: int,
) -> Optional[ArticleShareMeta]:
    """博客首页 /blog/{id} 的分享元数据（项目不存在则 None）。"""
    project_repo = ProjectRepository(session)
    project = await project_repo.get_by_id(project_id)
    if not project:
        return None

    name = (project.name or "").strip() or "博客"
    page_title = f"{name} - BlogN"
    empty_desc = f"「{name}」的博客首页，BlogN"
    description = _markdown_to_plain_preview(
        project.comment,
        empty_fallback=empty_desc,
    )

    canonical_path = f"/blog/{project_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        canonical_path=canonical_path,
    )


def inject_article_share_preview(
    html_template: str,
    meta: ArticleShareMeta,
    og_type: str = "article",
    *,
    public_base_url: str = "",
) -> str:
    """
    在 HTML 模板中替换 <title>、description，并在 </head> 前插入 Open Graph。

    ``public_base_url`` 非空时（由请求的 Host / X-Forwarded-* 解析），``og:url`` 与 ``og:image``
    使用绝对 URL，便于微信等抓取；否则保持站内相对路径。

    ``og_type``：文章/留言主题常用 ``article``，博客首页用 ``website``。
    """
    title_el = html.escape(meta.page_title, quote=False)
    esc_title = html.escape(meta.page_title, quote=True)
    esc_desc = html.escape(meta.description, quote=True)
    og_url = absolute_url_from_site_base(public_base_url, meta.canonical_path)
    og_image = absolute_url_from_site_base(public_base_url, SITE_OG_IMAGE_PATH)
    esc_path = html.escape(og_url, quote=True)
    esc_image = html.escape(og_image, quote=True)

    html_out = re.sub(
        r"<title>.*?</title>",
        f"<title>{title_el}</title>",
        html_template,
        count=1,
        flags=re.DOTALL,
    )

    html_out = re.sub(
        r'<meta\s+name="description"\s+content="[^"]*"\s*>',
        f'<meta name="description" content="{esc_desc}">',
        html_out,
        count=1,
    )

    esc_og_type = html.escape(og_type, quote=True)

    og_lines = [
        f'    <meta property="og:type" content="{esc_og_type}">',
        f'    <meta property="og:title" content="{esc_title}">',
        f'    <meta property="og:description" content="{esc_desc}">',
        f'    <meta property="og:url" content="{esc_path}">',
        f'    <meta property="og:image" content="{esc_image}">',
        f'    <meta property="og:site_name" content="BlogN">',
    ]
    og_block = "\n".join(og_lines) + "\n"

    html_out = html_out.replace("</head>", og_block + "\n</head>", 1)
    return html_out
