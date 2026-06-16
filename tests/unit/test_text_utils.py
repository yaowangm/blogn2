"""文本工具单元测试。"""

from src.utils.text_utils import (
    truncate_excerpt,
    plain_text_excerpt,
    strip_markdown_light,
    POST_LIST_EXCERPT_MAX_LENGTH,
)


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


class TestStripMarkdownLight:
    def test_strips_html_and_markdown(self):
        text = "<p>**Hello** [world](http://x.com)</p>"
        assert strip_markdown_light(text) == "Hello world"

    def test_plain_text_excerpt_truncates(self):
        text = "# Title\n\n" + "a" * 120
        result = plain_text_excerpt(text, max_length=100)
        assert len(result) == 103
        assert result.endswith("...")
