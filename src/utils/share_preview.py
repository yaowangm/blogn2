"""
社交分享 / 爬虫预览：在首包 HTML 中注入 Open Graph、微数据与标题。

微信等客户端不执行 JavaScript，仅解析静态 HTML；普通浏览器仍走原有 SPA + Ajax。

链接策略：``canonical_path``、``og:image``、``twitter:image`` 等使用以 ``/`` 开头的站内
相对路径，由客户端按当前页面协议（https）解析为绝对 URL，避免错误写成 ``http://``
导致缩略图被丢弃。

微信链接预览对 ``og:image`` 的依赖不稳定；部分场景会回退到站点图标。
除 ``og:image`` 等 meta 外，在 ``</head>`` 前注入 ``shortcut icon`` / ``icon``（指向仓库内
实际存在的 ``/static/favicon.svg``），便于预览抓取。
``itemprop="image"`` 仍为站点 SVG logo；``og:image`` 为文章首图 / 头像 / 无图时用同一 SVG。
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

_IMAGE_SUFFIXES: tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
)

# 分享预览里给微信等读取的 itemprop 缩略图（站内相对路径）
_SITE_LOGO_SHARE_PATH = "/static/images/logo-light.svg"
# 仓库内仅有 favicon.svg，无 favicon.ico；分享与回退图统一用 SVG
_SITE_FAVICON_SHARE_PATH = "/static/favicon.svg"


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
    """分享注入用元数据（文章 / 博客首页 / 留言主题）。

    ``og_image_path``、``canonical_path`` 均为以 ``/`` 开头的站内路径，注入 meta 时不拼主机名。
    """

    page_title: str
    description: str
    og_image_path: str
    canonical_path: str


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


def _share_og_image_path_for_user(userid: Optional[int]) -> str:
    """有头像文件则用其站内路径，否则站点 favicon.svg（博客首页与留言主贴共用）。"""
    rel = _avatar_relative_url_if_exists(userid)
    if rel:
        return rel if rel.startswith("/") else f"/{rel.lstrip('/')}"
    return _SITE_FAVICON_SHARE_PATH


async def load_article_share_meta(
    session: AsyncSession,
    article_id: int,
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

    og_image_path: Optional[str] = None
    attachments = await attachment_repo.get_by_project_item_id(article_id)
    for att in attachments or []:
        if _is_image_path(getattr(att, "linkstr", None)):
            link = (att.linkstr or "").lstrip("/")
            og_image_path = f"/upload/{link}"
            break
    if not og_image_path and _is_image_path(article.attachment):
        link = (article.attachment or "").lstrip("/")
        og_image_path = f"/upload/{link}"
    if not og_image_path:
        og_image_path = _SITE_FAVICON_SHARE_PATH

    canonical_path = f"/article/{article_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        og_image_path=og_image_path,
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

    og_image_path = _share_og_image_path_for_user(main.get("userid"))

    canonical_path = f"/thread/{thread_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        og_image_path=og_image_path,
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

    og_image_path = _share_og_image_path_for_user(project.userid)

    canonical_path = f"/blog/{project_id}"

    return ArticleShareMeta(
        page_title=page_title,
        description=description,
        og_image_path=og_image_path,
        canonical_path=canonical_path,
    )


def inject_article_share_preview(
    html_template: str,
    meta: ArticleShareMeta,
    og_type: str = "article",
) -> str:
    """
    在 HTML 模板中替换 <title>、description，并在 </head> 前插入 Open Graph、
    微数据以及 ``shortcut icon`` / ``icon`` 链接（站内相对路径）。

    与 ``article.html`` / ``blog.html`` / ``thread.html`` 等首段 head 结构兼容。
    ``og_type``：文章/留言主题常用 ``article``，博客首页用 ``website``。
    """
    title_el = html.escape(meta.page_title, quote=False)
    esc_title = html.escape(meta.page_title, quote=True)
    esc_desc = html.escape(meta.description, quote=True)
    esc_path = html.escape(meta.canonical_path, quote=True)
    esc_image = html.escape(meta.og_image_path or _SITE_FAVICON_SHARE_PATH, quote=True)
    esc_itemprop_image = html.escape(_SITE_LOGO_SHARE_PATH, quote=True)
    esc_favicon = html.escape(_SITE_FAVICON_SHARE_PATH, quote=True)

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
    <link rel="shortcut icon" type="image/svg+xml" href="{esc_favicon}">
    <link rel="icon" type="image/svg+xml" href="{esc_favicon}">
    <meta itemprop="name" content="{esc_title}">
    <meta itemprop="description" content="{esc_desc}">
    <meta itemprop="image" content="{esc_itemprop_image}">
    <meta property="og:type" content="{esc_og_type}">
    <meta property="og:title" content="{esc_title}">
    <meta property="og:description" content="{esc_desc}">
    <meta property="og:url" content="{esc_path}">
    <meta property="og:image" content="{esc_image}">
    <meta property="og:site_name" content="BlogN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc_title}">
    <meta name="twitter:description" content="{esc_desc}">
    <meta name="twitter:image" content="{esc_image}">
"""

    html_out = html_out.replace("</head>", og_block + "\n</head>", 1)
    return html_out
