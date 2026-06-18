/**
 * 基础组件类 (BaseComponent)
 * 
 * 提供所有Web组件共用的基础功能，包括：
 * - 统一的错误处理和日志记录
 * - 通用的工具方法（HTML转义、日期格式化等）
 * - 安全的内容过滤和验证
 * - 统一的加载和错误状态显示
 * - 项目ID和文章ID的获取逻辑
 * - 单列布局同步（`_attachLayoutSingleColumnObserver`，与 `body.layout-single-column` 一致）
 * 
 * 所有自定义Web组件都应该继承此类以获得基础功能。
 */
class BaseComponent extends HTMLElement {
    static _projectCache = {};
    static _projectPromises = {};
    static _articleCache = {};
    static _articlePromises = {};
    static _metadataCache = null;
    static _metadataPromise = null;
    static _userCache = {};
    static _userPromises = {};
    static _appConfigCache = null;
    static _appConfigPromise = null;

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
        this.metadata = await BaseComponent.getMetadata();
    }

    static async getMetadata() {
        if (BaseComponent._metadataCache) return BaseComponent._metadataCache;
        if (BaseComponent._metadataPromise) return BaseComponent._metadataPromise;
        BaseComponent._metadataPromise = (async () => {
            try {
                const response = await fetch('/api/metadata/');
                if (response.ok) {
                    BaseComponent._metadataCache = await response.json();
                    return BaseComponent._metadataCache;
                }
            } catch (error) {
                console.error('Error loading metadata:', error);
            }
            const fallback = {
                site_name: 'BlogN',
                logo_url: '/static/favicon.svg',
                user_count: 0,
                post_count: 0,
            };
            BaseComponent._metadataCache = fallback;
            return fallback;
        })();
        try {
            return await BaseComponent._metadataPromise;
        } finally {
            BaseComponent._metadataPromise = null;
        }
    }

    static async getUser(userId) {
        if (!userId) return null;
        if (BaseComponent._userCache[userId]) return BaseComponent._userCache[userId];
        if (BaseComponent._userPromises[userId]) return BaseComponent._userPromises[userId];
        BaseComponent._userPromises[userId] = (async () => {
            try {
                const response = await fetch(`/api/users/${userId}`);
                if (!response.ok) return null;
                const data = await response.json();
                BaseComponent._userCache[userId] = data;
                return data;
            } catch (error) {
                console.warn(`Failed to load user ${userId}:`, error);
                return null;
            } finally {
                delete BaseComponent._userPromises[userId];
            }
        })();
        return BaseComponent._userPromises[userId];
    }

    static async getAppConfig() {
        if (BaseComponent._appConfigCache) return BaseComponent._appConfigCache;
        if (BaseComponent._appConfigPromise) return BaseComponent._appConfigPromise;
        BaseComponent._appConfigPromise = (async () => {
            try {
                const response = await fetch('/api/config/app');
                if (response.ok) {
                    BaseComponent._appConfigCache = await response.json();
                    return BaseComponent._appConfigCache;
                }
            } catch (error) {
                console.warn('Failed to load app config:', error);
            }
            const fallback = { blog_posts_page_size: 10, max_attachments_per_article: 5 };
            BaseComponent._appConfigCache = fallback;
            return fallback;
        })();
        try {
            return await BaseComponent._appConfigPromise;
        } finally {
            BaseComponent._appConfigPromise = null;
        }
    }

    static observeWhenVisible(element, callback, rootMargin = '120px') {
        if (!element || typeof callback !== 'function') return;
        if (!('IntersectionObserver' in window)) {
            callback();
            return;
        }
        const observer = new IntersectionObserver((entries) => {
            if (entries.some((entry) => entry.isIntersecting)) {
                observer.disconnect();
                callback();
            }
        }, { rootMargin });
        observer.observe(element);
    }

    /**
     * 等待两帧布局稳定（字体、KaTeX、图片占位等）。
     */
    static waitForLayoutSettle() {
        return new Promise((resolve) => {
            requestAnimationFrame(() => {
                requestAnimationFrame(resolve);
            });
        });
    }

    /**
     * 等待 Shadow DOM / 容器内图片加载完成后再继续（含 lazy 图 promoted 为 eager）。
     */
    static waitForImagesInRoot(root, timeoutMs = 15000) {
        if (!root) {
            return BaseComponent.waitForLayoutSettle();
        }

        const images = [...root.querySelectorAll('img')].filter((img) => {
            const rect = img.getBoundingClientRect();
            return rect.width > 0 || rect.height > 0 || img.offsetParent !== null;
        });
        images.forEach((img) => {
            if (!img.complete && img.loading === 'lazy') {
                img.loading = 'eager';
            }
        });

        const pending = images.filter((img) => !img.complete);
        if (pending.length === 0) {
            return BaseComponent.waitForLayoutSettle();
        }

        return new Promise((resolve) => {
            let settled = 0;
            const cleanups = [];
            let resolved = false;
            const done = () => {
                if (resolved) {
                    return;
                }
                resolved = true;
                clearTimeout(timer);
                cleanups.forEach((cleanup) => cleanup());
                resolve();
            };
            const finish = () => {
                settled += 1;
                if (settled >= pending.length) {
                    done();
                }
            };
            const timer = setTimeout(done, timeoutMs);
            pending.forEach((img) => {
                img.addEventListener('load', finish, { once: true });
                img.addEventListener('error', finish, { once: true });
                cleanups.push(() => {
                    img.removeEventListener('load', finish);
                    img.removeEventListener('error', finish);
                });
            });
        }).then(() => BaseComponent.waitForLayoutSettle());
    }

    /**
     * 等待自定义元素满足就绪条件（如数据已加载）。
     */
    static async waitForCustomElementReady(selector, isReady, timeoutMs = 15000) {
        const start = Date.now();
        while (Date.now() - start < timeoutMs) {
            const element = document.querySelector(selector);
            if (element && isReady(element)) {
                return element;
            }
            await new Promise((resolve) => setTimeout(resolve, 50));
        }
        return null;
    }

    /**
     * 固定顶栏（header-component）占用的高度，用于 scroll 偏移。
     */
    static getScrollTopOffset(extra = 8) {
        const header = document.querySelector('header-component');
        const headerHeight = header ? header.getBoundingClientRect().height : 64;
        return headerHeight + extra;
    }

    /**
     * 将元素滚入视口，并留出 sticky 顶栏空间。
     */
    static scrollElementIntoView(element, options = {}) {
        if (!element) {
            return;
        }
        const behavior = options.behavior ?? 'auto';
        const offset = options.offset ?? BaseComponent.getScrollTopOffset();
        const top = window.scrollY + element.getBoundingClientRect().top - offset;
        window.scrollTo({ top: Math.max(0, top), behavior });
    }

    /**
     * 翻页后将所属卡片顶部滚入视口（留出 sticky 顶栏空间）。
     */
    scrollPaginatedCardToTop(options = {}) {
        const behavior = options.behavior ?? 'auto';

        void BaseComponent.waitForLayoutSettle().then(() => {
            const card = this.shadowRoot?.querySelector('.card') ?? this;
            BaseComponent.scrollElementIntoView(card, {
                behavior,
                offset: options.offset,
            });
        });
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
            logo_url: '/static/favicon.svg',
            user_count: 0,
            post_count: 0
        };
    }

    /**
     * 获取Logo URL
     * 站点 Logo 与 favicon 共用同一 SVG，不做主题切换。
     */
    getLogoUrl() {
        return this.metadata?.logo_url || '/static/favicon.svg';
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
     * 将文章表单的 Markdown 正文渲染到预览容器。
     * create/edit 表单共用，保持空内容、库缺失和解析失败时的原有展示。
     */
    renderMarkdownPreview(previewContent, content) {
        if (!previewContent) {
            console.error('preview-content element not found!');
            return;
        }

        if (!content.trim()) {
            previewContent.innerHTML = '<p class="no-content">暂无内容</p>';
            return;
        }

        if (typeof MarkdownUtils === 'undefined') {
            console.error('MarkdownUtils is not available');
            previewContent.innerHTML = '<p style="color: red;">错误：Markdown 解析库未加载，请刷新页面重试</p>';
            return;
        }

        try {
            MarkdownUtils.ensureKatexStyles(this.shadowRoot);
            const html = MarkdownUtils.parseMarkdown(content);

            previewContent.innerHTML = HtmlUtils.processRichTextLinks(html);
        } catch (error) {
            console.error('Markdown parsing failed in preview', error);
            this.logError('Markdown parsing failed in preview', error);
            // 如果Markdown解析失败，显示原始文本
            previewContent.innerHTML = `<pre>${this.escapeHtml(content)}</pre>`;
        }
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
     * 从 URL 查询参数获取当前页码（用于博客列表分页）
     * @returns {number} 页码，默认为 1
     */
    getCurrentPageFromUrl() {
        const url = new URL(window.location.href);
        const page = url.searchParams.get('page');
        if (page === null || page === '') return 1;
        const n = parseInt(page, 10);
        return isNaN(n) || n < 1 ? 1 : n;
    }

    /**
     * 全站共享：按 projectId 获取项目数据，同页多组件只请求一次
     * @param {number} projectId
     * @returns {Promise<object|null>} 成功返回数据，404 返回 null
     */
    static async getProject(projectId) {
        if (!projectId) return null;
        if (BaseComponent._projectCache[projectId]) return BaseComponent._projectCache[projectId];
        if (BaseComponent._projectPromises[projectId]) return BaseComponent._projectPromises[projectId];
        const p = (async () => {
            try {
                const res = await fetch(`/api/projects/${projectId}`);
                if (res.status === 404) return null;
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                BaseComponent._projectCache[projectId] = data;
                return data;
            } finally {
                delete BaseComponent._projectPromises[projectId];
            }
        })();
        BaseComponent._projectPromises[projectId] = p;
        return p;
    }

    /**
     * 全站共享：按 articleId 获取文章数据，同页多组件只请求一次
     * @param {number} articleId
     * @returns {Promise<object|null>} 成功返回数据，404 返回 null
     */
    static async getArticle(articleId) {
        if (!articleId) return null;
        if (BaseComponent._articleCache[articleId]) return BaseComponent._articleCache[articleId];
        if (BaseComponent._articlePromises[articleId]) return BaseComponent._articlePromises[articleId];
        const headers = (typeof UserManager !== 'undefined' && UserManager.createHeaders) ? UserManager.createHeaders() : {};
        const p = (async () => {
            try {
                const res = await fetch(`/api/articles/${articleId}`, { headers });
                if (res.status === 404) return null;
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                BaseComponent._articleCache[articleId] = data;
                return data;
            } finally {
                delete BaseComponent._articlePromises[articleId];
            }
        })();
        BaseComponent._articlePromises[articleId] = p;
        return p;
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
     * 移除Markdown标记，返回纯文本
     * 用于在摘要列表中显示纯文本内容
     * 高性能版本：使用预编译正则表达式和优化的处理流程
     */
    stripMarkdown(text) {
        return HtmlUtils.stripMarkdown(text);
    }

    isAnonymousUser(userId) {
        return !userId || userId === 0;
    }

    getDefaultUserAvatarIconHtml() {
        if (typeof Icons !== 'undefined' && Icons.user) {
            return Icons.user.replace(
                /<svg[^>]*>/,
                '<svg class="author-avatar-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
            );
        }
        return '用';
    }

    getAuthorAvatarFallbackContent(authorName, userId) {
        if (this.isAnonymousUser(userId)) {
            return this.getDefaultUserAvatarIconHtml();
        }
        const name = authorName || '用户';
        return this.escapeHtml(name).charAt(0).toUpperCase();
    }

    /**
     * 与 `sidebar-collapse` 同步整页单列模式：`document.body` 含 `layout-single-column` 时
     * 在宿主上设置 `data-layout-single-column`，供 Shadow 内 `:host([...])` 使用（`:host-context` 在 Shadow 中不可靠）。
     * 在子类 `connectedCallback` 开头调用；在 `disconnectedCallback` 中调用 {@link BaseComponent#_detachLayoutSingleColumnObserver}。
     */
    _attachLayoutSingleColumnObserver() {
        if (this._layoutBodyObserver) {
            return;
        }
        const sync = () => {
            if (document.body.classList.contains('layout-single-column')) {
                this.setAttribute('data-layout-single-column', '');
            } else {
                this.removeAttribute('data-layout-single-column');
            }
        };
        this._layoutBodyObserver = new MutationObserver(sync);
        this._layoutBodyObserver.observe(document.body, {
            attributes: true,
            attributeFilter: ['class'],
        });
        sync();
    }

    _detachLayoutSingleColumnObserver() {
        if (this._layoutBodyObserver) {
            this._layoutBodyObserver.disconnect();
            this._layoutBodyObserver = null;
        }
    }
}

// 鼠标点击后移除焦点环（尤其 target="_blank" 的卡片链接）
(function initBlognUiFocusHandlers() {
    if (typeof document === 'undefined' || document.__blognUiFocusInit) {
        return;
    }
    document.__blognUiFocusInit = true;

    document.addEventListener('click', (event) => {
        if (event.detail === 0) {
            return;
        }
        const path = event.composedPath();
        const el = path.find((node) => {
            if (!(node instanceof Element)) {
                return false;
            }
            return node.matches(
                'a[target="_blank"], a.post-item, a.blog-item, a.blog-profile-link, .nav-item, button.tab, .pagination-btn, .create-post-button'
            );
        });
        if (el && typeof el.blur === 'function') {
            requestAnimationFrame(() => el.blur());
        }
    });
})();

// 注册基础组件（不直接使用，仅作为基类）
customElements.define('base-component', BaseComponent);
