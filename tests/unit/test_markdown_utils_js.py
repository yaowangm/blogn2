"""markdown-utils.js 与 KaTeX 本地资源静态检查。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MARKDOWN_UTILS_JS = PROJECT_ROOT / "src" / "static" / "js" / "utils" / "markdown-utils.js"
KATEX_DIR = PROJECT_ROOT / "src" / "static" / "js" / "libs" / "katex"
ARTICLE_HTML = PROJECT_ROOT / "src" / "static" / "article.html"
CREATE_POST_HTML = PROJECT_ROOT / "src" / "static" / "create-post.html"
EDIT_ARTICLE_HTML = PROJECT_ROOT / "src" / "static" / "edit-article.html"
ARTICLE_CONTENT_CARD_JS = (
    PROJECT_ROOT / "src" / "static" / "js" / "components" / "article-content-card.js"
)
BASE_COMPONENT_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "base-component.js"
CREATE_POST_FORM_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "create-post-form.js"
EDIT_POST_FORM_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "edit-post-form.js"
DOC_MARKDOWN_KATEX = PROJECT_ROOT / "doc" / "MARKDOWN_KATEX.md"


class TestKatexLocalAssets:
    def test_katex_core_files_exist(self):
        assert (KATEX_DIR / "katex.min.js").is_file()
        assert (KATEX_DIR / "katex.min.css").is_file()
        assert (KATEX_DIR / "mhchem.min.js").is_file()
        assert (KATEX_DIR / "LICENSE").is_file()
        fonts = list((KATEX_DIR / "fonts").glob("*.woff2"))
        assert len(fonts) >= 1

    def test_katex_license_is_mit(self):
        text = (KATEX_DIR / "LICENSE").read_text(encoding="utf-8")
        assert "MIT License" in text
        assert "KaTeX" in text or "Khan Academy" in text


class TestMarkdownUtilsJs:
    def test_markdown_utils_exports_parse(self):
        content = MARKDOWN_UTILS_JS.read_text(encoding="utf-8")
        assert "class MarkdownUtils" in content
        assert "static parseMarkdown(source)" in content
        assert "_extractProtectedSegments" in content
        assert "_renderMathPlaceholders" in content
        assert "ensureKatexStyles" in content
        assert "sanitizeHtml" in content
        assert "renderToString" in content
        assert "output: 'html'" in content
        assert 'data-math-idx' in content

    def test_components_use_markdown_utils(self):
        for path in (ARTICLE_CONTENT_CARD_JS, BASE_COMPONENT_JS):
            text = path.read_text(encoding="utf-8")
            assert "MarkdownUtils.parseMarkdown" in text
        for path in (CREATE_POST_FORM_JS, EDIT_POST_FORM_JS):
            text = path.read_text(encoding="utf-8")
            assert "renderMarkdownPreview" in text

    def test_html_pages_load_local_katex_not_cdn(self):
        for path in (ARTICLE_HTML, CREATE_POST_HTML, EDIT_ARTICLE_HTML):
            html = path.read_text(encoding="utf-8")
            assert "/static/js/libs/katex/katex.min.js" in html
            assert "/static/js/libs/katex/katex.min.css" in html
            assert "/static/js/utils/markdown-utils.js" in html
            assert "cdn.jsdelivr" not in html
            assert "unpkg.com" not in html

    def test_documentation_covers_katex_license(self):
        doc = DOC_MARKDOWN_KATEX.read_text(encoding="utf-8")
        assert "KaTeX" in doc
        assert "MIT" in doc
        assert "marked" in doc
        assert "src/static/js/libs/katex/LICENSE" in doc
