"""自动链接 URL 识别：与 HtmlUtils.AUTO_LINK_URL_SOURCE 保持一致。"""

import re

AUTO_LINK_URL_PATTERN = re.compile(
    r"[a-zA-Z][a-zA-Z0-9+.-]*://"
    r"(?:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]|%[0-9A-Fa-f]{2})+"
)


def find_autolink_urls(text: str) -> list[str]:
    return AUTO_LINK_URL_PATTERN.findall(text)


def extract_autolink_url(text: str) -> str:
    match = AUTO_LINK_URL_PATTERN.match(text)
    if not match:
        return ""
    return match.group(0)


class TestAutolinkUtils:
    def test_stops_before_fullwidth_punctuation_and_cjk(self):
        text = (
            "http://club.beelink.com.cn/index.asp?boardid=168），"
            "禁书挺多的，就是用FTP下载麻烦了些"
        )
        assert find_autolink_urls(text) == [
            "http://club.beelink.com.cn/index.asp?boardid=168"
        ]
        assert extract_autolink_url(
            "http://club.beelink.com.cn/index.asp?boardid=168），禁书挺多的"
        ) == "http://club.beelink.com.cn/index.asp?boardid=168"

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
