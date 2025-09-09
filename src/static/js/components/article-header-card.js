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
            // 从localStorage获取当前用户信息
            const userInfo = localStorage.getItem('user_info');
            const token = localStorage.getItem('access_token');
            
            if (!userInfo || !token) {
                // 用户未登录
                this.currentUser = null;
                this.isAdmin = false;
                this.isAuthor = false;
                return;
            }

            this.currentUser = JSON.parse(userInfo);
            
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
            // 获取认证token
            const token = localStorage.getItem('access_token');
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(`/api/articles/${this.articleId}`, {
                headers: headers
            });
            if (response.ok) {
                this.articleData = await response.json();
                
                // 检查是否为文章作者
                if (this.currentUser && this.articleData.author) {
                    this.isAuthor = this.currentUser.id === this.articleData.author.id;
                }
            } else if (response.status === 404) {
                // 文章不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.logError('Failed to load article data', error);
            // 加载失败，跳转到错误页面
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

        const { title, author, project, category, hits, itemsize, created_at, updated_at, comment_count } = this.articleData;

        // 检查是否显示工具栏
        const showToolbar = this.isAdmin || this.isAuthor;
        
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
                    </div>
                    
                    ${showToolbar ? `
                        <div class="article-toolbar">
                            <button class="btn btn-primary btn-sm" id="edit-article-btn">
                                <i class="icon-edit"></i>
                                修改文章
                            </button>
                            <button class="btn btn-danger btn-sm" id="delete-article-btn">
                                <i class="icon-trash"></i>
                                删除文章
                            </button>
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
        const editBtn = this.shadowRoot.getElementById('edit-article-btn');
        const deleteBtn = this.shadowRoot.getElementById('delete-article-btn');
        
        if (editBtn) {
            editBtn.addEventListener('click', () => this.handleEditArticle());
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.handleDeleteArticle());
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
            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/articles/${this.articleId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
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
     * 添加样式
     */
    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                @import url('/static/css/common-components.css');
                
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
                
                .article-toolbar .btn i {
                    font-size: 14px;
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('article-header-card', ArticleHeaderCard);
