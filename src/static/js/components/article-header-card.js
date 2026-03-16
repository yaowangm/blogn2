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

        const { title, author, project, category, hits, itemsize, created_at, updated_at, comment_count, itemtype } = this.articleData;

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
                    
                    <div class="article-meta">
                        <div class="meta-item">
                            <span class="meta-label">作者:</span>
                            <span class="meta-value">${author?.name || '未知作者'}</span>
                        </div>
                        
                        <div class="meta-item">
                            <span class="meta-label">发布时间:</span>
                            <span class="meta-value">${this.formatDate(created_at)}</span>
                        </div>
                        
                        ${updated_at && updated_at !== created_at ? `
                            <div class="meta-item">
                                <span class="meta-label">更新时间:</span>
                                <span class="meta-value">${this.formatDate(updated_at)}</span>
                            </div>
                        ` : ''}
                        
                        ${category?.name ? `
                            <div class="meta-item">
                                <span class="meta-label">分类:</span>
                                <span class="meta-value">${category.name}</span>
                            </div>
                        ` : ''}
                        
                        <div class="meta-item">
                            <span class="meta-label">点击数:</span>
                            <span class="meta-value">${hits || 0}</span>
                        </div>
                        
                        <div class="meta-item">
                            <span class="meta-label">文章长度:</span>
                            <span class="meta-value">${this.formatFileSize(itemsize || 0)}</span>
                        </div>
                        
                        <div class="meta-item">
                            <span class="meta-label">评论数:</span>
                            <span class="meta-value">${comment_count || 0}</span>
                        </div>
                        
                        <div class="meta-item">
                            <span class="meta-label">文章状态:</span>
                            <span class="meta-value status-${itemtype}">${this.getStatusText(itemtype)}</span>
                        </div>
                    </div>
                    
                    ${showToolbar ? `
                        <div class="article-toolbar">
                            ${showSetSiteIntroButton ? `
                                <button class="btn btn-info btn-sm" id="set-site-intro-btn">
                                    <i class="icon-globe"></i>
                                    设为网站介绍
                                </button>
                            ` : ''}
                            ${showSetIntroButton ? `
                                <button class="btn btn-success btn-sm" id="set-intro-btn">
                                    <i class="icon-user"></i>
                                    设为个人介绍
                                </button>
                            ` : ''}
                            <button class="btn btn-primary btn-sm" id="edit-article-btn">
                                <i class="icon-edit"></i>
                                修改文章
                            </button>
                            <button class="btn btn-danger btn-sm" id="delete-article-btn">
                                <i class="icon-trash"></i>
                                删除文章
                            </button>
                            ${this.isAdmin ? `
                                <button class="btn btn-warning btn-sm" id="permanent-delete-article-btn">
                                    <i class="icon-delete"></i>
                                    彻底删除
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
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

        if (!confirm('确定要将此文章设为网站介绍吗？')) {
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
        
        // 确认操作
        if (!confirm('确定要将此文章设为个人介绍吗？\n\n此操作将：\n1. 将此文章设为您的个人介绍\n2. 将文章的附件图片复制为您的头像图片\n3. 如果已有头像，将被新图片覆盖')) {
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
        
        // 确认删除
        if (!confirm('确定要删除这篇文章吗？此操作不可撤销。')) {
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
        
        // 确认彻底删除
        if (!confirm('确定要彻底删除这篇文章吗？\n\n此操作将：\n1. 永久删除文章的所有图片文件\n2. 从数据库中完全删除文章记录\n3. 更新相关统计信息\n\n此操作不可撤销！')) {
            return;
        }
        
        // 二次确认
        if (!confirm('最后确认：您真的要彻底删除这篇文章吗？\n\n一旦执行，文章及其所有相关数据将永久消失！')) {
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
                
                .article-title h1 {
                    font-size: var(--font-size-3xl);
                    font-weight: 700;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-6);
                    line-height: 1.2;
                }
                
                .article-meta {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: var(--spacing-4);
                    padding: var(--spacing-4);
                    background-color: var(--gray-50);
                    border-radius: var(--radius-lg);
                    border: 1px solid var(--gray-200);
                }
                
                .meta-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                
                .meta-label {
                    font-weight: 600;
                    color: var(--gray-600);
                    min-width: 80px;
                }
                
                .meta-value {
                    color: var(--gray-800);
                }
                
                .article-toolbar {
                    margin-top: 24px;
                    padding-top: 16px;
                    border-top: 1px solid #e5e7eb;
                    display: flex !important;
                    gap: 12px;
                    justify-content: flex-end;
                    width: 100%;
                }
                
                .article-toolbar .btn {
                    display: inline-flex !important;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                    margin-left: 8px;
                }
                
                .article-toolbar .btn-primary {
                    background-color: #2563eb !important;
                    color: white !important;
                }
                
                .article-toolbar .btn-primary:hover {
                    background-color: #1d4ed8 !important;
                }
                
                .article-toolbar .btn-danger {
                    background-color: #dc2626 !important;
                    color: white !important;
                }
                
                .article-toolbar .btn-danger:hover {
                    background-color: #b91c1c !important;
                }
                
                .article-toolbar .btn-warning {
                    background-color: #f59e0b !important;
                    color: white !important;
                }
                
                .article-toolbar .btn-warning:hover {
                    background-color: #d97706 !important;
                }
                
                .article-toolbar .btn-success {
                    background-color: #059669 !important;
                    color: white !important;
                }
                
                .article-toolbar .btn-success:hover {
                    background-color: #047857 !important;
                }
                
                .article-toolbar .btn i {
                    font-size: 14px;
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
