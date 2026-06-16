class BlogInfoCard extends BaseComponent {
    constructor() {
        super();
        this.blogData = null;
    }

    async connectedCallback() {
        try {
            this.render();
            
            // 如果在个人资料页面，等待targetUserIdReady事件
            if (window.location.pathname.startsWith('/profile')) {
                if (window.targetUserId) {
                    // 如果已经有targetUserId，直接加载数据
                    await this.loadBlogData();
                } else {
                    // 等待targetUserIdReady事件
                    window.addEventListener('targetUserIdReady', async (event) => {
                        await this.loadBlogData();
                    }, { once: true });
                }
            } else {
                // 不在个人资料页面，直接加载数据
                await this.loadBlogData();
            }
        } catch (error) {
            console.error('BlogInfoCard connectedCallback 错误:', error);
        }
    }

    async loadBlogData() {
        try {
            // 优先使用全局目标用户ID，如果没有则使用当前登录用户
            let userId = window.targetUserId;
            
            if (!userId) {
                // 从UserManager获取当前用户信息
                if (!UserManager.isLoggedIn()) {
                    // 如果没有目标用户ID且未登录，显示错误
                    this.showError('无法获取用户ID');
                    return;
                }

                const currentUser = UserManager.getCurrentUser();
                userId = currentUser.id;
            }

            // 获取用户信息
            const headers = UserManager.createHeaders();
            
            const userResponse = await fetch(`/api/users/${userId}`, { headers });
            if (!userResponse.ok) {
                throw new Error(`获取用户信息失败: ${userResponse.status}`);
            }
            
            const userData = await userResponse.json();
            
            if (userData.projectid) {
                const projectData = await BaseComponent.getProject(userData.projectid);
                if (projectData) {
                    this.blogData = projectData;
                } else {
                    throw new Error('获取博客信息失败');
                }
            } else {
                // 用户没有博客，显示开通博客选项
                this.blogData = null;
                this.userId = userId;
            }
            
            this.render();
        } catch (error) {
            console.error('加载博客数据失败:', error);
            this.showError('加载博客数据失败');
        }
    }

    formatDateTime(dateString) {
        if (!dateString) return '未设置';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getCardStyles() {
        return `
            @import url('/static/css/common-components.css');
            :host { display: block; }
            .card-title {
                display: flex;
                align-items: center;
                gap: var(--spacing-2);
            }
            .title-icon {
                width: 20px;
                height: 20px;
                color: var(--primary-color);
                flex-shrink: 0;
            }
            .title-icon svg {
                width: 100%;
                height: 100%;
                display: block;
            }
            .blog-name {
                margin: 0 0 var(--spacing-2);
                font-size: var(--font-size-base);
                font-weight: 600;
                line-height: 1.3;
            }
            .blog-name a {
                color: var(--primary-color);
                text-decoration: none;
            }
            .blog-name a:hover {
                color: var(--primary-hover);
                text-decoration: underline;
            }
            .blog-description {
                margin: 0 0 var(--spacing-3);
                color: var(--gray-600);
                font-size: var(--font-size-sm);
                line-height: 1.5;
            }
            .blog-stats {
                display: flex;
                flex-wrap: wrap;
                gap: var(--spacing-2);
                margin-bottom: var(--spacing-3);
                padding-bottom: var(--spacing-3);
                border-bottom: 1px solid var(--gray-100);
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
            }
            .stat-icon {
                display: block;
                width: 16px;
                height: 16px;
                flex-shrink: 0;
            }
            .stat-label { font-weight: 500; }
            .stat-number {
                font-weight: 600;
                color: var(--gray-900);
            }
            .meta-items {
                display: flex;
                flex-wrap: wrap;
                gap: var(--spacing-3);
            }
            .meta-item {
                display: inline-flex;
                align-items: center;
                gap: var(--spacing-1);
                color: var(--gray-500);
                font-size: var(--font-size-xs);
            }
            .meta-icon {
                display: block;
                width: 16px;
                height: 16px;
                flex-shrink: 0;
            }
            .empty-state {
                text-align: center;
                padding: var(--spacing-6) var(--spacing-2);
            }
            .empty-icon {
                width: 40px;
                height: 40px;
                margin: 0 auto var(--spacing-3);
                color: var(--gray-400);
            }
            .empty-icon svg {
                width: 100%;
                height: 100%;
                display: block;
            }
            .empty-title {
                margin: 0 0 var(--spacing-2);
                font-size: var(--font-size-base);
                font-weight: 600;
                color: var(--gray-800);
            }
            .empty-description {
                margin: 0 0 var(--spacing-4);
                color: var(--gray-500);
                font-size: var(--font-size-sm);
                line-height: 1.5;
            }
            .loading, .error {
                text-align: center;
                padding: var(--spacing-8);
                color: var(--gray-500);
            }
            .error { color: var(--error-color); }
            .modal-overlay {
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.5);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            .modal-overlay.show { display: flex; }
            .modal-panel {
                background: var(--white);
                padding: var(--spacing-4);
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-xl);
                border: 1px solid var(--gray-200);
                max-width: 500px;
                width: 90%;
            }
            .modal-title {
                font-size: var(--font-size-base);
                font-weight: 600;
                margin: 0 0 var(--spacing-4);
                color: var(--gray-900);
            }
            .modal-form {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-3);
            }
            .form-group {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-1);
            }
            .form-label {
                font-weight: 500;
                color: var(--gray-700);
                font-size: var(--font-size-sm);
            }
            .form-input, .form-textarea {
                padding: var(--spacing-2) var(--spacing-3);
                border: 1px solid var(--gray-300);
                border-radius: var(--radius-md);
                font-size: var(--font-size-sm);
            }
            .form-input:focus, .form-textarea:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px var(--primary-color-10);
            }
            .form-textarea {
                resize: vertical;
                min-height: 96px;
            }
            .error-message {
                color: var(--error-color);
                font-size: var(--font-size-xs);
            }
            .modal-actions {
                display: flex;
                gap: var(--spacing-2);
                justify-content: flex-end;
                margin-top: var(--spacing-2);
            }
            .btn svg {
                width: 16px;
                height: 16px;
                flex-shrink: 0;
            }
        `;
    }

    getStatIcon(type) {
        const stroke = '#475569';
        const svg = (paths) =>
            `<svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        const icons = {
            posts: svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/>'),
            comments: svg('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'),
            views: svg('<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'),
        };
        return icons[type] || '';
    }

    getMetaIcon(calendar) {
        const stroke = '#475569';
        if (calendar) {
            return `<svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg>`;
        }
        return `<svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>`;
    }

    renderStatItem(type, label, value) {
        return `
            <div class="stat-item">
                ${this.getStatIcon(type)}
                <span class="stat-label">${label}</span>
                <span class="stat-number">${value}</span>
            </div>
        `;
    }

    render() {
        if (!this.blogData && !this.userId) {
            this.shadowRoot.innerHTML = `
                <style>${this.getCardStyles()}</style>
                <div class="card"><div class="loading">加载中...</div></div>
            `;
            return;
        }

        if (!this.blogData && this.userId) {
            this.renderCreateBlogOption();
            return;
        }

        const safeBlogName = this.escapeHtml(this.blogData.name || '未设置');
        const safeBlogDesc = this.escapeHtml(this.blogData.comment || '暂无说明');

        this.shadowRoot.innerHTML = `
            <style>${this.getCardStyles()}</style>
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="title-icon">${Icons.home}</span>
                        博客信息
                    </h2>
                </div>
                <div class="card-body">
                    <h3 class="blog-name">
                        <a href="/blog/${this.blogData.id}" target="_blank" rel="noopener noreferrer">${safeBlogName}</a>
                    </h3>
                    <p class="blog-description">${safeBlogDesc}</p>
                    <div class="blog-stats">
                        ${this.renderStatItem('posts', '文章', this.blogData.recordcount || 0)}
                        ${this.renderStatItem('comments', '评论', this.blogData.commentcount || 0)}
                        ${this.renderStatItem('views', '访问', this.blogData.accesscount || 0)}
                    </div>
                    <div class="meta-items">
                        <div class="meta-item">
                            ${this.getMetaIcon(true)}
                            <span>创建于 ${this.formatDateTime(this.blogData.createtime)}</span>
                        </div>
                        <div class="meta-item">
                            ${this.getMetaIcon(false)}
                            <span>更新于 ${this.formatDateTime(this.blogData.updatetime)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.shadowRoot.innerHTML = `
            <style>${this.getCardStyles()}</style>
            <div class="card"><div class="error">${this.escapeHtml(message)}</div></div>
        `;
    }

    renderCreateBlogOption() {
        this.shadowRoot.innerHTML = `
            <style>${this.getCardStyles()}</style>
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="title-icon">${Icons.home}</span>
                        博客信息
                    </h2>
                </div>
                <div class="card-body">
                    <div class="empty-state">
                        <div class="empty-icon">${Icons.edit}</div>
                        <h3 class="empty-title">还没有开通博客</h3>
                        <p class="empty-description">开通博客后，您可以发布文章、管理内容，开始您的创作之旅。</p>
                        <button type="button" class="btn btn-primary btn-sm" id="createBlogBtn">
                            ${Icons.add}
                            开通博客
                        </button>
                    </div>
                </div>
            </div>

            <div class="modal-overlay" id="createBlogModal">
                <div class="modal-panel">
                    <h3 class="modal-title">开通博客</h3>
                    <form class="modal-form" id="createBlogForm">
                        <div class="form-group">
                            <label class="form-label" for="blogName">博客名称 *</label>
                            <input type="text" id="blogName" class="form-input" required maxlength="100" placeholder="请输入博客名称">
                            <div class="error-message" id="blogNameError"></div>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="blogDescription">博客描述</label>
                            <textarea id="blogDescription" class="form-textarea" maxlength="500" placeholder="请输入博客描述（可选）"></textarea>
                            <div class="error-message" id="blogDescriptionError"></div>
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary btn-sm btn-icon-only" id="cancelCreateBtn" title="取消" aria-label="取消">${Icons.asBtnIcon(Icons.close)}</button>
                            <button type="submit" class="btn btn-primary btn-sm" id="confirmCreateBtn">创建博客</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        this.addCreateBlogEventListeners();
    }

    addCreateBlogEventListeners() {
        // 开通博客按钮
        const createBlogBtn = this.shadowRoot.querySelector('#createBlogBtn');
        if (createBlogBtn) {
            createBlogBtn.addEventListener('click', () => {
                this.showCreateBlogModal();
            });
        }

        // 取消创建
        const cancelCreateBtn = this.shadowRoot.querySelector('#cancelCreateBtn');
        if (cancelCreateBtn) {
            cancelCreateBtn.addEventListener('click', () => {
                this.hideCreateBlogModal();
            });
        }

        // 确认创建
        const createBlogForm = this.shadowRoot.querySelector('#createBlogForm');
        if (createBlogForm) {
            createBlogForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCreateBlog();
            });
        }

        // 点击模态框外部关闭
        const modal = this.shadowRoot.querySelector('#createBlogModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideCreateBlogModal();
                }
            });
        }
    }

    showCreateBlogModal() {
        const modal = this.shadowRoot.querySelector('#createBlogModal');
        if (modal) {
            modal.classList.add('show');
            // 聚焦到博客名称输入框
            const blogNameInput = this.shadowRoot.querySelector('#blogName');
            if (blogNameInput) {
                blogNameInput.focus();
            }
        }
    }

    hideCreateBlogModal() {
        const modal = this.shadowRoot.querySelector('#createBlogModal');
        if (modal) {
            modal.classList.remove('show');
            // 清空表单
            const form = this.shadowRoot.querySelector('#createBlogForm');
            if (form) {
                form.reset();
            }
            // 清空错误信息
            this.clearCreateBlogErrors();
        }
    }

    clearCreateBlogErrors() {
        const errorElements = this.shadowRoot.querySelectorAll('.error-message');
        errorElements.forEach(el => {
            el.textContent = '';
        });
    }

    async handleCreateBlog() {
        const blogName = this.shadowRoot.querySelector('#blogName').value.trim();
        const blogDescription = this.shadowRoot.querySelector('#blogDescription').value.trim();

        // 验证输入
        if (!blogName) {
            this.showCreateBlogError('blogName', '博客名称不能为空');
            return;
        }

        if (blogName.length > 100) {
            this.showCreateBlogError('blogName', '博客名称不能超过100个字符');
            return;
        }

        if (blogDescription && blogDescription.length > 500) {
            this.showCreateBlogError('blogDescription', '博客描述不能超过500个字符');
            return;
        }

        // 清空错误信息
        this.clearCreateBlogErrors();

        // 获取当前用户信息
        if (!UserManager.isLoggedIn()) {
            this.showCreateBlogError('blogName', '用户信息获取失败，请重新登录');
            return;
        }

        const currentUser = UserManager.getCurrentUser();

        try {
            // 调用创建博客API
            const headers = UserManager.createHeaders({
                'Content-Type': 'application/json'
            });

            const response = await fetch('/api/projects/create', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    name: blogName,
                    comment: blogDescription,
                    userid: currentUser.id
                })
            });

            if (response.ok) {
                const newBlog = await response.json();
                
                // 创建成功，隐藏模态框
                this.hideCreateBlogModal();
                
                // 重新加载博客数据
                this.blogData = newBlog;
                this.userId = null;
                this.render();
                
                // 显示成功消息
                this.showSuccessMessage('博客创建成功！');
            } else {
                const errorData = await response.json();
                this.showCreateBlogError('blogName', errorData.detail || '创建博客失败');
            }
        } catch (error) {
            console.error('创建博客失败:', error);
            this.showCreateBlogError('blogName', '网络错误，请稍后重试');
        }
    }

    showCreateBlogError(fieldName, message) {
        const errorElement = this.shadowRoot.querySelector(`#${fieldName}Error`);
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
            font-size: 14px;
        `;
        successDiv.textContent = message;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
    }
}

customElements.define('blog-info-card', BlogInfoCard);
