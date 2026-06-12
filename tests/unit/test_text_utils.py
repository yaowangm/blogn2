"""文本工具单元测试。"""

from src.utils.text_utils import truncate_excerpt, POST_LIST_EXCERPT_MAX_LENGTH


class TestTruncateExcerpt:
    def test_empty_text(self):
        assert truncate_excerpt(None) == ""
        assert truncate_excerpt("") == ""

    def test_short_text_unchanged(self):
        text = "hello"
        assert truncate_excerpt(text) == text

    def test_long_text_truncated(self):
        text = "x" * (POST_LIST_EXCERPT_MAX_LENGTH + 50)
        result = truncate_excerpt(text)
        assert len(result) == POST_LIST_EXCERPT_MAX_LENGTH + 3
        assert result.endswith("...")
