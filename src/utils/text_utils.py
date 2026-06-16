"""文本处理工具。"""

import re

POST_LIST_EXCERPT_MAX_LENGTH = 300

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MD_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```|~~~[\s\S]*?~~~")
_MD_DISPLAY_MATH_RE = re.compile(r"\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]")
_MD_INLINE_MATH_RE = re.compile(r"\\\(.+?\\\)|(?<!\$)\$(?!\$)[^\$\n]+?\$(?!\$)")
_MD_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
_MD_LINE_START_RE = re.compile(
    r"^(#{1,6}\s+|>\s*|[\s]*[-*+]\s+|[\s]*\d+\.\s+|[-*_]{3,}$)", re.MULTILINE
)
_MD_INLINE_RE = re.compile(
    r"\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_|~~([^~]+)~~|`([^`]+)`"
)
_WHITESPACE_RE = re.compile(r"\s+")


def strip_markdown_light(text: str) -> str:
    """轻量剥离 Markdown/HTML 标记，返回纯文本（用于列表摘要）。"""
    if not text:
        return ""
    result = _HTML_TAG_RE.sub("", text)
    result = _MD_CODE_BLOCK_RE.sub("", result)
    result = _MD_DISPLAY_MATH_RE.sub("", result)
    result = _MD_INLINE_MATH_RE.sub("", result)
    result = _MD_LINE_START_RE.sub("", result)
    result = _MD_INLINE_RE.sub(
        lambda m: next(g for g in m.groups() if g is not None), result
    )
    result = _MD_LINK_RE.sub(r"\1", result)
    result = result.replace("|", " ")
    return _WHITESPACE_RE.sub(" ", result).strip()


def truncate_excerpt(text: str | None, max_length: int = POST_LIST_EXCERPT_MAX_LENGTH) -> str:
    """截断博文摘要，用于列表 API 响应，避免返回完整正文。"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def plain_text_excerpt(
    text: str | None, max_length: int = POST_LIST_EXCERPT_MAX_LENGTH
) -> str:
    """剥离 Markdown/HTML 后截断，供列表 API 返回纯文本摘要。"""
    return truncate_excerpt(strip_markdown_light(text or ""), max_length)
