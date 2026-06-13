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
        this.currentPage = this.getCurrentPageFromUrl();
        this.render();
        this.initializeAsync();
        this.addEventListeners();
    }

    getProjectIdFromUrl() {
        return this.getProjectId();
    }

    async initializeAsync() {
        try {
            await Promise.all([
                this.checkOwnership(),
                this.loadSubscriptions(this.currentPage)
            ]);
            this.render();
        } catch (error) {
            console.error('组件初始化失败:', error);
        }
    }

    async checkOwnership() {
        if (!this.projectId) return;
        try {
            const projectData = await BaseComponent.getProject(this.projectId);
            if (projectData) {
                this.projectData = projectData;
                if (UserManager.isLoggedIn()) {
                    const currentUser = UserManager.getCurrentUser();
                    this.isOwner = currentUser.id === projectData.userid;
                } else {
                    this.isOwner = false;
                }
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
        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '取消订阅',
            message: `确定要取消订阅博客「${projectName}」吗？`,
        })) {
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
                @import url('/static/css/common-components.css');

                .subscription-avatar {
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

                .subscription-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .post-item.subscription-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-4);
                    cursor: pointer;
                }

                .subscription-content {
                    flex: 1;
                    min-width: 0;
                }

                .subscription-actions {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    flex-shrink: 0;
                }

                .subscription-actions .btn {
                    pointer-events: auto;
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

                .pagination-toolbar {
                    margin-top: var(--spacing-4);
                    padding-top: var(--spacing-4);
                    border-top: 1px solid var(--gray-200);
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
            <div class="post-list">
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
            `<button class="btn btn-danger btn-icon-only" title="取消订阅" aria-label="取消订阅" onclick="event.stopPropagation(); this.getRootNode().host.unsubscribeFromBlog(${blog.relation_id}, ${blog.project_id}, '${this.escapeHtml(blog.project_name)}')">
                ${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.unsubscribe) : '取消订阅'}
            </button>` : '';

        return `
            <div class="post-item subscription-item clickable" onclick="window.open('/blog/${blog.project_id}', '_blank')">
                <div class="subscription-avatar">
                    ${avatar}
                </div>
                <div class="subscription-content post-content">
                    <h4 class="post-title">${this.escapeHtml(blog.project_name)}</h4>
                    <p class="post-excerpt">${this.escapeHtml(blog.project_description || '暂无描述')}</p>
                    <div class="article-meta">
                        <div class="meta-items-left">
                            <div class="meta-item">
                                <span>作者: ${this.escapeHtml(blog.user_name)}</span>
                            </div>
                            <div class="meta-item">
                                <span>订阅时间: ${subscribedAt}</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="subscription-actions">
                    ${unsubscribeButton}
                </div>
            </div>
        `;
    }

    renderPagination() {
        if (this.totalPages <= 1) {
            return '';
        }
        
        const pagination = {
            current_page: this.currentPage,
            total_pages: this.totalPages,
            total: this.totalBlogs,
            has_prev: this.currentPage > 1,
            has_next: this.currentPage < this.totalPages
        };
        
        return `<div class="pagination-toolbar"><navigation-card mode="pagination" pagination='${JSON.stringify(pagination)}'></navigation-card></div>`;
    }

    addEventListeners() {
        // 监听document上的分页事件
        document.addEventListener('page-change', (event) => {
            this.goToPage(event.detail.page);
        });
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        
        this.currentPage = page;
        this.loadSubscriptions(page);
    }
}

customElements.define('subscriptions-list-card', SubscriptionsListCard);
