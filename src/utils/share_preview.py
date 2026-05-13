"""
社交分享 / 爬虫预览：在首包 HTML 中替换标题、摘要，并注入 Open Graph。

微信等不执行 JavaScript，只读首包 HTML；普通浏览器仍走 SPA。
``canonical_path`` 与 ``property="og:image"``（恒为 ``SITE_OG_IMAGE_PATH`` 站点 logo）使用站内
相对路径。不注入 ``itemprop`` 微数据。
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Mapping, Optional

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

# 分享预览 og:image 固定使用浅色主题站点 logo（与顶栏等一致）
SITE_OG_IMAGE_PATH = "/static/images/logo-light.svg"


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

    ``canonical_path`` 为以 ``/`` 开头的站内路径。预览图 URL 由注入函数固定为站点 logo，
    不在此结构体中重复存储。
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
) -> str:
    """
    在 HTML 模板中替换 <title>、description，并在 </head> 前插入 Open Graph。

    ``property="og:image"`` 为 ``SITE_OG_IMAGE_PATH``（站点 logo）。不写入 ``itemprop``。
    ``og_type``：文章/留言主题常用 ``article``，博客首页用 ``website``。
    """
    title_el = html.escape(meta.page_title, quote=False)
    esc_title = html.escape(meta.page_title, quote=True)
    esc_desc = html.escape(meta.description, quote=True)
    esc_path = html.escape(meta.canonical_path, quote=True)
    esc_image = html.escape(SITE_OG_IMAGE_PATH, quote=True)

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
