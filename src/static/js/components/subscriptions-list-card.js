/**
 * 订阅博客列表卡片组件
 * 显示当前博客订阅的所有博客列表，支持分页和取消订阅
 */
class SubscriptionsListCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalBlogs = 0;
        this.totalPages = 0;
        this.blogs = [];
        this.loading = true;
        this.isOwner = false;
        this.projectData = null;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.initializeAsync();
    }

    getProjectIdFromUrl() {
        return this.getProjectId();
    }

    async initializeAsync() {
        try {
            // 检查所有权
            await this.checkOwnership();
            
            // 加载订阅博客列表
            this.loadSubscriptions();
        } catch (error) {
            console.error('组件初始化失败:', error);
        }
    }

    async checkOwnership() {
        if (!this.projectId) {
            return;
        }

        try {
            // 获取项目信息
            const projectResponse = await fetch(`/api/projects/${this.projectId}`);
            if (projectResponse.ok) {
                this.projectData = await projectResponse.json();
                
                // 检查当前用户是否为博客所有者
                if (UserManager.isLoggedIn()) {
                    const currentUser = UserManager.getCurrentUser();
                    this.isOwner = currentUser.id === this.projectData.userid;
                }
                
                // 所有权检查完成后重新渲染
                this.render();
            }
        } catch (error) {
            console.error('检查博客所有权失败:', error);
        }
    }

    async loadSubscriptions(page = 1) {
        if (!this.projectId) {
            this.loading = false;
            this.render();
            return;
        }

        try {
            this.currentPage = page;
            this.loading = true;
            this.render();

            const response = await fetch(`/api/subscriptions/blogs/${this.projectId}?page=${page}&limit=${this.pageSize}`);
            if (response.ok) {
                const data = await response.json();
                this.blogs = data.blogs || [];
                this.totalBlogs = data.total || 0;
                this.totalPages = data.total_pages || 0;
            } else if (response.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                this.blogs = [];
                this.totalBlogs = 0;
                this.totalPages = 0;
            }
        } catch (error) {
            console.error('Error loading subscriptions:', error);
            this.blogs = [];
            this.totalBlogs = 0;
            this.totalPages = 0;
        } finally {
            this.loading = false;
            this.render();
        }
    }

    async unsubscribeFromBlog(relationId, projectId, projectName) {
        if (!confirm(`确定要取消订阅博客"${projectName}"吗？`)) {
            return;
        }

        try {
            const response = await fetch(`/api/subscriptions/unsubscribe/${projectId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${UserManager.getAccessToken()}`
                }
            });

            if (response.ok) {
                // 重新加载当前页面的数据
                this.loadSubscriptions(this.currentPage);
                
                // 显示成功消息
                this.showMessage('取消订阅成功', 'success');
            } else {
                const errorData = await response.json();
                this.showMessage(`取消订阅失败: ${errorData.detail || '未知错误'}`, 'error');
            }
        } catch (error) {
            console.error('取消订阅失败:', error);
            this.showMessage('取消订阅失败，请稍后重试', 'error');
        }
    }

    showMessage(message, type = 'info') {
        // 简单的消息提示，可以后续优化为更好的UI组件
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-size: 14px;
            z-index: 1000;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        `;
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            document.body.removeChild(messageDiv);
        }, 3000);
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) return;
        this.loadSubscriptions(page);
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }
                
                /* CSS Variables */
                :root {
                    --primary-color: #3b82f6;
                    --primary-hover: #2563eb;
                    --white: #ffffff;
                    --gray-50: #f9fafb;
                    --gray-100: #f3f4f6;
                    --gray-200: #e5e7eb;
                    --gray-300: #d1d5db;
                    --gray-400: #9ca3af;
                    --gray-500: #6b7280;
                    --gray-600: #4b5563;
                    --gray-700: #374151;
                    --gray-800: #1f2937;
                    --gray-900: #111827;
                    --error-color: #ef4444;
                    --success-color: #10b981;
                    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    --font-size-xs: 0.75rem;
                    --font-size-sm: 0.875rem;
                    --font-size-base: 1rem;
                    --font-size-lg: 1.125rem;
                    --font-size-xl: 1.25rem;
                    --spacing-1: 0.25rem;
                    --spacing-2: 0.5rem;
                    --spacing-3: 0.75rem;
                    --spacing-4: 1rem;
                    --spacing-5: 1.25rem;
                    --spacing-6: 1.5rem;
                    --spacing-8: 2rem;
                    --radius-sm: 0.25rem;
                    --radius-md: 0.375rem;
                    --radius-lg: 0.5rem;
                    --radius-xl: 0.75rem;
                    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    --transition-fast: all 0.15s ease;
                    --transition-normal: all 0.3s ease;
                }
                
                .card {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    margin-bottom: var(--spacing-6);
                }
                
                .card-header {
                    padding: var(--spacing-5);
                    border-bottom: 1px solid var(--gray-200);
                    background: var(--gray-50);
                }
                
                .card-title {
                    font-size: var(--font-size-xl);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }
                
                .card-body {
                    padding: var(--spacing-5);
                }
                
                .blog-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }
                
                .blog-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-4);
                    padding: var(--spacing-4);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-lg);
                    transition: var(--transition-fast);
                    background: var(--white);
                    cursor: pointer;
                }
                
                .blog-item:hover {
                    box-shadow: var(--shadow-md);
                    transform: translateY(-1px);
                    border-color: var(--primary-color);
                }
                
                .blog-avatar {
                    width: 48px;
                    height: 48px;
                    border-radius: var(--radius-full);
                    overflow: hidden;
                    flex-shrink: 0;
                    background: var(--gray-100);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 600;
                    color: var(--gray-600);
                }
                
                .blog-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                
                .blog-content {
                    flex: 1;
                    min-width: 0;
                }
                
                .blog-name {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0 0 var(--spacing-1) 0;
                }
                
                .blog-description {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    margin: 0 0 var(--spacing-2) 0;
                    line-height: 1.4;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }
                
                .blog-meta {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-4);
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }
                
                .blog-actions {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                
                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-2) var(--spacing-4);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    border-radius: var(--radius-md);
                    border: 1px solid transparent;
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                    line-height: 1;
                }
                
                .btn-primary {
                    background-color: var(--primary-color);
                    color: var(--white);
                    border-color: var(--primary-color);
                }
                
                .btn-primary:hover {
                    background-color: var(--primary-hover);
                    border-color: var(--primary-hover);
                }
                
                .btn-danger {
                    background-color: var(--error-color);
                    color: var(--white);
                    border-color: var(--error-color);
                }
                
                .btn-danger:hover {
                    background-color: #dc2626;
                    border-color: #dc2626;
                }
                
                .blog-actions {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                
                .blog-actions .btn {
                    pointer-events: auto;
                }
                
                .btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
                
                .empty-state {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
                
                .pagination {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: var(--spacing-6);
                    padding-top: var(--spacing-4);
                    border-top: 1px solid var(--gray-200);
                }
                
                .pagination-info {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                }
                
                .pagination-controls {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                
                .nav-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    padding: var(--spacing-2) var(--spacing-3);
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    background: var(--white);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                }
                
                .nav-btn:hover:not(:disabled) {
                    background: var(--gray-50);
                    color: var(--primary-color);
                    border-color: var(--primary-color);
                }
                
                .nav-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .page-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <path d="M22 6l-10 7L2 6"/>
                        </svg>
                        订阅的博客
                    </h2>
                </div>
                <div class="card-body">
                    ${this.loading ? this.renderLoading() : this.renderBlogList()}
                    ${!this.loading && this.totalPages > 1 ? this.renderPagination() : ''}
                </div>
            </div>
        `;
    }

    renderLoading() {
        return `
            <div class="loading">
                <div>加载中...</div>
            </div>
        `;
    }

    renderBlogList() {
        if (this.blogs.length === 0) {
            return `
                <div class="empty-state">
                    <p>还没有订阅任何博客</p>
                    <p>去发现一些有趣的博客吧！</p>
                </div>
            `;
        }

        return `
            <div class="blog-list">
                ${this.blogs.map(blog => this.renderBlogItem(blog)).join('')}
            </div>
        `;
    }

    renderBlogItem(blog) {
        const avatar = blog.user_avatar ? 
            `<img src="${blog.user_avatar}" alt="${blog.user_name}" onerror="this.style.display='none'">` :
            `<span>${blog.user_name ? blog.user_name.charAt(0) : '用'}</span>`;
        
        const subscribedAt = blog.subscribed_at ? 
            new Date(blog.subscribed_at).toLocaleDateString('zh-CN') : '未知时间';
        
        const unsubscribeButton = this.isOwner ? 
            `<button class="btn btn-danger" onclick="event.stopPropagation(); this.getRootNode().host.unsubscribeFromBlog(${blog.relation_id}, ${blog.project_id}, '${this.escapeHtml(blog.project_name)}')">
                取消订阅
            </button>` : '';

        return `
            <div class="blog-item" onclick="window.open('/blog/${blog.project_id}', '_blank')" style="cursor: pointer;">
                <div class="blog-avatar">
                    ${avatar}
                </div>
                <div class="blog-content">
                    <div class="blog-name">
                        ${this.escapeHtml(blog.project_name)}
                    </div>
                    <p class="blog-description">${this.escapeHtml(blog.project_description || '暂无描述')}</p>
                    <div class="blog-meta">
                        <span>作者: ${this.escapeHtml(blog.user_name)}</span>
                        <span>订阅时间: ${subscribedAt}</span>
                    </div>
                </div>
                <div class="blog-actions">
                    ${unsubscribeButton}
                </div>
            </div>
        `;
    }

    renderPagination() {
        const prevDisabled = this.currentPage === 1;
        const nextDisabled = this.currentPage === this.totalPages;
        
        return `
            <div class="pagination">
                <div class="pagination-info">
                    共 ${this.totalBlogs} 条记录
                </div>
                <div class="pagination-controls">
                    <button class="nav-btn" onclick="this.getRootNode().host.goToPage(1)" ${prevDisabled ? 'disabled' : ''}>
                        首页
                    </button>
                    <button class="nav-btn" onclick="this.getRootNode().host.goToPage(${this.currentPage - 1})" ${prevDisabled ? 'disabled' : ''}>
                        上一页
                    </button>
                    <div class="page-info">
                        <span>第 ${this.currentPage} 页，共 ${this.totalPages} 页</span>
                    </div>
                    <button class="nav-btn" onclick="this.getRootNode().host.goToPage(${this.currentPage + 1})" ${nextDisabled ? 'disabled' : ''}>
                        下一页
                    </button>
                    <button class="nav-btn" onclick="this.getRootNode().host.goToPage(${this.totalPages})" ${nextDisabled ? 'disabled' : ''}>
                        尾页
                    </button>
                </div>
            </div>
        `;
    }
}

customElements.define('subscriptions-list-card', SubscriptionsListCard);
