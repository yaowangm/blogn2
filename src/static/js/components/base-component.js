/**
 * 基础组件类
 * 提供所有Web组件共用的基础功能
 */
class BaseComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.metadata = null;
    }

    /**
     * 加载网站元数据
     * 所有组件共享的元数据加载逻辑
     */
    async loadMetadata() {
        try {
            const response = await fetch('/api/metadata/');
            if (response.ok) {
                this.metadata = await response.json();
            } else {
                this.logError('Failed to load metadata', response.status);
                this.metadata = this.getDefaultMetadata();
            }
        } catch (error) {
            this.logError('Error loading metadata', error);
            this.metadata = this.getDefaultMetadata();
        }
    }

    /**
     * 统一的错误日志记录
     * @param {string} message - 错误消息
     * @param {any} error - 错误对象
     */
    logError(message, error) {
        console.error(`${message}:`, error);
        // TODO: 添加错误上报逻辑
    }

    /**
     * 获取默认元数据
     * 当API请求失败时使用的默认值
     */
    getDefaultMetadata() {
        return {
            site_name: 'BlogN',
            logo_url: '/static/images/logo.svg',
            user_count: 0,
            post_count: 0
        };
    }

    /**
     * 获取Logo URL
     * 根据当前主题返回相应的Logo URL
     */
    getLogoUrl() {
        const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const baseUrl = this.metadata?.logo_url || '/static/images/logo.svg';
        
        if (isDarkMode) {
            return baseUrl.replace('logo.svg', 'logo-dark.svg');
        } else {
            return baseUrl.replace('logo.svg', 'logo-light.svg');
        }
    }

    /**
     * 格式化日期
     * 将ISO日期字符串格式化为可读格式
     */
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        
        // 计算日期差（不考虑时间）
        const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const diffDays = Math.floor((nowOnly - dateOnly) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            // 今天：显示小时和分钟
            const diffTime = now - date;
            const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
            const diffMinutes = Math.floor((diffTime % (1000 * 60 * 60)) / (1000 * 60));
            
            if (diffHours > 0) {
                return `${diffHours}小时${diffMinutes}分钟前`;
            } else if (diffMinutes > 0) {
                return `${diffMinutes}分钟前`;
            } else {
                return '刚刚';
            }
        } else if (diffDays === 1) {
            return '昨天';
        } else if (diffDays < 7) {
            return `${diffDays}天前`;
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }

    /**
     * 截断文本
     * 将长文本截断到指定长度并添加省略号
     */
    truncateText(text, maxLength = 20) {
        if (!text) return '';
        
        const cleanText = text.replace(/\\r\\n/g, ' ').replace(/\\n/g, ' ').trim();
        return cleanText.length > maxLength 
            ? cleanText.substring(0, maxLength) + '...' 
            : cleanText;
    }

    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * 创建加载状态HTML
     * 统一的加载状态显示
     */
    createLoadingHTML() {
        return `
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                color: var(--gray-500);
                font-size: 14px;
            ">
                <div style="
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--gray-200);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 8px;
                "></div>
                加载中...
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
    }

    /**
     * 创建错误状态HTML
     * 统一的错误状态显示
     */
    createErrorHTML(message = '加载失败') {
        return `
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                color: var(--red-500);
                font-size: 14px;
            ">
                <span style="margin-right: 8px;">${Icons.warning}</span>
                ${message}
            </div>
        `;
    }

    /**
     * 获取项目ID
     * 统一处理博客页面和文章页面的项目ID获取
     * 支持 /blog/{project_id}、/article/{article_id} 和 /edit-article/{article_id} 三种URL格式
     */
    getProjectId() {
        const path = window.location.pathname;
        
        // 尝试从博客页面URL获取项目ID
        const blogMatch = path.match(/\/blog\/(\d+)/);
        if (blogMatch) {
            return parseInt(blogMatch[1]);
        }
        
        // 尝试从文章页面URL获取文章ID
        const articleMatch = path.match(/\/article\/(\d+)/);
        if (articleMatch) {
            // 在文章页面，我们需要从文章ID获取项目ID
            // 这里返回null，让组件知道当前在文章页面
            return null;
        }
        
        // 尝试从编辑文章页面URL获取文章ID
        const editArticleMatch = path.match(/\/edit-article\/(\d+)/);
        if (editArticleMatch) {
            // 在编辑文章页面，我们需要从文章ID获取项目ID
            // 这里返回null，让组件知道当前在编辑文章页面
            return null;
        }
        
        return null;
    }

    /**
     * 获取文章ID
     * 从URL中获取文章ID
     * 支持 /article/{article_id} 和 /edit-article/{article_id} 两种URL格式
     */
    getArticleId() {
        const path = window.location.pathname;
        
        // 尝试从文章页面URL获取文章ID
        const articleMatch = path.match(/\/article\/(\d+)/);
        if (articleMatch) {
            return parseInt(articleMatch[1]);
        }
        
        // 尝试从编辑文章页面URL获取文章ID
        const editArticleMatch = path.match(/\/edit-article\/(\d+)/);
        if (editArticleMatch) {
            return parseInt(editArticleMatch[1]);
        }
        
        return null;
    }

    /**
     * 检查当前是否在文章页面
     * 包括文章详情页面和编辑文章页面
     */
    isArticlePage() {
        const path = window.location.pathname;
        return path.includes('/article/') || path.includes('/edit-article/');
    }

    /**
     * 安全的HTML过滤，防止XSS攻击
     * 所有组件共享的HTML安全过滤方法
     */
    sanitizeHtml(html) {
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

    /**
     * 验证URL是否安全
     */
    isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            return ['http:', 'https:', 'mailto:'].includes(urlObj.protocol);
        } catch {
            return false;
        }
    }

    /**
     * 验证图片src是否安全
     */
    isValidImageSrc(src) {
        try {
            const urlObj = new URL(src);
            return ['http:', 'https:'].includes(urlObj.protocol);
        } catch {
            return false;
        }
    }

    /**
     * HTML转义，防止XSS攻击
     */
    escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * 移除Markdown标记，返回纯文本
     * 用于在摘要列表中显示纯文本内容
     */
    stripMarkdown(text) {
        if (typeof text !== 'string') {
            return '';
        }
        
        return text
            // 移除标题标记
            .replace(/^#{1,6}\s+/gm, '')
            // 移除粗体和斜体标记
            .replace(/\*\*([^*]+)\*\*/g, '$1')
            .replace(/\*([^*]+)\*/g, '$1')
            .replace(/__([^_]+)__/g, '$1')
            .replace(/_([^_]+)_/g, '$1')
            // 移除删除线标记
            .replace(/~~([^~]+)~~/g, '$1')
            // 移除行内代码标记
            .replace(/`([^`]+)`/g, '$1')
            // 移除代码块标记
            .replace(/```[\s\S]*?```/g, '')
            .replace(/~~~[\s\S]*?~~~/g, '')
            // 移除链接标记，保留链接文本
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            // 移除图片标记
            .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
            // 移除引用标记
            .replace(/^>\s*/gm, '')
            // 移除列表标记
            .replace(/^[\s]*[-*+]\s+/gm, '')
            .replace(/^[\s]*\d+\.\s+/gm, '')
            // 移除水平线
            .replace(/^[-*_]{3,}$/gm, '')
            // 移除表格标记
            .replace(/\|/g, ' ')
            // 移除多余的空白字符
            .replace(/\n\s*\n/g, '\n')
            .replace(/\s+/g, ' ')
            .trim();
    }
}

// 注册基础组件（不直接使用，仅作为基类）
customElements.define('base-component', BaseComponent); 