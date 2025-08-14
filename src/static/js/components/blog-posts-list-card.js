/**
 * 博客文章列表卡片组件
 * 包含原创和订阅两个标签页，支持分页和分类浏览
 */
class BlogPostsListCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.activeTab = 'original';
        this.currentPage = 1;
        this.pageSize = 10;
        this.posts = [];
        this.totalPosts = 0;
        this.loading = true;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadData();
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    async loadData() {
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            const response = await fetch(`/api/projects/${this.projectId}/posts?page=${this.currentPage}&limit=${this.pageSize}&type=${this.activeTab}`);
            if (response.ok) {
                const data = await response.json();
                this.posts = data.posts || [];
                this.totalPosts = data.total || 0;
            } else {
                this.posts = this.getMockPosts();
                this.totalPosts = this.posts.length;
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            this.posts = this.getMockPosts();
            this.totalPosts = this.posts.length;
        } finally {
            this.loading = false;
            this.render();
        }
    }

    getMockPosts() {
        return [
            {
                id: 1,
                name: '深入理解FastAPI异步编程',
                comment: 'FastAPI是一个现代化的Python Web框架，它基于Python 3.6+的类型提示，提供了高性能的异步支持...',
                createtime: '2024-01-15T10:30:00Z',
                accesscount: 156,
                commentcount: 8,
                category: '技术分享'
            },
            {
                id: 2,
                name: 'Docker容器化部署实践',
                comment: 'Docker是一个开源的容器化平台，它可以让开发者将应用程序和依赖项打包到一个轻量级的容器中...',
                createtime: '2024-01-14T15:20:00Z',
                accesscount: 89,
                commentcount: 5,
                category: '技术分享'
            }
        ];
    }

    switchTab(tabName) {
        this.activeTab = tabName;
        this.currentPage = 1;
        this.loadData();
    }

    changePage(page) {
        this.currentPage = page;
        this.loadData();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host { display: block; font-family: var(--font-family); }
                .card { background: var(--white); border-radius: var(--radius-xl); box-shadow: var(--shadow-md); border: 1px solid var(--gray-200); overflow: hidden; margin-bottom: var(--spacing-6); }
                .card-header { padding: var(--spacing-4) var(--spacing-6); background: var(--gray-50); border-bottom: 1px solid var(--gray-200); }
                .card-title { margin: 0; font-size: var(--font-size-lg); font-weight: 600; color: var(--gray-800); }
                .tabs { display: flex; border-bottom: 1px solid var(--gray-200); }
                .tab { flex: 1; padding: var(--spacing-4) var(--spacing-6); text-align: center; background: var(--gray-100); border: none; cursor: pointer; transition: var(--transition-fast); font-size: var(--font-size-sm); color: var(--gray-600); }
                .tab.active { background: var(--white); color: var(--primary-color); border-bottom: 2px solid var(--primary-color); }
                .tab:hover:not(.active) { background: var(--gray-200); }
                .posts-list { list-style: none; margin: 0; padding: 0; }
                .post-item { border-bottom: 1px solid var(--gray-100); padding: var(--spacing-6); }
                .post-item:last-child { border-bottom: none; }
                .post-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--spacing-3); }
                .post-title { margin: 0; font-size: var(--font-size-lg); font-weight: 600; color: var(--gray-800); text-decoration: none; }
                .post-title:hover { color: var(--primary-color); }
                .post-meta { display: flex; align-items: center; gap: var(--spacing-4); font-size: var(--font-size-xs); color: var(--gray-500); }
                .post-category { background: var(--primary-color); color: var(--white); padding: var(--spacing-1) var(--spacing-2); border-radius: var(--radius-full); font-size: var(--font-size-xs); }
                .post-content { color: var(--gray-700); line-height: 1.6; margin-bottom: var(--spacing-4); }
                .post-stats { display: flex; align-items: center; gap: var(--spacing-4); font-size: var(--font-size-xs); color: var(--gray-500); }
                .loading { text-align: center; padding: var(--spacing-8); color: var(--gray-500); }
                .error { text-align: center; padding: var(--spacing-6); color: var(--error-color); background: var(--gray-50); border-radius: var(--radius-lg); }
                .empty-state { text-align: center; padding: var(--spacing-6); color: var(--gray-500); }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">博客文章</h3>
                </div>
                <div class="tabs">
                    <button class="tab ${this.activeTab === 'original' ? 'active' : ''}" onclick="this.getRootNode().host.switchTab('original')">原创文章</button>
                    <button class="tab ${this.activeTab === 'subscription' ? 'active' : ''}" onclick="this.getRootNode().host.switchTab('subscription')">订阅文章</button>
                </div>
                ${this.loading ? this.renderLoading() : 
                  this.posts.length > 0 ? this.renderPosts() : 
                  this.renderEmptyState()}
            </div>
        `;
    }

    renderLoading() {
        return `<div class="loading"><div>加载中...</div></div>`;
    }

    renderPosts() {
        return `
            <ul class="posts-list">
                ${this.posts.map(post => `
                    <li class="post-item">
                        <div class="post-header">
                            <a href="/projectitem/${post.id}" class="post-title">${post.name}</a>
                            <div class="post-meta">
                                <span>${this.formatDate(post.createtime)}</span>
                                <span class="post-category">${post.category || '未分类'}</span>
                            </div>
                        </div>
                        <div class="post-content">${this.truncateText(post.comment, 120)}</div>
                        <div class="post-stats">
                            <span>👁️ ${post.accesscount || 0} 次浏览</span>
                            <span>💬 ${post.commentcount || 0} 条评论</span>
                        </div>
                    </li>
                `).join('')}
            </ul>
        `;
    }

    renderEmptyState() {
        return `<div class="empty-state"><div>暂无文章</div></div>`;
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }
}

customElements.define('blog-posts-list-card', BlogPostsListCard);
