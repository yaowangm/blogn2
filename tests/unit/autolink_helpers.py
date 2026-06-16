"""
与 src/static/js/utils/html-utils.js 中 autolink 逻辑保持一致的 Python 参考实现，供单元测试使用。
"""

from __future__ import annotations

import re
from html import escape
from urllib.parse import urlparse

AUTO_LINK_URL_SOURCE = (
    r"[a-zA-Z][a-zA-Z0-9+.-]*://"
    r"(?:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]|%[0-9A-Fa-f]{2})+"
)
AUTO_LINK_URL_PATTERN = re.compile(AUTO_LINK_URL_SOURCE)
TRAILING_PUNCT = re.compile(
    r"(?:[,;:!?]+|[\u3001\u3002\uff0c\uff0e\uff1a\uff1b\uff01\uff1f\uff09\uff3d\uff5d"
    r"\u300b\u300d\u300f\uff02\uff07\u2026])+$"
)
ALLOWED_PROTOCOLS = frozenset(
    {"http", "https", "ftp", "mailto", "tel", "ed2k", "thunder"}
)
# marked GFM autolink: <a href="...">...</a>，文本与 href 相同
MARKED_AUTOLINK_ANCHOR = re.compile(
    r'<a\b([^>]*\bhref="([^"]*)"[^>]*)>([^<]*)</a>',
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ALLOWED_PROTOCOLS
    except (ValueError, AttributeError):
        return False


def trim_autolink_url(url: str) -> str:
    if not url:
        return ""
    s = url
    while True:
        before = s
        s = TRAILING_PUNCT.sub("", s)
        while s.endswith(")"):
            opens = s.count("(")
            closes = s.count(")")
            if closes <= opens:
                break
            s = s[:-1]
        while s.endswith("\uff09"):
            opens = s.count("\uff08")
            closes = s.count("\uff09")
            if closes <= opens:
                break
            s = s[:-1]
        while s.endswith("]"):
            opens = s.count("[")
            closes = s.count("]")
            if closes <= opens:
                break
            s = s[:-1]
        if s.endswith(".") and is_valid_url(s[:-1]):
            s = s[:-1]
        if s == before:
            break
    return s


def extract_autolink_url(text: str) -> str:
    if not text:
        return ""
    match = AUTO_LINK_URL_PATTERN.match(text)
    if not match:
        return ""
    return trim_autolink_url(match.group(0))


def find_autolink_urls(text: str) -> list[str]:
    return AUTO_LINK_URL_PATTERN.findall(text)


def linkify_plain_text_to_html(text: str) -> str:
    if not text:
        return ""
    text = text.lstrip()
    parts: list[str] = []
    last_index = 0
    for match in AUTO_LINK_URL_PATTERN.finditer(text):
        if match.start() > last_index:
            parts.append(escape(text[last_index : match.start()]))
        raw_url = match.group(0)
        url = trim_autolink_url(raw_url)
        tail = escape(raw_url[len(url) :]) if len(raw_url) > len(url) else ""
        if url and is_valid_url(url):
            safe = escape(url, quote=True)
            display = escape(url)
            parts.append(
                f'<a href="{safe}" target="_blank" rel="noopener noreferrer" '
                f'class="auto-link">{display}</a>{tail}'
            )
        else:
            parts.append(escape(raw_url))
        last_index = match.end()
    if last_index < len(text):
        parts.append(escape(text[last_index:]))
    return "".join(parts)


def normalize_autolink_anchors(html: str) -> str:
    """
    修正 marked GFM autolink：href 与链接文本相同且含 CJK/全角后缀时截断 href。
    """

    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        href = match.group(2)
        text = match.group(3)
        if text != href:
            return match.group(0)
        fixed = extract_autolink_url(href)
        if not fixed or not is_valid_url(fixed) or href == fixed:
            return match.group(0)
        if not href.startswith(fixed):
            return match.group(0)
        tail = href[len(fixed) :]
        safe_href = escape(fixed, quote=True)
        new_attrs = re.sub(
            r'href="[^"]*"',
            f'href="{safe_href}"',
            attrs,
            count=1,
            flags=re.IGNORECASE,
        )
        return f"<a{new_attrs}>{escape(fixed)}</a>{escape(tail)}"

    return MARKED_AUTOLINK_ANCHOR.sub(repl, html)
