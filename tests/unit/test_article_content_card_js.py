"""
article-content-card.js 静态检查：按发表日期切换 Markdown / 纯文本渲染。
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTICLE_CONTENT_CARD_JS = (
    PROJECT_ROOT / "src" / "static" / "js" / "components" / "article-content-card.js"
)


class TestArticleContentCardJs:
    def test_article_content_card_js_exists(self):
        assert ARTICLE_CONTENT_CARD_JS.exists()

    def test_markdown_cutoff_date_constant(self):
        content = ARTICLE_CONTENT_CARD_JS.read_text(encoding="utf-8")
        assert "MARKDOWN_CONTENT_SINCE = '2026-03-28T00:00:00Z'" in content

    def test_uses_created_at_to_choose_renderer(self):
        content = ARTICLE_CONTENT_CARD_JS.read_text(encoding="utf-8")
        assert "usesMarkdownContent" in content
        assert "formatContentPlainText" in content
        assert "plain-text-content" in content
        assert "markdown-content" in content
        assert "formatContent(content, created_at)" in content
        assert "HtmlUtils.processRichTextLinks" in content

    def test_plain_text_escapes_and_linkifies_only(self):
        content = ARTICLE_CONTENT_CARD_JS.read_text(encoding="utf-8")
        assert "this.escapeHtml(content)" in content
        assert "HtmlUtils.linkifyPlainTextToHtml(p)" in content
        assert "if (!this.usesMarkdownContent(createdAt))" in content
