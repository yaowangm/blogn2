"""article-content-card.js 静态检查：按发表日期切换 Markdown / 纯文本渲染。"""

from pathlib import Path

from tests.unit.autolink_helpers import linkify_plain_text_to_html, normalize_autolink_anchors

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTICLE_CONTENT_CARD_JS = (
    PROJECT_ROOT / "src" / "static" / "js" / "components" / "article-content-card.js"
)
ARTICLE_COMMENTS_CARD_JS = (
    PROJECT_ROOT / "src" / "static" / "js" / "components" / "article-comments-card.js"
)
THREAD_CARD_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "thread-card.js"
HTML_UTILS_JS = PROJECT_ROOT / "src" / "static" / "js" / "utils" / "html-utils.js"

BEELINK = "http://club.beelink.com.cn/index.asp?boardid=168"


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
        assert "MarkdownUtils.parseMarkdown" in content
        assert "MarkdownUtils.ensureKatexStyles" in content

    def test_plain_text_escapes_and_linkifies_only(self):
        content = ARTICLE_CONTENT_CARD_JS.read_text(encoding="utf-8")
        assert "this.escapeHtml(content)" in content
        assert "HtmlUtils.linkifyPlainTextToHtml(p)" in content
        assert "if (!this.usesMarkdownContent(createdAt))" in content


class TestAutolinkComponentWiring:
    """各展示场景应调用 HtmlUtils，而非本地重复实现。"""

    def test_comments_use_html_utils_linkify(self):
        content = ARTICLE_COMMENTS_CARD_JS.read_text(encoding="utf-8")
        assert "HtmlUtils.linkifyPlainTextToHtml" in content
        assert "processTextWithLinks" not in content

    def test_comment_hash_scroll_waits_for_article_layout(self):
        content = ARTICLE_COMMENTS_CARD_JS.read_text(encoding="utf-8")
        assert "_waitForArticlePageLayoutReady" in content
        assert "waitForLayoutReady" in content
        assert "await this._waitForArticlePageLayoutReady()" in content

    def test_article_content_card_waits_for_images_before_anchor_scroll(self):
        content = ARTICLE_CONTENT_CARD_JS.read_text(encoding="utf-8")
        assert "async waitForLayoutReady()" in content
        assert "waitForImagesInRoot" in content
        assert 'loading="eager"' in content

    def test_thread_card_use_html_utils_linkify(self):
        content = THREAD_CARD_JS.read_text(encoding="utf-8")
        assert "HtmlUtils.linkifyPlainTextToHtml" in content

    def test_html_utils_exports_autolink_api(self):
        content = HTML_UTILS_JS.read_text(encoding="utf-8")
        assert "AUTO_LINK_URL_SOURCE" in content
        assert "linkifyPlainTextToHtml" in content
        assert "normalizeAutoLinkAnchors" in content
        assert "processRichTextLinks" in content


class TestAutolinkIntegrationScenarios:
    """评论 / 旧文 / marked 三类场景的期望 HTML 输出。"""

    def test_plain_text_comment_scenario(self):
        text = BEELINK + "），禁书挺多的"
        html = linkify_plain_text_to_html(text)
        assert f'href="{BEELINK}"' in html
        assert "），禁书挺多的" in html

    def test_marked_autolink_scenario(self):
        bad = BEELINK + "），禁书挺多的"
        html = normalize_autolink_anchors(f'<a href="{bad}">{bad}</a>')
        assert f'href="{BEELINK}"' in html
        assert "），禁书挺多的" in html
