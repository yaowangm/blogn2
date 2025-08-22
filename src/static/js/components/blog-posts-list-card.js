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
        this.currentFolderId = null;
        this.currentCategoryName = '全部文章';
        this.loadPageSizeConfig();
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.currentFolderId = this.getCurrentFolderId();
        this.render();
        this.loadData();
        this.addEventListeners();
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    getCurrentFolderId() {
        const url = new URL(window.location);
        return url.searchParams.get('folderid');
    }

    addEventListeners() {
        // 监听分类变化事件
        this.addEventListener('categoryChanged', (event) => {
            const { folderId, folderName } = event.detail;
            this.currentFolderId = folderId || null;
            this.currentCategoryName = folderName || '全部文章';
            this.currentPage = 1; // 重置页码
            this.loadData();
        });
    }

    async loadData() {
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            let apiUrl = `/api/projects/${this.projectId}/posts?page=${this.currentPage}&limit=${this.pageSize}&type=${this.activeTab}`;
            
            // 添加folderid参数
            if (this.currentFolderId) {
                apiUrl += `&folderid=${this.currentFolderId}`;
            }
            
            const response = await fetch(apiUrl);
            if (response.ok) {
                const data = await response.json();
                this.posts = data.posts || [];
                this.totalPosts = data.total || 0;
                this.currentCategoryName = data.category || '全部文章';
            } else if (response.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
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
        // 更新URL参数
        const url = new URL(window.location);
        url.searchParams.set('page', page);
        if (this.currentFolderId) {
            url.searchParams.set('folderid', this.currentFolderId);
        }
        window.history.pushState({}, '', url);
        this.loadData();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host { display: block; font-family: var(--font-family); }
                .card { background: var(--white); border-radius: var(--radius-xl); box-shadow: var(--shadow-md); border: 1px solid var(--gray-200); overflow: hidden; margin-bottom: var(--spacing-6); }
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
                
                /* 博文列表容器样式 */
                .blog-list-container {
                    padding: 0;
                }
            </style>

            <div class="card">
                <div class="tabs">
                    <button class="tab ${this.activeTab === 'original' ? 'active' : ''}" onclick="this.getRootNode().host.switchTab('original')">原创文章</button>
                    <button class="tab ${this.activeTab === 'subscription' ? 'active' : ''}" onclick="this.getRootNode().host.switchTab('subscription')">订阅文章</button>
                </div>
                ${this.loading ? this.renderLoading() : 
                  this.activeTab === 'original' ? this.renderOriginalPosts() :
                  this.renderSubscriptionPosts()}
            </div>
        `;
    }

    renderLoading() {
        return `<div class="loading"><div>加载中...</div></div>`;
    }

    renderOriginalPosts() {
        // 复用 blog-list-card 组件显示原创文章
        return `
            <div class="blog-list-container">
                <blog-list-card show-category></blog-list-card>
            </div>
        `;
    }

    renderSubscriptionPosts() {
        // 复用 blog-list-card 组件显示订阅文章
        return `
            <div class="blog-list-container">
                <blog-list-card id="subscription-posts-card"></blog-list-card>
            </div>
        `;
    }

    loadPageSizeConfig() {
        fetch('/api/config/app')
            .then(response => response.json())
            .then(config => {
                this.pageSize = config.blog_posts_page_size || 10;
                console.log(`📋 应用配置已加载: 博客文章每页显示数量=${this.pageSize}`);
            })
            .catch(error => {
                console.warn('⚠️ 加载应用配置失败，使用默认pagesize=10:', error);
            });
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }
}

customElements.define('blog-posts-list-card', BlogPostsListCard);
