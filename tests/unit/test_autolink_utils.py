"""自动链接 URL 识别：与 HtmlUtils autolink 逻辑一致的 Python 参考实现测试。"""

from tests.unit.autolink_helpers import (
    extract_autolink_url,
    find_autolink_urls,
    linkify_plain_text_to_html,
    normalize_autolink_anchors,
    trim_autolink_url,
)

BEELINK_URL = "http://club.beelink.com.cn/index.asp?boardid=168"
BEELINK_SUFFIX = "），禁书挺多的，就是用FTP下载麻烦了些"


class TestAutolinkUrlPattern:
    def test_stops_before_fullwidth_punctuation_and_cjk(self):
        text = BEELINK_URL + BEELINK_SUFFIX
        assert find_autolink_urls(text) == [BEELINK_URL]
        assert extract_autolink_url(BEELINK_URL + "），禁书挺多的") == BEELINK_URL

    def test_multiple_http_links(self):
        text = "多个链接: http://site1.com 和 https://site2.com/path?q=1"
        assert find_autolink_urls(text) == [
            "http://site1.com",
            "https://site2.com/path?q=1",
        ]

    def test_no_false_positive_in_plain_text(self):
        assert find_autolink_urls("没有链接的普通文本") == []

    def test_percent_encoding_in_path(self):
        text = "见 https://example.com/path%20name 详情"
        assert find_autolink_urls(text) == ["https://example.com/path%20name"]

    def test_old_loose_pattern_would_over_match(self):
        """回归：旧 [^\\s<>\"']+ 会把中文无空格地吞进 URL。"""
        import re

        loose = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>\"']+")
        text = BEELINK_URL + BEELINK_SUFFIX
        loose_match = loose.search(text)
        assert loose_match is not None
        assert loose_match.group(0) != BEELINK_URL
        assert find_autolink_urls(text) == [BEELINK_URL]


class TestTrimAutolinkUrl:
    def test_strips_trailing_ascii_period_when_valid_without_it(self):
        assert trim_autolink_url("https://example.com/path.") == "https://example.com/path"

    def test_keeps_dot_in_domain(self):
        url = "https://example.co.uk/path"
        assert trim_autolink_url(url) == url

    def test_strips_unbalanced_closing_paren(self):
        assert trim_autolink_url("https://example.com/foo)") == "https://example.com/foo"

    def test_keeps_balanced_parens_in_path(self):
        url = "https://example.com/wiki/Test_(disambiguation)"
        assert trim_autolink_url(url) == url


class TestLinkifyPlainTextToHtml:
    def test_beelink_comment_style_output(self):
        html = linkify_plain_text_to_html(BEELINK_URL + BEELINK_SUFFIX)
        assert f'href="{BEELINK_URL}"' in html
        assert f">{BEELINK_URL}</a>" in html
        assert "），禁书挺多的" in html
        assert BEELINK_URL + "），" not in html

    def test_escapes_html_outside_links(self):
        html = linkify_plain_text_to_html("<script>alert(1)</script> https://example.com ok")
        assert "&lt;script&gt;" in html
        assert "<script>" not in html
        assert 'href="https://example.com"' in html


class TestNormalizeAutolinkAnchors:
    def test_fixes_marked_gfm_overlong_href(self):
        bad_href = BEELINK_URL + BEELINK_SUFFIX
        html = (
            f'<p><a href="{bad_href}">{bad_href}</a></p>'
        )
        fixed = normalize_autolink_anchors(html)
        assert f'href="{BEELINK_URL}"' in fixed
        assert f">{BEELINK_URL}</a>" in fixed
        assert "），禁书挺多的" in fixed
        assert bad_href not in fixed

    def test_leaves_markdown_style_link_text_unchanged(self):
        html = '<a href="http://evil.com/），x">点击这里</a>'
        assert normalize_autolink_anchors(html) == html
