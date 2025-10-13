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
            // 代码块（优先处理，避免处理代码块内的Markdown）
            codeBlocks: /```[\s\S]*?```|~~~[\s\S]*?~~~/g,
            // 行首标记（标题、引用、列表、水平线）
            lineStart: /^(#{1,6}\s+|>\s*|[\s]*[-*+]\s+|[\s]*\d+\.\s+|[-*_]{3,}$)/gm,
            // 内联格式（粗体、斜体、删除线、行内代码）
            inline: /(\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_|~~([^~]+)~~|`([^`]+)`)/g,
            // 链接和图片
            links: /!?\[([^\]]*)\]\([^)]+\)/g,
            // 表格分隔符
            table: /\|/g,
            // 空白字符清理
            whitespace: /\n\s*\n/g,
            spaces: /\s+/g
        };
        
        // 分步处理，减少字符串操作次数
        let result = text;
        
        // 1. 移除代码块（避免处理代码块内的Markdown语法）
        result = result.replace(patterns.codeBlocks, '');
        
        // 2. 处理行首标记
        result = result.replace(patterns.lineStart, '');
        
        // 3. 处理内联格式（使用回调函数提取内容）
        result = result.replace(patterns.inline, (match, p1, p2, p3, p4, p5, p6, p7) => {
            return p2 || p3 || p4 || p5 || p6 || p7 || '';
        });
        
        // 4. 处理链接和图片
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
     * 验证URL是否安全
     * @param {string} url - 要验证的URL
     * @returns {boolean} 是否安全
     */
    static isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            // 允许任何有效的协议，但排除一些明显不安全的协议
            const disallowedProtocols = ['javascript:', 'data:', 'vbscript:', 'file:'];
            return !disallowedProtocols.includes(urlObj.protocol);
        } catch {
            return false;
        }
    }

    /**
     * 验证图片src是否安全
     * @param {string} src - 要验证的图片src
     * @returns {boolean} 是否安全
     */
    static isValidImageSrc(src) {
        try {
            const urlObj = new URL(src);
            return ['http:', 'https:'].includes(urlObj.protocol);
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
            'a', 'img',
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
                    if (['href', 'src', 'alt', 'title', 'class', 'id'].includes(attrName)) {
                        if (attrName === 'href') {
                            const href = attr.value;
                            if (this.isValidUrl(href)) {
                                newElement.setAttribute('href', href);
                                if (href.startsWith('http') && !href.includes(window.location.hostname)) {
                                    newElement.setAttribute('target', '_blank');
                                    newElement.setAttribute('rel', 'noopener noreferrer');
                                }
                            }
                        } else if (attrName === 'src') {
                            const src = attr.value;
                            if (this.isValidImageSrc(src)) {
                                newElement.setAttribute('src', src);
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
