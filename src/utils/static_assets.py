"""
静态资源版本与 HTML 缓存破除。

发布新版本时通过 STATIC_VERSION（或自动解析的构建标识）为页面内 /static/ 链接追加 ?v=，
并禁止浏览器长期缓存 HTML；带版本号的静态资源可长期缓存。
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

_STATIC_URL_ATTR_RE = re.compile(
    r'(?P<attr>href|src)=["\'](/static/[^"\']+)["\']',
    re.IGNORECASE,
)
_HEAD_OPEN_RE = re.compile(r"(<head[^>]*>)", re.IGNORECASE)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_STATIC_DIR = _PROJECT_ROOT / "src" / "static"
_STATIC_VERSION_FILE = _PROJECT_ROOT / ".static_version"


def _read_static_version_file() -> str:
    """读取构建脚本写入的 .static_version（Docker 构建或 build-app.sh）。"""
    if not _STATIC_VERSION_FILE.is_file():
        return ""
    try:
        return _STATIC_VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.debug("无法读取 .static_version: %s", exc)
        return ""


@lru_cache(maxsize=1)
def get_static_version() -> str:
    """
    静态资源版本标识，用于 ?v= 查询参数。

    优先级：环境变量 STATIC_VERSION > .static_version 文件 > git 短提交哈希 > src/static mtime。
    """
    env_version = os.getenv("STATIC_VERSION", "").strip()
    if env_version:
        return env_version

    file_version = _read_static_version_file()
    if file_version:
        return file_version

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=str(_PROJECT_ROOT),
            check=False,
        )
        if result.returncode == 0:
            git_hash = result.stdout.strip()
            if git_hash:
                return git_hash
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("无法从 git 解析 STATIC_VERSION: %s", exc)

    return _static_dir_mtime_version()


def _static_dir_mtime_version() -> str:
    """以 src/static 下文件的最大修改时间（秒）作为版本回退值。"""
    if not _STATIC_DIR.is_dir():
        return "0"

    latest_mtime = 0.0
    for path in _STATIC_DIR.rglob("*"):
        if path.is_file():
            try:
                latest_mtime = max(latest_mtime, path.stat().st_mtime)
            except OSError:
                continue
    return str(int(latest_mtime))


def append_static_version(url: str, version: str | None = None) -> str:
    """为 /static/ URL 追加 ?v= 版本参数（已含 v= 时原样返回）。"""
    if not url.startswith("/static/"):
        return url

    version = version if version is not None else get_static_version()
    if not version or "v=" in url:
        return url

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"


def inject_static_version_into_html(html: str, version: str | None = None) -> str:
    """为 HTML 中 href/src 指向的 /static/ 资源追加版本查询参数。"""
    version = version if version is not None else get_static_version()
    if not version:
        return html

    def _replace(match: re.Match[str]) -> str:
        attr = match.group("attr")
        url = append_static_version(match.group(2), version)
        return f'{attr}="{url}"'

    return _STATIC_URL_ATTR_RE.sub(_replace, html)


def inject_static_version_bootstrap(html: str, version: str | None = None) -> str:
    """在 <head> 后注入全局版本号与 static-url.js。"""
    version = version if version is not None else get_static_version()
    if not version:
        return html

    static_url_script = append_static_version("/static/js/utils/static-url.js", version)
    snippet = (
        f'<script>window.__BLOGN_STATIC_VERSION__="{version}";</script>\n'
        f'    <script src="{static_url_script}"></script>'
    )
    return _HEAD_OPEN_RE.sub(rf"\1\n    {snippet}", html, count=1)


def apply_html_no_cache_headers(response: HTMLResponse) -> None:
    """HTML 页面每次发布都应重新校验，避免壳页面被长期缓存。"""
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"


def build_versioned_html_response(html: str) -> HTMLResponse:
    """将静态 HTML 模板转为带版本号与 no-cache 的响应。"""
    version = get_static_version()
    html = inject_static_version_bootstrap(html, version)
    html = inject_static_version_into_html(html, version)
    response = HTMLResponse(content=html)
    apply_html_no_cache_headers(response)
    return response


def resolve_static_file_path(url_path: str) -> Path | None:
    """将 /static/... 请求路径解析为磁盘上的文件路径。"""
    if not url_path.startswith("/static/"):
        return None

    relative = url_path[len("/static/") :].split("?", 1)[0]
    if not relative or ".." in relative.split("/"):
        return None

    file_path = (_STATIC_DIR / relative).resolve()
    try:
        file_path.relative_to(_STATIC_DIR.resolve())
    except ValueError:
        return None

    return file_path if file_path.is_file() else None


def apply_static_cache_headers(response, request_path: str, query_string: str) -> None:
    """为 /static/ 响应设置 ETag；带 ?v= 的资源允许长期缓存。"""
    file_path = resolve_static_file_path(request_path)
    if file_path is None:
        return

    try:
        stat = file_path.stat()
    except OSError:
        return

    response.headers["ETag"] = f'"{int(stat.st_mtime)}-{stat.st_size}"'

    if "v=" in query_string:
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response.headers["Cache-Control"] = "public, max-age=0, must-revalidate"
