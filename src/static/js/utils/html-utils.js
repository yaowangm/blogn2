/**
 * HTML工具模块
 * 
 * 提供HTML相关的工具函数，包括：
 * - HTML转义：防止XSS攻击
 * - HTML清理：安全的HTML过滤
 * - 文本处理：截断、格式化等
 * 
 * 所有需要HTML处理的模块都可以使用此工具模块
 */

class HtmlUtils {
    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */
    static escapeHtml(text) {
        if (typeof text !== 'string') return text;
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * 截断文本
     * 将长文本截断到指定长度并添加省略号
     * @param {string} text - 要截断的文本
     * @param {number} maxLength - 最大长度
     * @returns {string} 截断后的文本
     */
    static truncateText(text, maxLength = 20) {
        if (!text) return '';
        
        const cleanText = text.replace(/\r\n/g, ' ').replace(/\n/g, ' ').trim();
        return cleanText.length > maxLength 
            ? cleanText.substring(0, maxLength) + '...' 
            : cleanText;
    }

    /**
     * 移除Markdown标记，返回纯文本
     * 用于在摘要列表中显示纯文本内容
     * @param {string} text - Markdown文本
     * @returns {string} 纯文本
     */
    static stripMarkdown(text) {
        if (typeof text !== 'string') {
            return '';
        }
        
        // 预编译正则表达式（避免重复编译）
        const patterns = {
            // 数学公式（块级与行内）
            displayMath: /\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]/g,
            inlineMath: /\\\(.+?\\\)|(?<!\$)\$(?!\$)[^\$\n]+?\$(?!\$)/g,
            // 代码块（优先处理，避免处理代码块内的Markdown）
            codeBlocks: /```[\s\S]*?```|~~~[\s\S]*?~~~/g,
            // 行首标记（标题、引用、列表、水平线）
            lineStart: /^(#{1,6}\s+|>\s*|[\s]*[-*+]\s+|[\s]*\d+\.\s+|[-*_]{3,}$)/gm,
            // 内联格式（粗体、斜体、删除线、行内代码）
            inline: /(\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_|~~([^~]+)~~|`([^`]+)`)/g,
            // 链接
            links: /!?\[([^\]]*)\]\([^)]+\)/g,
            // 表格分隔符
            table: /\|/g,
            // 空白字符清理
            whitespace: /\n\s*\n/g,
            spaces: /\s+/g
        };
        
        // 分步处理，减少字符串操作次数
        let result = text;
        
        // 1. 移除数学公式与代码块
        result = result.replace(patterns.displayMath, '');
        result = result.replace(patterns.inlineMath, '');
        result = result.replace(patterns.codeBlocks, '');
        
        // 2. 处理行首标记
        result = result.replace(patterns.lineStart, '');
        
        // 3. 处理内联格式（使用回调函数提取内容）
        result = result.replace(patterns.inline, (match, p1, p2, p3, p4, p5, p6, p7) => {
            return p2 || p3 || p4 || p5 || p6 || p7 || '';
        });
        
        // 4. 处理链接
        result = result.replace(patterns.links, '$1');
        
        // 5. 清理表格和空白字符
        result = result
            .replace(patterns.table, ' ')
            .replace(patterns.whitespace, '\n')
            .replace(patterns.spaces, ' ')
            .trim();
        
        return result;
    }

    /**
     * 自动链接：协议 + RFC 3986 允许的 ASCII 字符（不含 CJK、全角标点等）
     * @type {string}
     */
    static get AUTO_LINK_URL_SOURCE() {
        return "[a-zA-Z][a-zA-Z0-9+.-]*:\\/\\/(?:[A-Za-z0-9\\-._~:/?#\\[\\]@!$&'()*+,;=%]|%[0-9A-Fa-f]{2})+";
    }

    /** @returns {RegExp} 全局匹配，用于 String.replace / matchAll */
    static get AUTO_LINK_URL_REGEX() {
        return new RegExp(`(${HtmlUtils.AUTO_LINK_URL_SOURCE})`, 'g');
    }

    /** @returns {RegExp} 非 global，用于 RegExp.test（避免 lastIndex 副作用） */
    static get AUTO_LINK_URL_TEST_REGEX() {
        return new RegExp(HtmlUtils.AUTO_LINK_URL_SOURCE);
    }

    /**
     * 去掉自动识别 URL 末尾常见的句读/括号（仍保留 URL 字符集内的合法结尾）
     * @param {string} url
     * @returns {string}
     */
    static trimAutoLinkUrl(url) {
        if (!url || typeof url !== 'string') {
            return '';
        }
        let s = url;
        const trailingPunct = /(?:[,;:!?]+|[\u3001\u3002\uff0c\uff0e\uff1a\uff1b\uff01\uff1f\uff09\uff3d\uff5d\u300b\u300d\u300f\uff02\uff07\u2026])+$/;
        for (;;) {
            const before = s;
            s = s.replace(trailingPunct, '');
            while (s.endsWith(')')) {
                const open = (s.match(/\(/g) || []).length;
                const close = (s.match(/\)/g) || []).length;
                if (close <= open) {
                    break;
                }
                s = s.slice(0, -1);
            }
            while (s.endsWith('\uFF09')) {
                const open = (s.match(/\uFF08/g) || []).length;
                const close = (s.match(/\uFF09/g) || []).length;
                if (close <= open) {
                    break;
                }
                s = s.slice(0, -1);
            }
            while (s.endsWith(']')) {
                const open = (s.match(/\[/g) || []).length;
                const close = (s.match(/\]/g) || []).length;
                if (close <= open) {
                    break;
                }
                s = s.slice(0, -1);
            }
            if (s.endsWith('.') && HtmlUtils.isValidUrl(s.slice(0, -1))) {
                s = s.slice(0, -1);
            }
            if (s === before) {
                break;
            }
        }
        return s;
    }

    /**
     * 从字符串开头提取符合规则的 URL（用于修正 marked 等产生的过长 href）
     * @param {string} str
     * @returns {string}
     */
    static extractAutoLinkUrl(str) {
        if (!str || typeof str !== 'string') {
            return '';
        }
        const re = new RegExp(`^${HtmlUtils.AUTO_LINK_URL_SOURCE}`);
        const match = str.match(re);
        if (!match) {
            return '';
        }
        return HtmlUtils.trimAutoLinkUrl(match[0]);
    }

    /**
     * 纯文本 → HTML：识别 URL 并转为链接（调用方若未转义，需自行保证 XSS 安全）
     * @param {string} text
     * @returns {string}
     */
    static linkifyPlainTextToHtml(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        text = text.trimStart();
        const parts = [];
        let lastIndex = 0;
        const re = new RegExp(HtmlUtils.AUTO_LINK_URL_SOURCE, 'g');
        let match;
        while ((match = re.exec(text)) !== null) {
            if (match.index > lastIndex) {
                parts.push(HtmlUtils.escapeHtml(text.slice(lastIndex, match.index)));
            }
            const rawUrl = match[0];
            const url = HtmlUtils.trimAutoLinkUrl(rawUrl);
            const tail = rawUrl.length > url.length
                ? HtmlUtils.escapeHtml(rawUrl.slice(url.length))
                : '';
            if (url && HtmlUtils.isValidUrl(url)) {
                const safeUrl = HtmlUtils.escapeHtml(url);
                parts.push(
                    `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="auto-link">${safeUrl}</a>${tail}`
                );
            } else {
                parts.push(HtmlUtils.escapeHtml(rawUrl));
            }
            lastIndex = match.index + rawUrl.length;
        }
        if (lastIndex < text.length) {
            parts.push(HtmlUtils.escapeHtml(text.slice(lastIndex)));
        }
        return parts.join('');
    }

    /**
     * 修正 HTML 中已有 &lt;a&gt; 的 href（如 marked GFM 用 [^\\s&lt;]* 误吞 CJK）
     * @param {string} html
     * @returns {string}
     */
    static normalizeAutoLinkAnchors(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }
        const container = document.createElement('div');
        container.innerHTML = html;
        container.querySelectorAll('a[href]').forEach((anchor) => {
            const href = anchor.getAttribute('href') || '';
            const fixed = HtmlUtils.extractAutoLinkUrl(href);
            if (!fixed || !HtmlUtils.isValidUrl(fixed) || href === fixed) {
                return;
            }
            if (!href.startsWith(fixed)) {
                return;
            }
            const hrefTail = href.slice(fixed.length);
            anchor.setAttribute('href', fixed);
            if (anchor.textContent === href) {
                anchor.textContent = fixed;
                if (hrefTail) {
                    anchor.after(document.createTextNode(hrefTail));
                }
            }
        });
        return container.innerHTML;
    }

    /**
     * 在 HTML 的文本节点中识别 URL（跳过已有 a/code/pre 等）
     * @param {string} html
     * @returns {string}
     */
    static linkifyHtmlContent(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }
        const urlRegex = HtmlUtils.AUTO_LINK_URL_REGEX;
        const urlTestRegex = HtmlUtils.AUTO_LINK_URL_TEST_REGEX;
        const container = document.createElement('div');
        container.innerHTML = html;

        const SKIP_TAGS = new Set(['A', 'CODE', 'PRE', 'SCRIPT', 'STYLE']);

        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
            acceptNode: (node) => {
                const parent = node.parentNode;
                if (!parent) {
                    return NodeFilter.FILTER_REJECT;
                }
                let el = parent;
                while (el && el.nodeType === 1) {
                    if (SKIP_TAGS.has(el.nodeName)) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    el = el.parentNode;
                }
                return urlTestRegex.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
            },
        });

        const nodes = [];
        let n;
        while ((n = walker.nextNode())) {
            nodes.push(n);
        }

        for (const textNode of nodes) {
            const text = textNode.nodeValue;
            const parts = [];
            let lastIndex = 0;
            text.replace(urlRegex, (match, url, offset) => {
                if (offset > lastIndex) {
                    parts.push(document.createTextNode(text.slice(lastIndex, offset)));
                }
                const linkUrl = HtmlUtils.trimAutoLinkUrl(url);
                const tail = linkUrl.length < url.length ? url.slice(linkUrl.length) : '';
                if (linkUrl && HtmlUtils.isValidUrl(linkUrl)) {
                    const a = document.createElement('a');
                    a.href = linkUrl;
                    a.target = '_blank';
                    a.rel = 'noopener noreferrer';
                    a.className = 'auto-link';
                    a.textContent = linkUrl;
                    parts.push(a);
                    if (tail) {
                        parts.push(document.createTextNode(tail));
                    }
                } else {
                    parts.push(document.createTextNode(url));
                }
                lastIndex = offset + match.length;
                return match;
            });
            if (lastIndex < text.length) {
                parts.push(document.createTextNode(text.slice(lastIndex)));
            }

            const parent = textNode.parentNode;
            if (parent) {
                for (const part of parts) {
                    parent.insertBefore(part, textNode);
                }
                parent.removeChild(textNode);
            }
        }

        return container.innerHTML;
    }

    /**
     * Markdown/HTML 正文：先修正错误 autolink，再 linkify 剩余裸 URL
     * @param {string} html
     * @returns {string}
     */
    static processRichTextLinks(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }
        return HtmlUtils.linkifyHtmlContent(HtmlUtils.normalizeAutoLinkAnchors(html));
    }

    /**
     * 验证URL是否安全
     * @param {string} url - 要验证的URL
     * @returns {boolean} 是否安全
     */
    static isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            // 只允许指定的安全协议
            const allowedProtocols = ['http:', 'https:', 'ftp:', 'mailto:', 'tel:', 'ed2k:', 'thunder:'];
            return allowedProtocols.includes(urlObj.protocol);
        } catch {
            return false;
        }
    }

    /**
     * 安全的HTML过滤，防止XSS攻击
     * @param {string} html - 要过滤的HTML
     * @returns {string} 过滤后的安全HTML
     */
    static sanitizeHtml(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }

        // 使用更简单的方法：先清理危险内容，再过滤标签
        let cleanHtml = html;
        
        // 移除危险的脚本和事件
        cleanHtml = cleanHtml.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        cleanHtml = cleanHtml.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');
        cleanHtml = cleanHtml.replace(/javascript:/gi, '');
        
        // 创建临时DOM元素
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = cleanHtml;
        
        // 允许的HTML标签
        const allowedTags = [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'del', 'strike',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'blockquote', 'pre', 'code',
            'a',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'hr', 'div', 'span'
        ];

        // 递归过滤节点
        const filterNode = (node) => {
            if (node.nodeType === Node.TEXT_NODE) {
                return node.cloneNode(true);
            }

            if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                // 检查标签是否被允许
                if (!allowedTags.includes(tagName)) {
                    // 如果不允许，返回文本内容
                    return document.createTextNode(node.textContent);
                }

                // 创建新的元素
                const newElement = document.createElement(tagName);

                // 复制安全的属性
                for (const attr of node.attributes) {
                    const attrName = attr.name.toLowerCase();
                    if (['href', 'src', 'alt', 'title', 'class', 'id', 'data-math-idx'].includes(attrName)) {
                        if (attrName === 'href') {
                            const href = attr.value;
                            if (this.isValidUrl(href)) {
                                newElement.setAttribute('href', href);
                                if (href.startsWith('http') && !href.includes(window.location.hostname)) {
                                    newElement.setAttribute('target', '_blank');
                                    newElement.setAttribute('rel', 'noopener noreferrer');
                                }
                            }
                        } else {
                            newElement.setAttribute(attrName, this.escapeHtml(attr.value));
                        }
                    }
                }

                // 递归处理子节点
                for (const child of node.childNodes) {
                    const filteredChild = filterNode(child);
                    if (filteredChild) {
                        newElement.appendChild(filteredChild);
                    }
                }

                return newElement;
            }

            return null;
        };

        // 过滤所有子节点
        const filteredNodes = [];
        for (const child of tempDiv.childNodes) {
            const filteredChild = filterNode(child);
            if (filteredChild) {
                filteredNodes.push(filteredChild);
            }
        }

        // 创建新的容器
        const newContainer = document.createElement('div');
        filteredNodes.forEach(node => newContainer.appendChild(node));

        return newContainer.innerHTML;
    }
}

// 导出工具类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HtmlUtils;
}

// 全局访问（用于非模块环境）
if (typeof window !== 'undefined') {
    window.HtmlUtils = HtmlUtils;
}
