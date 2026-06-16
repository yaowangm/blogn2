/**
 * Markdown 解析工具（marked + 本地 KaTeX）
 *
 * 在 marked 解析前保护代码块与数学公式占位，解析后再用 KaTeX 渲染公式。
 * 依赖全局：marked、katex（可选 mhchem.min.js 用于化学式）。
 */

class MarkdownUtils {
    static get MARKED_OPTIONS() {
        return {
            breaks: true,
            gfm: true,
            pedantic: false,
        };
    }

    /**
     * 将 Markdown 源码转为 HTML（含数学公式渲染）
     * @param {string} source
     * @returns {string}
     */
    static parseMarkdown(source) {
        if (typeof source !== 'string' || !source.trim()) {
            return '';
        }

        const markedParser = typeof marked !== 'undefined' ? marked : window.marked;
        if (!markedParser) {
            throw new Error('marked.js is not loaded');
        }

        const { text, placeholders } = this._extractProtectedSegments(source);
        let html = markedParser.parse(text, this.MARKED_OPTIONS);
        // 先消毒 HTML，再渲染 KaTeX，避免 sanitize 剥离公式内部标签（如 svg）
        html = HtmlUtils.sanitizeHtml(html);
        html = this._renderMathPlaceholders(html, placeholders);
        html = this._normalizeDisplayMath(html);
        return html;
    }

    /**
     * 在 Shadow DOM 中注入 KaTeX 样式（@import 在 Shadow 内字体路径不可靠）
     * @param {ShadowRoot} shadowRoot
     */
    static ensureKatexStyles(shadowRoot) {
        if (!shadowRoot || shadowRoot.querySelector('link[data-katex-styles]')) {
            return;
        }
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        const katexCss = '/static/js/libs/katex/katex.min.css';
        link.href = (window.BlognStatic && window.BlognStatic.url(katexCss)) || katexCss;
        link.setAttribute('data-katex-styles', '1');
        shadowRoot.prepend(link);
    }

    /**
     * 是否已加载 KaTeX
     * @returns {boolean}
     */
    static isKatexAvailable() {
        const lib = typeof katex !== 'undefined' ? katex : window.katex;
        return Boolean(lib && typeof lib.renderToString === 'function');
    }

    /**
     * @param {string} source
     * @returns {{ text: string, placeholders: Array<{token: string, kind: string, value: string}> }}
     */
    static _extractProtectedSegments(source) {
        const placeholders = [];
        let index = 0;

        const stash = (kind, value) => {
            const idx = index;
            index += 1;
            placeholders.push({ idx, kind, value });
            if (kind === 'display') {
                return `\n\n<div class="math-pending" data-math-idx="${idx}"></div>\n\n`;
            }
            if (kind === 'inline') {
                return `<span class="math-pending" data-math-idx="${idx}"></span>`;
            }
            return value;
        };

        let text = source;

        // 1. 围栏代码块
        text = text.replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g, (block) => stash('raw', block));

        // 2. 行内代码
        text = text.replace(/`[^`\n]+`/g, (code) => stash('raw', code));

        // 3. 块级公式 $$ ... $$ 与 \[ ... \]
        text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => stash('display', tex.trim()));
        text = text.replace(/\\\[([\s\S]+?)\\\]/g, (_, tex) => stash('display', tex.trim()));

        // 4. 行内公式 \( ... \) 与 $ ... $（排除 $$）
        text = text.replace(/\\\((.+?)\\\)/g, (_, tex) => stash('inline', tex.trim()));
        text = text.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)/g, (_, tex) => {
            const trimmed = tex.trim();
            return trimmed ? stash('inline', trimmed) : `$${tex}$`;
        });

        return { text, placeholders };
    }

    /**
     * 将占位元素替换为 KaTeX 渲染结果（须在 sanitizeHtml 之后调用）
     * @param {string} html
     * @param {Array<{idx: number, kind: string, value: string}>} placeholders
     * @returns {string}
     */
    static _renderMathPlaceholders(html, placeholders) {
        if (!placeholders.length) {
            return html;
        }

        let result = html;
        for (const item of placeholders) {
            if (item.kind === 'raw') {
                continue;
            }
            const replacement = this._renderMath(item.value, item.kind === 'display');
            const pattern = new RegExp(
                `<(?:div|span)\\s+class="math-pending"\\s+data-math-idx="${item.idx}"\\s*></(?:div|span)>`,
                'g'
            );
            result = result.replace(pattern, replacement);
        }
        return result;
    }

    /**
     * 块级公式不应包在 <p> 内，否则 text-align:justify 会导致错位
     * @param {string} html
     * @returns {string}
     */
    static _normalizeDisplayMath(html) {
        return html.replace(
            /<p>\s*(<span class="katex-display">[\s\S]*?<\/span>)\s*<\/p>/gi,
            '$1'
        );
    }

    /**
     * @param {string} tex
     * @param {boolean} displayMode
     * @returns {string}
     */
    static _renderMath(tex, displayMode) {
        if (!tex) {
            return '';
        }

        const katexLib = typeof katex !== 'undefined' ? katex : window.katex;
        if (!katexLib || typeof katexLib.renderToString !== 'function') {
            const escaped = HtmlUtils.escapeHtml(tex);
            return displayMode ? `<pre class="math-fallback">${escaped}</pre>` : escaped;
        }

        try {
            return katexLib.renderToString(tex, {
                displayMode,
                output: 'html',
                throwOnError: false,
                strict: 'warn',
                trust: false,
            });
        } catch (error) {
            const escaped = HtmlUtils.escapeHtml(tex);
            return displayMode
                ? `<pre class="math-fallback">${escaped}</pre>`
                : `<span class="math-fallback">${escaped}</span>`;
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownUtils;
}

if (typeof window !== 'undefined') {
    window.MarkdownUtils = MarkdownUtils;
}
