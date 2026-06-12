/**
 * 博客头部信息卡片组件
 * 显示博客名称、描述和统计信息
 */
class BlogHeaderCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.blogData = null;
        this.userData = null;
        this.loading = true;
        this.subscriptionStatus = null;
        this.isCurrentUserBlog = false;
    }

    connectedCallback() {
        this._attachLayoutSingleColumnObserver();
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadData();
    }

    disconnectedCallback() {
        this._detachLayoutSingleColumnObserver();
    }

    getProjectIdFromUrl() {
        // 使用基类的统一方法
        return this.getProjectId();
    }

    async loadData() {
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            const blogData = await BaseComponent.getProject(this.projectId);
            if (blogData === null) {
                window.location.href = '/static/error.html';
                return;
            }
            this.blogData = blogData;

            const userPromise = blogData.userid
                ? BaseComponent.getUser(blogData.userid)
                : Promise.resolve(null);
            await Promise.all([
                userPromise.then((userData) => { this.userData = userData; }),
                this.loadSubscriptionStatus(),
            ]);

            this.checkIfCurrentUserBlog();
            
        } catch (error) {
            console.error('Error loading blog data:', error);
            this.blogData = this.getMockBlogData();
        } finally {
            this.loading = false;
            this.render();
            // 动态更新页面title
            this.updatePageTitle();
        }
    }

    /**
     * 加载博客头部信息
     */
    async loadBlogHeader() {
        try {
            this.loading = true;
            this.render();
            const blogData = await BaseComponent.getProject(this.projectId);
            if (blogData === null) throw new Error('Project not found');
            this.blogData = blogData;
            
            // 更新页面标题
            this.updatePageTitle();
            
        } catch (error) {
            console.error('Error loading blog header data:', error);
            this.showError('加载博客信息失败');
        } finally {
            this.loading = false;
            this.render();
        }
    }


    /**
     * 检查是否为当前用户的博客
     */
    checkIfCurrentUserBlog() {
        if (!this.blogData || !UserManager.isLoggedIn()) {
            this.isCurrentUserBlog = false;
            return;
        }
        
        const currentUser = UserManager.getCurrentUser();
        this.isCurrentUserBlog = currentUser.id === this.blogData.userid;
    }

    /**
     * 检查是否为管理员
     */
    isAdmin() {
        if (!UserManager.isLoggedIn()) {
            return false;
        }
        
        const currentUser = UserManager.getCurrentUser();
        return currentUser.role === 'admin' || currentUser.role === 'administrator';
    }

    /**
     * 检查是否可以编辑博客信息
     */
    canEditBlog() {
        return this.isCurrentUserBlog || this.isAdmin();
    }

    getMockBlogData() {
        return {
            id: this.projectId,
            name: '我的技术博客',
            comment: '分享技术心得、学习笔记和生活感悟的地方。记录成长，分享快乐。',
            recordcount: 25,
            commentcount: 18,
            accesscount: 1250,
            createtime: '2023-06-15T00:00:00Z',
            updatetime: '2024-01-15T10:30:00Z'
        };
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');
                :host {
                    --spacing-2: 0.5rem;
                    --spacing-3: 0.75rem;
                    --font-size-xs: 0.75rem;
                    --gray-50: #f8fafc;
                    --gray-100: #f1f5f9;
                    --gray-200: #e2e8f0;
                    --gray-500: #64748b;
                    --gray-600: #475569;
                    --gray-900: #0f172a;
                }
                .card { margin-bottom: 0; }
                .card-header {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3) var(--spacing-4);
                    background: var(--gray-50);
                    border-bottom: 1px solid var(--gray-200);
                    text-align: left;
                }
                .header-avatar {
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                }
                .header-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                }
                .header-text {
                    min-width: 0;
                    flex: 1;
                }
                .card-body { padding: var(--spacing-3) var(--spacing-4); }
                .blog-title {
                    margin: 0 0 var(--spacing-1);
                    font-size: var(--font-size-xl);
                    font-weight: 700;
                    color: var(--gray-900);
                    line-height: 1.3;
                }
                .blog-description {
                    margin: 0;
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    line-height: 1.5;
                }
                .blog-stats {
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
                .blog-meta {
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
                .btn.btn-sm {
                    padding: calc(var(--spacing-2) * 1.2) calc(var(--spacing-3) * 1.2);
                    gap: calc(var(--spacing-2) * 1.2);
                    font-size: calc(var(--font-size-xs) * 1.2);
                    line-height: 1.25;
                }
                .btn .btn-icon {
                    width: 16px;
                    height: 16px;
                }
                :host([data-layout-single-column]) .blog-meta {
                    flex-direction: column;
                    align-items: stretch;
                }
                :host([data-layout-single-column]) .meta-items-left,
                :host([data-layout-single-column]) .btn-toolbar {
                    justify-content: flex-start;
                }
                .subscription-section {
                    margin-top: var(--spacing-3);
                    text-align: center;
                }
            </style>

            <div class="card">
                ${this.loading ? this.renderLoading() : 
                  this.blogData ? this.renderContent() : 
                  this.renderError()}
            </div>
        `;
    }

    renderLoading() {
        return `<div class="loading"><div>加载中...</div></div>`;
    }

    static get ICON_STROKE() {
        return '#475569';
    }

    getStatIcons() {
        const s = BlogHeaderCard.ICON_STROKE;
        const svg = (paths) =>
            `<svg class="stat-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        return {
            posts: svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'),
            comments: svg('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'),
            views: svg('<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'),
            history: svg('<circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>'),
        };
    }

    getMetaIcon(calendar) {
        const s = BlogHeaderCard.ICON_STROKE;
        if (calendar) {
            return `<svg class="meta-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg>`;
        }
        return `<svg class="meta-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>`;
    }

    getBtnIcon(type) {
        const s = 'currentColor';
        const wrap = (paths) =>
            `<svg class="btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        if (type === 'edit') {
            if (typeof Icons !== 'undefined') {
                return Icons.edit.replace('<svg ', '<svg class="btn-icon" width="16" height="16" aria-hidden="true" ');
            }
            return wrap('<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>');
        }
        if (typeof Icons !== 'undefined') {
            return Icons.subscription.replace('<svg ', '<svg class="btn-icon" width="16" height="16" aria-hidden="true" ');
        }
        return wrap('<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>');
    }

    getAvatarPath(userId) {
        if (!userId) return null;
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/${userId}.jpg`;
    }

    renderHeaderAvatar() {
        const userId = this.userData?.id || this.blogData?.userid;
        const displayName = this.userData?.name || this.blogData?.name || '?';
        const safeFallback = this.escapeHtml(displayName.charAt(0).toUpperCase());
        const avatarPath = this.getAvatarPath(userId);

        return `
            <div class="header-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';"
                         style="display: block;">
                ` : ''}
                <span style="display: ${avatarPath ? 'none' : 'flex'}; width: 100%; height: 100%; align-items: center; justify-content: center;">${safeFallback}</span>
            </div>
        `;
    }

    renderStatItem(iconSvg, label, value, suffix = '') {
        return `
            <div class="stat-item">
                ${iconSvg}
                <span class="stat-label">${label}</span>
                <span class="stat-number">${value}</span>
                ${suffix ? `<span class="stat-label">${suffix}</span>` : ''}
            </div>
        `;
    }

    renderContent() {
        // 安全处理所有文本字段，防止HTML注入和XSS攻击
        const safeBlogName = this.escapeHtml(this.blogData.name || '未命名博客');
        const safeBlogDesc = this.escapeHtml(this.blogData.comment || '这个博客还没有描述');
        const createDate = this.blogData.createtime ? this.formatDate(this.blogData.createtime) : '未知';
        const updateDate = this.blogData.updatetime ? this.formatDate(this.blogData.updatetime) : '未知';
        const icons = this.getStatIcons();

        return `
            <div class="card-header">
                ${this.renderHeaderAvatar()}
                <div class="header-text">
                    <h1 class="blog-title">${safeBlogName}</h1>
                    <p class="blog-description">${safeBlogDesc}</p>
                </div>
            </div>
            <div class="card-body">
                <div class="blog-meta">
                    <div class="meta-items-left">
                        <div class="meta-item">
                            ${this.getMetaIcon(true)}
                            <span>创建于 ${createDate}</span>
                        </div>
                        <div class="meta-item">
                            ${this.getMetaIcon(false)}
                            <span>更新于 ${updateDate}</span>
                        </div>
                    </div>
                    <div class="btn-toolbar">
                        ${this.renderEditButton()}
                        ${this.renderSubscriptionButton()}
                    </div>
                </div>
                <div class="blog-stats">
                    ${this.renderStatItem(icons.posts, '文章', this.blogData.recordcount || 0)}
                    ${this.renderStatItem(icons.comments, '评论', this.blogData.commentcount || 0)}
                    ${this.renderStatItem(icons.views, '访问', this.blogData.accesscount || 0)}
                    ${this.renderStatItem(icons.history, '历史', this.getDaysSinceCreation(), '天')}
                </div>
            </div>
        `;
    }

    renderError() {
        return `<div class="error"><div>加载失败</div></div>`;
    }

    /**
     * 渲染编辑博客信息按钮
     */
    renderEditButton() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            return '';
        }

        // 如果未登录，不显示编辑按钮
        if (!UserManager.isLoggedIn()) {
            return '';
        }

        // 如果不可以编辑博客，不显示编辑按钮
        if (!this.canEditBlog()) {
            return '';
        }

        return `<button type="button" class="btn btn-secondary btn-sm" onclick="this.getRootNode().host.showEditModal()">${this.getBtnIcon('edit')}<span>修改博客信息</span></button>`;
    }

    /**
     * 渲染订阅按钮（内联版本）
     */
    renderSubscriptionButton() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            console.error('UserManager not available in renderSubscriptionButton');
            return '';
        }

        // 如果未登录，不显示订阅按钮
        if (!UserManager.isLoggedIn()) {
            return '';
        }

        // 如果是当前用户的博客，不显示订阅按钮
        if (this.isCurrentUserBlog) {
            return '';
        }

        // 如果订阅状态未加载，显示加载中
        if (this.subscriptionStatus === null) {
            return `<button type="button" class="btn btn-sm" disabled>加载中...</button>`;
        }

        const isSubscribed = this.subscriptionStatus.is_subscribed;
        const buttonText = isSubscribed ? '取消订阅' : '订阅';
        const buttonClass = isSubscribed ? 'btn btn-danger btn-sm' : 'btn btn-primary btn-sm';
        return `<button type="button" class="${buttonClass}" onclick="this.getRootNode().host.handleSubscription()">${this.getBtnIcon('subscription')}<span>${buttonText}</span></button>`;
    }

    /**
     * 渲染订阅区域（保留原方法以兼容）
     */
    renderSubscriptionSection() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            console.error('UserManager not available in renderSubscriptionSection');
            return '';
        }

        // 如果未登录，不显示订阅区域
        if (!UserManager.isLoggedIn()) {
            return '';
        }

        // 如果是当前用户的博客，不显示订阅区域
        if (this.isCurrentUserBlog) {
            return '';
        }

        // 如果订阅状态未加载，显示加载中
        if (this.subscriptionStatus === null) {
            return `
                <div class="subscription-section">
                    <button type="button" class="btn btn-sm" disabled>加载中...</button>
                </div>
            `;
        }

        const isSubscribed = this.subscriptionStatus.is_subscribed;
        const buttonText = isSubscribed ? '取消订阅' : '订阅';
        const buttonClass = isSubscribed ? 'btn btn-danger' : 'btn btn-primary';
        return `
            <div class="subscription-section">
                <button type="button" class="${buttonClass}" onclick="this.getRootNode().host.handleSubscription()">
                    ${this.getBtnIcon('subscription')}<span>${buttonText}</span>
                </button>
            </div>
        `;
    }

    getDaysSinceCreation() {
        if (!this.blogData.createtime) return 0;
        const createDate = new Date(this.blogData.createtime);
        const now = new Date();
        const diffTime = Math.abs(now - createDate);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }

    updatePageTitle() {
        if (this.blogData && this.blogData.name) {
            const blogName = this.blogData.name;
            document.title = `${blogName} - BlogN`;
        }
    }

    /**
     * 加载订阅状态
     */
    async loadSubscriptionStatus() {
        try {
            // 检查UserManager是否可用
            if (typeof UserManager === 'undefined') {
                console.error('UserManager not available');
                this.subscriptionStatus = null;
                return;
            }

            // 检查用户是否登录
            if (!UserManager.isLoggedIn()) {
                this.subscriptionStatus = null;
                return;
            }

            // 检查是否是当前用户的博客
            const currentUser = UserManager.getCurrentUser();
            if (currentUser && currentUser.projectid == this.projectId) {
                this.isCurrentUserBlog = true;
                this.subscriptionStatus = null;
                return;
            }

            // 获取订阅状态
            const headers = UserManager.createHeaders();
            const response = await fetch(`/api/subscriptions/status/${this.projectId}`, { headers });
            
            if (response.ok) {
                this.subscriptionStatus = await response.json();
            } else {
                console.error('Failed to load subscription status:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error response:', errorText);
                this.subscriptionStatus = null;
            }
        } catch (error) {
            console.error('Error loading subscription status:', error);
            this.subscriptionStatus = null;
        }
    }

    /**
     * 处理订阅操作
     */
    /**
     * 显示编辑博客信息模态框
     */
    showEditModal() {
        if (!this.canEditBlog()) {
            alert('您没有权限编辑此博客');
            return;
        }

        // 设置全局引用，以便模态框中的按钮可以访问组件实例
        window.blogHeaderComponent = this;

        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'edit-blog-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove(); window.blogHeaderComponent = null;">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>修改博客信息</h3>
                        <button class="modal-close" onclick="this.closest('.edit-blog-modal').remove(); window.blogHeaderComponent = null;">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="edit-blog-form">
                            <div class="form-group">
                                <label for="blog-name">博客名称</label>
                                <input type="text" id="blog-name" name="name" value="${this.escapeHtml(this.blogData.name || '')}" required>
                            </div>
                            <div class="form-group">
                                <label for="blog-description">博客描述</label>
                                <textarea id="blog-description" name="comment" rows="4" required>${this.escapeHtml(this.blogData.comment || '')}</textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.edit-blog-modal').remove(); window.blogHeaderComponent = null;">取消</button>
                        <button type="button" class="btn btn-primary" onclick="window.blogHeaderComponent.saveBlogInfo()">保存</button>
                    </div>
                </div>
            </div>
            <style>
                .edit-blog-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 1000;
                }
                .modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .modal-content {
                    background: white;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 500px;
                    max-height: 90vh;
                    overflow-y: auto;
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid #e5e7eb;
                }
                .modal-header h3 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                }
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #6b7280;
                }
                .modal-body {
                    padding: 20px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 500;
                    color: #374151;
                }
                .form-group input,
                .form-group textarea {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    font-size: 14px;
                    box-sizing: border-box;
                }
                .form-group textarea {
                    resize: vertical;
                    min-height: 80px;
                }
                .modal-footer {
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                    padding: 16px 20px;
                    border-top: 1px solid #e5e7eb;
                }
                .modal-footer .btn {
                    padding: 8px 16px;
                    font-size: 14px;
                    border-radius: 6px;
                    border: 1px solid #d1d5db;
                    background: #fff;
                    color: #374151;
                    cursor: pointer;
                }
                .modal-footer .btn-primary {
                    background: var(--primary-color);
                    border-color: var(--primary-color);
                    color: #fff;
                }
                .modal-footer .btn-secondary:hover {
                    background: #f9fafb;
                }
                .modal-footer .btn-primary:hover {
                    background: var(--primary-hover);
                    border-color: var(--primary-hover);
                }
            </style>
        `;

        document.body.appendChild(modal);
    }

    /**
     * 保存博客信息
     */
    async saveBlogInfo() {
        const form = document.getElementById('edit-blog-form');
        if (!form) return;

        const formData = new FormData(form);
        const blogData = {
            name: formData.get('name'),
            comment: formData.get('comment')
        };

        try {
            const response = await fetch(`/api/projects/${this.projectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${UserManager.getAccessToken()}`
                },
                body: JSON.stringify(blogData)
            });

            if (response.ok) {
                // 更新本地数据
                this.blogData.name = blogData.name;
                this.blogData.comment = blogData.comment;
                
                // 重新渲染
                this.render();
                
                // 关闭模态框
                const modal = document.querySelector('.edit-blog-modal');
                if (modal) {
                    modal.remove();
                }
                
                // 清理全局引用
                window.blogHeaderComponent = null;
                
                alert('博客信息更新成功');
            } else {
                const error = await response.json();
                alert(error.detail || '更新失败');
            }
        } catch (error) {
            console.error('Save blog info error:', error);
            alert('保存失败，请重试');
        }
    }

    async handleSubscription() {
        if (!UserManager.isLoggedIn()) {
            alert('请先登录');
            return;
        }

        if (this.isCurrentUserBlog) {
            alert('不能订阅自己的博客');
            return;
        }

        try {
            const headers = UserManager.createHeaders();
            let response;
            
            if (this.subscriptionStatus && this.subscriptionStatus.is_subscribed) {
                // 取消订阅
                response = await fetch(`/api/subscriptions/unsubscribe/${this.projectId}`, {
                    method: 'DELETE',
                    headers
                });
            } else {
                // 订阅
                response = await fetch(`/api/subscriptions/subscribe/${this.projectId}`, {
                    method: 'POST',
                    headers
                });
            }

            if (response.ok) {
                const result = await response.json();
                
                // 重新加载订阅状态
                await this.loadSubscriptionStatus();
                this.render();
            } else {
                const error = await response.json();
                alert(error.detail || '操作失败');
            }
        } catch (error) {
            console.error('Subscription error:', error);
            alert('操作失败，请重试');
        }
    }
}

customElements.define('blog-header-card', BlogHeaderCard);
