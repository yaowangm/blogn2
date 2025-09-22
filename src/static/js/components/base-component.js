/**
 * 基础组件类 (BaseComponent)
 * 
 * 提供所有Web组件共用的基础功能，包括：
 * - 统一的错误处理和日志记录
 * - 通用的工具方法（HTML转义、日期格式化等）
 * - 安全的内容过滤和验证
 * - 统一的加载和错误状态显示
 * - 项目ID和文章ID的获取逻辑
 * 
 * 所有自定义Web组件都应该继承此类以获得基础功能。
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
        // 可以在这里添加错误上报逻辑
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
     * 支持过去和未来日期的正确显示
     * 
     * @param {string} dateString - ISO日期字符串
     * @returns {string} 格式化后的日期字符串
     */
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        
        // 检查是否为未来日期
        if (date > now) {
            // 计算日期差（不考虑时间）
            const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
            const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const diffDays = Math.floor((dateOnly - nowOnly) / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) {
                // 今天：显示小时和分钟
                const diffTime = date - now;
                const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
                const diffMinutes = Math.floor((diffTime % (1000 * 60 * 60)) / (1000 * 60));
                
                if (diffHours > 0) {
                    return `${diffHours}小时后`;
                } else if (diffMinutes > 0) {
                    return `${diffMinutes}分钟后`;
                } else {
                    return '即将到来';
                }
            } else if (diffDays === 1) {
                return '明天';
            } else if (diffDays < 7) {
                return `${diffDays}天后`;
            } else {
                return date.toLocaleDateString('zh-CN');
            }
        }
        
        // 过去日期的处理
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
        return HtmlUtils.truncateText(text, maxLength);
    }

    /**
     * 检查是否可以提交（防重复提交）
     * 检查submitting和loading状态，防止重复提交
     * 
     * @returns {boolean} 是否可以提交
     */
    canSubmit() {
        return !(this.submitting || this.loading);
    }

    /**
     * 创建防重复提交的表单提交处理器
     * 自动检查提交状态，防止重复提交
     * 
     * @param {Function} submitHandler - 实际的提交处理函数
     * @returns {Function} 包装后的提交处理器
     */
    createSubmitHandler(submitHandler) {
        return (event) => {
            event.preventDefault();
            
            // 防止重复提交：检查提交锁和loading状态
            if (!this.canSubmit()) {
                return;
            }
            
            submitHandler.call(this);
        };
    }

    /**
     * 更新提交按钮状态
     * 根据loading和submitting状态更新按钮的禁用状态和显示内容
     * 
     * @param {string} loadingText - 加载时显示的文本
     * @param {string} normalText - 正常状态显示的文本
     */
    updateSubmitButtonState(loadingText = '处理中...', normalText = '提交') {
        const submitBtn = this.shadowRoot.querySelector('button[type="submit"]');
        
        if (submitBtn) {
            if (this.loading || this.submitting) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <div class="loading">
                        <div class="loading-spinner"></div>
                        ${loadingText}
                    </div>
                `;
            } else {
                submitBtn.disabled = false;
                submitBtn.innerHTML = normalText;
            }
        }
    }

    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */
    escapeHtml(text) {
        return HtmlUtils.escapeHtml(text);
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
        return HtmlUtils.sanitizeHtml(html);
    }

    /**
     * 验证URL是否安全
     */
    isValidUrl(url) {
        return HtmlUtils.isValidUrl(url);
    }

    /**
     * 验证图片src是否安全
     */
    isValidImageSrc(src) {
        return HtmlUtils.isValidImageSrc(src);
    }


    /**
     * 移除Markdown标记，返回纯文本
     * 用于在摘要列表中显示纯文本内容
     * 高性能版本：使用预编译正则表达式和优化的处理流程
     */
    stripMarkdown(text) {
        return HtmlUtils.stripMarkdown(text);
    }
}

// 注册基础组件（不直接使用，仅作为基类）
customElements.define('base-component', BaseComponent); 