"""
社交分享 / 爬虫预览：在首包 HTML 中注入 Open Graph 与标题。

微信等客户端不执行 JavaScript，仅解析静态 HTML；普通浏览器仍走原有 SPA + Ajax。
"""

from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from typing import Mapping, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.app import validate_app_config
from src.constants import ArticleStatus
from src.repositories.attachment_repository import AttachmentRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.project_repository import ProjectRepository
from src.utils.permission_manager import permission_manager

# User-Agent 子串（大小写不敏感），覆盖微信与常见社交/预览爬虫
_SHARE_PREVIEW_UA_MARKERS: tuple[str, ...] = (
    "micromessenger",  # 微信内置浏览器与分享抓取
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

_IMAGE_SUFFIXES: tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
)


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
    生成对外绝对 URL 前缀（og:image、og:url）。
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


def _is_image_path(path: Optional[str]) -> bool:
    if not path:
        return False
    lower = path.split("?", 1)[0].lower()
    return any(lower.endswith(ext) for ext in _IMAGE_SUFFIXES)


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
    page_title: str
    description: str
    og_image_absolute: Optional[str]
    canonical_url: str


async def load_article_share_meta(
    session: AsyncSession,
    article_id: int,
    public_base_url: str,
) -> Optional[ArticleShareMeta]:
    """
    读取用于分享预览的元数据（与公开文章 API 一致的可见性：已删除对爬虫不可见）。
    """
    item_repo = ProjectItemRepository(session)
    project_repo = ProjectRepository(session)
    attachment_repo = AttachmentRepository(session)

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

    og_image: Optional[str] = None
    attachments = await attachment_repo.get_by_project_item_id(article_id)
    for att in attachments or []:
        if _is_image_path(getattr(att, "linkstr", None)):
            link = (att.linkstr or "").lstrip("/")
            og_image = f"{public_base_url}/upload/{link}"
            break
    if not og_image and _is_image_path(article.attachment):
        link = (article.attachment or "").lstrip("/")
        og_image = f"{public_base_url}/upload/{link}"
    if not og_image:
        og_image = f"{public_base_url}/static/favicon.ico"

    canonical_url = f"{public_base_url}/article/{article_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        og_image_absolute=og_image,
        canonical_url=canonical_url,
    )


def _avatar_relative_url_if_exists(userid: Optional[int]) -> Optional[str]:
    """与 BlogService._check_avatar_exists 一致：磁盘存在则返回站内头像路径。"""
    if not userid:
        return None
    config = validate_app_config()
    avatar_dir = config["avatar_dir"]
    prefix = (userid // 10000) + 1
    rel_web = f"/avatar/{prefix}/s_{userid}.jpg"
    real_path = os.path.join(avatar_dir, str(prefix), f"s_{userid}.jpg")
    if os.path.exists(real_path):
        return rel_web
    return None


async def load_blog_share_meta(
    session: AsyncSession,
    project_id: int,
    public_base_url: str,
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

    rel_avatar = _avatar_relative_url_if_exists(project.userid)
    if rel_avatar:
        link = rel_avatar.lstrip("/")
        og_image = f"{public_base_url}/{link}"
    else:
        og_image = f"{public_base_url}/static/favicon.ico"

    canonical_url = f"{public_base_url}/blog/{project_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        og_image_absolute=og_image,
        canonical_url=canonical_url,
    )


def inject_article_share_preview(
    html_template: str,
    meta: ArticleShareMeta,
    og_type: str = "article",
) -> str:
    """
    在 HTML 模板中替换 <title>、description，并在 </head> 前插入 Open Graph。

    ``og_type``：文章页用 ``article``，博客首页用 ``website``。
    """
    title_el = html.escape(meta.page_title, quote=False)
    esc_title = html.escape(meta.page_title, quote=True)
    esc_desc = html.escape(meta.description, quote=True)
    esc_url = html.escape(meta.canonical_url, quote=True)
    esc_image = html.escape(meta.og_image_absolute or "", quote=True)

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

    og_block = f"""
    <meta property="og:type" content="{esc_og_type}">
    <meta property="og:title" content="{esc_title}">
    <meta property="og:description" content="{esc_desc}">
    <meta property="og:url" content="{esc_url}">
    <meta property="og:image" content="{esc_image}">
    <meta property="og:site_name" content="BlogN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc_title}">
    <meta name="twitter:description" content="{esc_desc}">
    <meta name="twitter:image" content="{esc_image}">
"""

    html_out = html_out.replace("</head>", og_block + "\n</head>", 1)
    return html_out
