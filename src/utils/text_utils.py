"""文本处理工具。"""

POST_LIST_EXCERPT_MAX_LENGTH = 300


def truncate_excerpt(text: str | None, max_length: int = POST_LIST_EXCERPT_MAX_LENGTH) -> str:
    """截断博文摘要，用于列表 API 响应，避免返回完整正文。"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
