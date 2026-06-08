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

    render() {
        if (!this.blogData && !this.userId) {
            this.shadowRoot.innerHTML = `
                <div class="loading">加载中...</div>
            `;
            return;
        }

        if (!this.blogData && this.userId) {
            // 用户没有博客，显示开通博客选项
            this.renderCreateBlogOption();
            return;
        }

        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');
                :host {
                    display: block;
                    background: var(--card-bg);
                    border-radius: var(--card-radius);
                    box-shadow: var(--card-shadow);
                    padding: var(--card-padding);
                    margin-bottom: var(--card-margin);
                    border: 1px solid var(--card-border);
                }
                
                .card-header {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-bottom: var(--card-content-gap);
                    padding-bottom: var(--spacing-3);
                    border-bottom: 1px solid var(--card-header-border);
                }
                
                .card-title {
                    font-size: var(--card-title-size);
                    font-weight: var(--card-title-weight);
                    color: var(--card-title-color);
                    margin: 0;
                }
                
                .blog-info {
                    margin-bottom: var(--card-content-gap);
                }
                
                .blog-name {
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-3);
                    word-break: break-word;
                }
                
                .blog-name a {
                    color: inherit;
                    text-decoration: none;
                }
                
                .blog-name a:hover {
                    text-decoration: underline;
                }
                
                .blog-description {
                    color: var(--gray-500);
                    margin-bottom: var(--spacing-4);
                    line-height: 1.5;
                    word-break: break-word;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: var(--spacing-4);
                    margin-bottom: var(--card-content-gap);
                }
                
                .stat-item {
                    text-align: center;
                    padding: var(--spacing-3);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }
                
                .stat-number {
                    font-size: var(--font-size-xl);
                    font-weight: 700;
                    color: var(--primary-color);
                    display: block;
                }
                
                .stat-label {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    margin-top: var(--spacing-1);
                }
                
                .info-grid {
                    display: grid;
                    gap: var(--spacing-3);
                }
                
                .info-item {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--spacing-3);
                }
                
                .info-label {
                    min-width: 100px;
                    font-weight: 500;
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                }
                
                .info-value {
                    flex: 1;
                    color: var(--gray-900);
                    font-size: var(--font-size-sm);
                }
                
                .loading, .error {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--loading-color);
                }
                
                .error {
                    color: var(--error-color);
                }
            </style>
            
            <div class="card-header">
                <h2 class="card-title">博客信息</h2>
            </div>

            <div class="blog-info">
                <div class="blog-name">
                    <a href="/blog/${this.blogData.id}" target="_blank" rel="noopener noreferrer">${this.escapeHtml(this.blogData.name || '未设置')}</a>
                </div>
                
                <div class="blog-description">
                    ${this.escapeHtml(this.blogData.comment || '暂无说明')}
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">${this.blogData.recordcount || 0}</span>
                    <span class="stat-label">文章数量</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${this.blogData.commentcount || 0}</span>
                    <span class="stat-label">评论数量</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${this.blogData.accesscount || 0}</span>
                    <span class="stat-label">访问数量</span>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">创建时间</span>
                    <span class="info-value">${this.formatDateTime(this.blogData.createtime)}</span>
                </div>

                <div class="info-item">
                    <span class="info-label">最后更新</span>
                    <span class="info-value">${this.formatDateTime(this.blogData.updatetime)}</span>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="error">${this.escapeHtml(message)}</div>
        `;
    }

    renderCreateBlogOption() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    background: var(--card-bg);
                    border-radius: var(--card-radius);
                    box-shadow: var(--card-shadow);
                    padding: var(--card-padding);
                    margin-bottom: var(--card-margin);
                    border: 1px solid var(--card-border);
                }
                
                .card-header {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-bottom: var(--card-content-gap);
                    padding-bottom: var(--spacing-3);
                    border-bottom: 1px solid var(--card-header-border);
                }
                
                .card-title {
                    font-size: var(--card-title-size);
                    font-weight: var(--card-title-weight);
                    color: var(--card-title-color);
                    margin: 0;
                }
                
                .create-blog-content {
                    text-align: center;
                    padding: var(--spacing-8) 0;
                }
                
                .create-blog-icon {
                    font-size: 3rem;
                    margin-bottom: var(--spacing-4);
                    color: var(--gray-400);
                }
                
                .create-blog-title {
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-3);
                }
                
                .create-blog-description {
                    color: var(--gray-500);
                    margin-bottom: var(--spacing-6);
                    line-height: 1.5;
                }
                
                .create-blog-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    padding: var(--spacing-3) var(--spacing-6);
                    font-size: var(--font-size-base);
                    font-weight: 500;
                    background-color: var(--primary-color);
                    color: white;
                    border: none;
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: background-color var(--transition-fast);
                    text-decoration: none;
                }
                
                .create-blog-btn:hover {
                    background-color: var(--primary-hover);
                }
                
                .create-blog-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                
                .create-blog-modal.show {
                    display: flex;
                }
                
                .create-blog-modal-content {
                    background: white;
                    padding: var(--spacing-3) var(--spacing-4);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-xl);
                    max-width: 500px;
                    width: 90%;
                }
                
                .create-blog-modal-title {
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    margin-bottom: var(--spacing-4);
                    color: var(--gray-900);
                }
                
                .create-blog-form {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }
                
                .form-group {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-2);
                }
                
                .form-label {
                    font-weight: 500;
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                }
                
                .form-input, .form-textarea {
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    transition: border-color var(--transition-fast);
                }
                
                .form-input:focus, .form-textarea:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                }
                
                .form-textarea {
                    resize: vertical;
                    min-height: 100px;
                }
                
                .create-blog-actions {
                    display: flex;
                    gap: var(--spacing-3);
                    justify-content: flex-end;
                    margin-top: var(--spacing-4);
                }
                
                .btn-secondary {
                    background-color: var(--gray-100);
                    color: var(--gray-700);
                    border: 1px solid var(--gray-300);
                    padding: var(--spacing-2) var(--spacing-4);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                }
                
                .btn-secondary:hover {
                    background-color: var(--gray-200);
                    border-color: var(--gray-400);
                }
                
                .btn-primary {
                    background-color: var(--primary-color);
                    color: white;
                    border: 1px solid var(--primary-color);
                    padding: var(--spacing-2) var(--spacing-4);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                }
                
                .btn-primary:hover {
                    background-color: var(--primary-hover);
                    border-color: var(--primary-hover);
                }
                
                .error-message {
                    color: var(--error-color);
                    font-size: var(--font-size-sm);
                    margin-top: var(--spacing-1);
                }
            </style>
            
            <div class="card-header">
                <h2 class="card-title">博客信息</h2>
            </div>

            <div class="create-blog-content">
                <div class="create-blog-icon">📝</div>
                <h3 class="create-blog-title">还没有开通博客</h3>
                <p class="create-blog-description">开通博客后，您可以发布文章、管理内容，开始您的创作之旅。</p>
                <button class="create-blog-btn" id="createBlogBtn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 5v14M5 12h14"></path>
                    </svg>
                    开通博客
                </button>
            </div>
            
            <!-- 创建博客模态框 -->
            <div class="create-blog-modal" id="createBlogModal">
                <div class="create-blog-modal-content">
                    <h3 class="create-blog-modal-title">开通博客</h3>
                    <form class="create-blog-form" id="createBlogForm">
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
                        <div class="create-blog-actions">
                            <button type="button" class="btn-secondary" id="cancelCreateBtn">取消</button>
                            <button type="submit" class="btn-primary" id="confirmCreateBtn">创建博客</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // 添加事件监听器
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
