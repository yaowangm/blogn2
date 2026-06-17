"""markdown-utils.js 与 KaTeX 本地资源静态检查。"""

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

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

    def test_markdown_images_are_not_rendered(self):
        if not shutil.which("node"):
            pytest.skip("node is required for markdown rendering regression test")

        script = textwrap.dedent(
            r"""
            const fs = require('fs');
            const vm = require('vm');

            class TextNode {
              constructor(text) {
                this.nodeType = 3;
                this._text = String(text);
              }
              get textContent() {
                return this._text;
              }
              cloneNode() {
                return new TextNode(this._text);
              }
            }

            class ElementNode {
              constructor(tagName) {
                this.nodeType = 1;
                this.tagName = tagName.toUpperCase();
                this.attributes = [];
                this.childNodes = [];
              }
              get textContent() {
                return this.childNodes.map((child) => child.textContent).join('');
              }
              setAttribute(name, value) {
                const existing = this.attributes.find((attr) => attr.name === name);
                if (existing) existing.value = String(value);
                else this.attributes.push({ name, value: String(value) });
              }
              appendChild(node) {
                this.childNodes.push(node);
                return node;
              }
              set innerHTML(html) {
                this.childNodes = parseFragment(html);
              }
              get innerHTML() {
                return this.childNodes.map(serializeNode).join('');
              }
            }

            function parseAttrs(raw) {
              const attrs = [];
              raw.replace(/([\w:-]+)(?:="([^"]*)")?/g, (_, name, value = '') => {
                attrs.push({ name, value });
                return '';
              });
              return attrs;
            }

            function parseFragment(html) {
              const root = new ElementNode('root');
              const stack = [root];
              const tokenRe = /<[^>]+>|[^<]+/g;
              let match;
              while ((match = tokenRe.exec(html)) !== null) {
                const token = match[0];
                const parent = stack[stack.length - 1];
                if (token.startsWith('</')) {
                  if (stack.length > 1) stack.pop();
                } else if (token.startsWith('<')) {
                  const open = token.match(/^<\s*([a-zA-Z0-9-]+)([^>]*)>/);
                  if (!open) continue;
                  const el = new ElementNode(open[1]);
                  parseAttrs(open[2]).forEach((attr) => el.setAttribute(attr.name, attr.value));
                  parent.appendChild(el);
                  if (!token.endsWith('/>') && !['br', 'hr', 'img'].includes(open[1].toLowerCase())) {
                    stack.push(el);
                  }
                } else {
                  parent.appendChild(new TextNode(token));
                }
              }
              return root.childNodes;
            }

            function escapeHtml(text) {
              return String(text)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
            }

            function serializeNode(node) {
              if (node.nodeType === 3) return escapeHtml(node.textContent);
              const tag = node.tagName.toLowerCase();
              const attrs = node.attributes
                .map((attr) => ` ${attr.name}="${escapeHtml(attr.value)}"`)
                .join('');
              return `<${tag}${attrs}>${node.childNodes.map(serializeNode).join('')}</${tag}>`;
            }

            const context = {
              console,
              URL,
              window: { location: { hostname: 'localhost' } },
              Node: { TEXT_NODE: 3, ELEMENT_NODE: 1 },
            };
            context.window.window = context.window;
            context.document = {
              createElement: (tag) => new ElementNode(tag),
              createTextNode: (text) => new TextNode(text),
            };
            context.window.document = context.document;
            context.window.Node = context.Node;
            vm.createContext(context);

            for (const file of [
              'src/static/js/libs/marked.min.js',
              'src/static/js/libs/katex/katex.min.js',
              'src/static/js/utils/html-utils.js',
              'src/static/js/utils/markdown-utils.js',
            ]) {
              vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file });
            }

            const html = context.window.MarkdownUtils.parseMarkdown(
              '![alt text](https://example.com/image.png)\n\n[normal link](https://example.com)'
            );

            if (html.includes('<img') || html.includes('image.png')) {
              throw new Error(`Markdown image rendered unexpectedly: ${html}`);
            }
            if (!html.includes('<a href="https://example.com"')) {
              throw new Error(`Normal Markdown link was not preserved: ${html}`);
            }
            """
        )
        subprocess.run(["node", "-e", script], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)

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

    def test_markdown_example_covers_supported_formats(self):
        doc = DOC_MARKDOWN_KATEX.read_text(encoding="utf-8")
        examples = [
            "# 一篇包含多种 Markdown 格式的示例文章",
            "**加粗文字**",
            "*倾斜文字*",
            "~~删除线文字~~",
            "`行内代码`",
            "[示例网站](https://example.com)",
            "> 写作时",
            "---",
            "1. 第一件事",
            "- [x] 已完成的任务",
            "| 类型 | 示例 | 说明 |",
            "```js",
            "$E=mc^2$",
            "\\int_{-\\infty}^{\\infty}",
            "\\sum_{n=1}^{\\infty}",
            "2\\mathrm{H}_2 + \\mathrm{O}_2",
            "###### 六级标题",
        ]
        for example in examples:
            assert example in doc
        assert "![示例图片]" not in doc
