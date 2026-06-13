/**
 * 文章头部卡片组件
 * 显示文章的标题、作者、日期、分类、点击数等基本信息
 */
class ArticleHeaderCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
        this.currentUser = null;
        this.isAdmin = false;
        this.isAuthor = false;
    }

    async connectedCallback() {
        this._attachLayoutSingleColumnObserver();

        // 从URL获取文章ID
        this.articleId = this.getArticleIdFromUrl();
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        // 检查当前用户权限
        await this.checkUserPermissions();

        // 加载文章数据
        await this.loadArticleData();
        
        // 渲染组件
        this.render();
        
        // 更新页面标题
        this.updatePageTitle();
    }

    disconnectedCallback() {
        this._detachLayoutSingleColumnObserver();
    }

    /**
     * 从URL获取文章ID
     */
    getArticleIdFromUrl() {
        // 使用基类的统一方法
        return this.getArticleId();
    }

    /**
     * 检查当前用户权限
     */
    async checkUserPermissions() {
        try {
            // 从UserManager获取当前用户信息
            if (!UserManager.isLoggedIn()) {
                // 用户未登录
                this.currentUser = null;
                this.isAdmin = false;
                this.isAuthor = false;
                return;
            }

            this.currentUser = UserManager.getCurrentUser();
            
            // 检查是否为管理员（state为10表示管理员）
            this.isAdmin = this.currentUser.state === 10;
            
            // 检查是否为文章作者（需要等待文章数据加载后才能确定）
            // 这里先设置为false，在loadArticleData后再次检查
            this.isAuthor = false;
            
        } catch (error) {
            this.logError('Failed to check user permissions', error);
            this.currentUser = null;
            this.isAdmin = false;
            this.isAuthor = false;
        }
    }

    /**
     * 加载文章数据
     */
    async loadArticleData() {
        try {
            const articleData = await BaseComponent.getArticle(this.articleId);
            if (articleData === null) {
                window.location.href = '/static/error.html';
                return;
            }
            this.articleData = articleData;
            if (this.currentUser && articleData.author) {
                this.isAuthor = this.currentUser.id === articleData.author.id;
            }
        } catch (error) {
            this.logError('Failed to load article data', error);
            window.location.href = '/static/error.html';
        }
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.shadowRoot.innerHTML = `
                <div class="card article-header-card">
                    <div class="card-body">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            `;
            return;
        }

        const { title, author, project, category, hits, itemsize, created_at, comment_count, itemtype } = this.articleData;

        // 检查是否显示工具栏
        const showToolbar = this.isAdmin || this.isAuthor;
        
        // 检查是否显示"设为个人介绍"按钮
        // 只有当前用户是文章作者且文章有附件图片时才显示
        const showSetIntroButton = this.isAuthor && this.articleData.attachment;
        
        // 检查是否显示"设为网站介绍"按钮
        // 只有管理员才能设置网站介绍
        const showSetSiteIntroButton = this.isAdmin;
        
        this.shadowRoot.innerHTML = `
            <div class="card article-header-card">
                <div class="card-body">
                    <div class="article-title">
                        <h1>${title || '无标题'}</h1>
                    </div>
                    
                    ${this.renderArticleMeta({
                        author,
                        project,
                        category,
                        created_at,
                        itemtype,
                        isAdmin: this.isAdmin,
                        showToolbar,
                        showSetSiteIntroButton,
                        showSetIntroButton
                    })}
                    ${this.renderArticleStats(hits, comment_count, itemsize)}
                </div>
            </div>
        `;

        this.addStyles();
        
        // 绑定工具栏事件
        if (showToolbar) {
            this.bindToolbarEvents();
        }
    }

    /**
     * 更新页面标题
     */
    updatePageTitle() {
        if (this.articleData && this.articleData.title) {
            document.title = `${this.articleData.title} - BlogN`;
        }
    }

    /**
     * 绑定工具栏事件
     */
    bindToolbarEvents() {
        const setSiteIntroBtn = this.shadowRoot.getElementById('set-site-intro-btn');
        const setIntroBtn = this.shadowRoot.getElementById('set-intro-btn');
        const editBtn = this.shadowRoot.getElementById('edit-article-btn');
        const deleteBtn = this.shadowRoot.getElementById('delete-article-btn');
        const permanentDeleteBtn = this.shadowRoot.getElementById('permanent-delete-article-btn');
        
        if (setSiteIntroBtn) {
            setSiteIntroBtn.addEventListener('click', () => this.handleSetSiteIntro());
        }
        
        if (setIntroBtn) {
            setIntroBtn.addEventListener('click', () => this.handleSetIntro());
        }
        
        if (editBtn) {
            editBtn.addEventListener('click', () => this.handleEditArticle());
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.handleDeleteArticle());
        }
        
        if (permanentDeleteBtn) {
            permanentDeleteBtn.addEventListener('click', () => this.handlePermanentDeleteArticle());
        }
    }

    /**
     * 处理设为网站介绍
     */
    async handleSetSiteIntro() {
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '设为网站介绍',
            message: '确定要将此文章设为网站介绍吗？',
        })) {
            return;
        }

        try {
            const token = UserManager.getAccessToken();
            if (!token) {
                this.showError('请先登录');
                return;
            }
            
            const response = await fetch(`/api/blogs/set-intro/${this.articleId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '设置失败');
            }

            const result = await response.json();
            this.showSuccess(result.message);
            
        } catch (error) {
            this.logError('设置网站介绍失败', error);
            this.showError('设置网站介绍失败: ' + error.message);
        }
    }

    /**
     * 处理设为个人介绍
     */
    async handleSetIntro() {
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }
        
        if (!this.articleData.attachment) {
            alert('此文章没有附件图片，无法设为个人介绍');
            return;
        }
        
        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '设为个人介绍',
            message: '确定要将此文章设为个人介绍吗？\n\n此操作将：\n1. 将此文章设为您的个人介绍\n2. 将文章的附件图片复制为您的头像图片\n3. 如果已有头像，将被新图片覆盖',
        })) {
            return;
        }
        
        try {
            const headers = UserManager.createHeaders({
                'Content-Type': 'application/json'
            });
            
            const response = await fetch(`/api/users/set-intro`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    article_id: this.articleId
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                alert('个人介绍设置成功！');
                // 刷新页面以显示更新后的信息
                window.location.reload();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || '设置个人介绍失败');
            }
        } catch (error) {
            this.logError('Failed to set intro', error);
            alert('设置个人介绍失败: ' + error.message);
        }
    }

    /**
     * 处理修改文章
     */
    handleEditArticle() {
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }
        
        // 跳转到文章编辑页面
        window.location.href = `/edit-article/${this.articleId}`;
    }

    /**
     * 处理删除文章
     */
    async handleDeleteArticle() {
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }
        
        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '删除文章',
            message: '确定要删除这篇文章吗？此操作不可撤销。',
            danger: true,
        })) {
            return;
        }
        
        try {
            const headers = UserManager.createHeaders({
                'Content-Type': 'application/json'
            });
            const response = await fetch(`/api/articles/${this.articleId}`, {
                method: 'DELETE',
                headers: headers
            });
            
            if (response.ok) {
                // 删除成功，跳转到首页
                alert('文章删除成功');
                window.location.href = '/';
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || '删除失败');
            }
        } catch (error) {
            this.logError('Failed to delete article', error);
            alert('删除文章失败: ' + error.message);
        }
    }

    /**
     * 处理彻底删除文章
     */
    async handlePermanentDeleteArticle() {
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }
        
        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '彻底删除文章',
            message: '确定要彻底删除这篇文章吗？\n\n此操作将：\n1. 永久删除文章的所有图片文件\n2. 从数据库中完全删除文章记录\n3. 更新相关统计信息\n\n此操作不可撤销！',
            danger: true,
        })) {
            return;
        }

        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '最后确认',
            message: '最后确认：您真的要彻底删除这篇文章吗？\n\n一旦执行，文章及其所有相关数据将永久消失！',
            danger: true,
        })) {
            return;
        }
        
        try {
            const headers = UserManager.createHeaders({
                'Content-Type': 'application/json'
            });
            const response = await fetch(`/api/articles/${this.articleId}/permanent`, {
                method: 'DELETE',
                headers: headers
            });
            
            if (response.ok) {
                // 彻底删除成功，跳转到首页
                alert('文章已彻底删除');
                window.location.href = '/';
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || '彻底删除失败');
            }
        } catch (error) {
            this.logError('Failed to permanently delete article', error);
            alert('彻底删除文章失败: ' + error.message);
        }
    }

    static get ICON_STROKE() {
        return '#475569';
    }

    getStatIcons() {
        const s = ArticleHeaderCard.ICON_STROKE;
        const svg = (paths) =>
            `<svg class="stat-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        return {
            views: svg('<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'),
            comments: svg('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'),
            size: svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
        };
    }

    getMetaIcon(type) {
        const s = ArticleHeaderCard.ICON_STROKE;
        const svg = (paths) =>
            `<svg class="meta-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        switch (type) {
            case 'user':
                return svg('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>');
            case 'category':
                return svg('<path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 0 1 0 2.828l-7 7a2 2 0 0 1-2.828 0l-7-7A1.994 1.994 0 0 1 3 12V7a4 4 0 0 1 4-4z"/>');
            case 'created':
                return svg('<path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>');
            case 'updated':
            default:
                return svg('<circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>');
        }
    }

    renderStatItem(iconSvg, label, value) {
        return `
            <div class="stat-item">
                ${iconSvg}
                <span class="stat-label">${label}</span>
                <span class="stat-number">${value}</span>
            </div>
        `;
    }

    renderArticleStats(hits, commentCount, itemsize) {
        const icons = this.getStatIcons();
        return `
            <div class="article-stats">
                ${this.renderStatItem(icons.views, '点击', hits || 0)}
                ${this.renderStatItem(icons.comments, '评论', commentCount || 0)}
                ${this.renderStatItem(icons.size, '长度', this.formatFileSize(itemsize || 0))}
            </div>
        `;
    }

    renderArticleToolbar(showSetSiteIntroButton, showSetIntroButton) {
        return `
            <div class="btn-toolbar">
                ${showSetSiteIntroButton ? `
                    <button type="button" class="btn btn-secondary btn-sm btn-icon-only" id="set-site-intro-btn" title="设为网站介绍" aria-label="设为网站介绍">
                        ${this.getBtnIcon('globe')}
                    </button>
                ` : ''}
                ${showSetIntroButton ? `
                    <button type="button" class="btn btn-secondary btn-sm btn-icon-only" id="set-intro-btn" title="设为个人介绍" aria-label="设为个人介绍">
                        ${this.getBtnIcon('user')}
                    </button>
                ` : ''}
                <button type="button" class="btn btn-primary btn-sm btn-icon-only" id="edit-article-btn" title="修改文章" aria-label="修改文章">
                    ${this.getBtnIcon('edit')}
                </button>
                <button type="button" class="btn btn-danger btn-sm" id="delete-article-btn">
                    ${this.getBtnIcon('delete')}<span>删除文章</span>
                </button>
                ${this.isAdmin ? `
                    <button type="button" class="btn btn-danger btn-sm" id="permanent-delete-article-btn">
                        ${this.getBtnIcon('delete')}<span>彻底删除</span>
                    </button>
                ` : ''}
            </div>
        `;
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderAuthorMetaItem(author, project) {
        const safeAuthor = this.escapeHtml(author?.name || '未知作者');
        const blogId = project?.id;
        const avatarPath = author?.avatar || this.getSmallAvatarPath(author?.id);
        const fallbackLetter = safeAuthor.charAt(0).toUpperCase();

        const avatarHtml = `
            <span class="author-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="author-avatar-fallback" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackLetter}</span>
            </span>
        `;
        const nameHtml = `<span class="author-name">${safeAuthor}</span>`;

        if (blogId) {
            return `
                <div class="meta-item meta-item-author">
                    <a href="/blog/${blogId}" class="author-link" title="查看博客" target="_blank" rel="noopener noreferrer">
                        ${avatarHtml}
                        ${nameHtml}
                    </a>
                </div>
            `;
        }

        return `
            <div class="meta-item meta-item-author">
                ${avatarHtml}
                ${nameHtml}
            </div>
        `;
    }

    renderArticleMeta({ author, project, category, created_at, itemtype, isAdmin, showToolbar, showSetSiteIntroButton, showSetIntroButton }) {
        const safeCategory = category?.name ? this.escapeHtml(category.name) : '';
        const createDate = this.formatDate(created_at);
        const statusText = this.getStatusText(itemtype);
        const showStatus = itemtype !== 0 || isAdmin;

        return `
            <div class="article-meta">
                <div class="meta-items-left">
                    ${this.renderAuthorMetaItem(author, project)}
                    <div class="meta-item">
                        ${this.getMetaIcon('created')}
                        <span>发布于 ${createDate}</span>
                    </div>
                    ${safeCategory ? `
                        <div class="meta-item">
                            ${this.getMetaIcon('category')}
                            <span>${safeCategory}</span>
                        </div>
                    ` : ''}
                    ${showStatus ? `
                        <div class="meta-item">
                            <span class="status-${itemtype}">${statusText}</span>
                        </div>
                    ` : ''}
                </div>
                ${showToolbar ? this.renderArticleToolbar(showSetSiteIntroButton, showSetIntroButton) : ''}
            </div>
        `;
    }

    getBtnIcon(type) {
        if (typeof Icons !== 'undefined') {
            const iconMap = {
                edit: Icons.edit,
                delete: Icons.delete,
                user: Icons.user,
                globe: Icons.globe,
            };
            if (iconMap[type]) {
                return Icons.asBtnIcon(iconMap[type]);
            }
        }
        const wrap = (paths) =>
            `<svg class="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        if (type === 'globe') {
            return wrap('<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>');
        }
        if (type === 'edit') {
            return wrap('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>');
        }
        return wrap('<polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6m3,0V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"/>');
    }

    /**
     * 格式化文件大小显示
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    /**
     * 获取文章状态文本
     */
    getStatusText(itemtype) {
        switch (itemtype) {
            case 0:
                return '未知';
            case 1:
                return '正常';
            case 2:
                return '已删除';
            default:
                return '未知';
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="card article-header-card">
                <div class="card-body">
                    <div class="error-message">${message}</div>
                </div>
            </div>
        `;
        this.addStyles();
    }

    /**
     * 显示成功信息
     */
    showSuccess(message) {
        // 创建临时成功提示
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #10b981;
            color: white;
            padding: 20px 30px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 1001;
            font-size: 16px;
            font-weight: 500;
            text-align: center;
            min-width: 200px;
            max-width: 400px;
        `;
        successDiv.textContent = message;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
    }

    /**
     * 添加样式
     */
    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                @import url('/static/css/common-components.css');
                .card { margin-bottom: 0; }

                .card-body {
                    padding: calc(var(--spacing-3) * 0.6) var(--spacing-4);
                }

                .article-title h1 {
                    font-size: var(--font-size-xl);
                    font-weight: 700;
                    color: var(--gray-900);
                    margin: 0 0 var(--spacing-3);
                    line-height: 1.3;
                }

                .article-stats {
                    display: flex;
                    flex-wrap: wrap;
                    gap: var(--spacing-2);
                    padding-top: var(--spacing-2);
                    border-top: 1px solid var(--gray-100);
                }

                .stat-item {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    padding: var(--spacing-1) var(--spacing-2);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-sm);
                    font-size: var(--font-size-xs);
                    color: var(--gray-600);
                    line-height: 1.3;
                }

                .stat-icon,
                .meta-icon,
                .btn-icon {
                    display: block;
                    width: 18px;
                    height: 18px;
                    flex-shrink: 0;
                }

                .stat-label {
                    font-weight: 500;
                    color: var(--gray-600);
                }

                .stat-number {
                    font-weight: 600;
                    color: var(--gray-900);
                }

                .article-meta {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    justify-content: space-between;
                    gap: var(--spacing-2) var(--spacing-3);
                    margin-bottom: var(--spacing-2);
                }

                .meta-items-left {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: var(--spacing-3);
                    min-width: 0;
                }

                .meta-item {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                    white-space: nowrap;
                }

                .meta-item-author {
                    gap: var(--spacing-2);
                }

                .author-link {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    color: inherit;
                    text-decoration: none;
                    transition: color var(--transition-fast);
                }

                .author-link:hover {
                    color: var(--primary-color);
                }

                .author-link:focus {
                    outline: none;
                }

                .author-link:focus-visible {
                    outline: 2px solid var(--primary-color);
                    outline-offset: 2px;
                    border-radius: var(--radius-sm);
                }

                .author-avatar {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                }

                .author-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                }

                .author-avatar-fallback {
                    width: 100%;
                    height: 100%;
                    align-items: center;
                    justify-content: center;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    color: var(--gray-600);
                }

                .author-name {
                    font-weight: 500;
                    color: var(--gray-700);
                }

                .author-link:hover .author-name {
                    color: var(--primary-color);
                }

                .article-meta .btn-toolbar {
                    margin-top: 0;
                    padding-top: 0;
                    border-top: none;
                    width: auto;
                }

                .btn.btn-sm {
                    min-height: 36px;
                    padding: 0 12px;
                    gap: 6px;
                    font-size: var(--font-size-sm);
                    line-height: 1.25;
                }

                .btn.btn-sm.btn-icon-only {
                    width: 36px;
                    height: 36px;
                    min-width: 36px;
                    min-height: 36px;
                    padding: 0;
                    gap: 0;
                }

                .btn .btn-icon {
                    width: 18px;
                    height: 18px;
                }

                :host([data-layout-single-column]) .article-meta {
                    flex-direction: column;
                    align-items: stretch;
                }

                :host([data-layout-single-column]) .meta-items-left,
                :host([data-layout-single-column]) .article-meta .btn-toolbar {
                    justify-content: flex-start;
                }

                :host([data-layout-single-column]) .article-meta .btn-toolbar {
                    flex-direction: column;
                    align-items: stretch;
                    width: 100%;
                }

                :host([data-layout-single-column]) .article-meta .btn-toolbar .btn {
                    width: 100%;
                    box-sizing: border-box;
                }

                .status-0 {
                    color: var(--gray-500);
                    font-weight: 500;
                }
                
                .status-1 {
                    color: #059669;
                    font-weight: 600;
                }
                
                .status-2 {
                    color: #dc2626;
                    font-weight: 600;
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('article-header-card', ArticleHeaderCard);
