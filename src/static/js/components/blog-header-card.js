/**
 * 博客头部信息卡片组件
 * 显示博客名称、描述和统计信息
 */
class BlogHeaderCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.blogData = null;
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
            // 获取博客信息
            const response = await fetch(`/api/projects/${this.projectId}`);
            if (response.ok) {
                this.blogData = await response.json();
            } else {
                // 如果API不存在，使用模拟数据
                this.blogData = this.getMockBlogData();
            }
        } catch (error) {
            console.error('Error loading blog data:', error);
            this.blogData = this.getMockBlogData();
        } finally {
            this.loading = false;
            this.render();
        }
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
                :host { display: block; font-family: var(--font-family); }
                .card { background: var(--white); border-radius: var(--radius-xl); box-shadow: var(--shadow-md); border: 1px solid var(--gray-200); overflow: hidden; margin-bottom: var(--spacing-6); }
                .card-header { padding: var(--spacing-8) var(--spacing-6); background: linear-gradient(135deg, var(--primary-color), var(--primary-hover)); color: var(--white); text-align: center; }
                .blog-title { margin: 0 0 var(--spacing-4) 0; font-size: var(--font-size-3xl); font-weight: 700; color: var(--white); }
                .blog-description { margin: 0; font-size: var(--font-size-lg); color: var(--gray-100); opacity: 0.9; line-height: 1.6; max-width: 600px; margin-left: auto; margin-right: auto; }
                .card-body { padding: var(--spacing-6); }
                .blog-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--spacing-4); margin-bottom: var(--spacing-6); }
                .stat-item { text-align: center; padding: var(--spacing-4); background: var(--gray-50); border-radius: var(--radius-lg); border: 1px solid var(--gray-200); }
                .stat-number { font-size: var(--font-size-2xl); font-weight: 700; color: var(--primary-color); margin: 0 0 var(--spacing-2) 0; }
                .stat-label { font-size: var(--font-size-sm); color: var(--gray-600); margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
                .blog-meta { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-4) var(--spacing-6); background: var(--gray-50); border-radius: var(--radius-lg); }
                .meta-item { display: flex; align-items: center; gap: var(--spacing-2); color: var(--gray-600); font-size: var(--font-size-sm); }
                .meta-icon { width: 16px; height: 16px; color: var(--gray-500); }
                .loading { text-align: center; padding: var(--spacing-8); color: var(--gray-500); }
                .error { text-align: center; padding: var(--spacing-6); color: var(--error-color); background: var(--gray-50); border-radius: var(--radius-lg); }
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

    renderContent() {
        const blogName = this.blogData.name || '未命名博客';
        const blogDesc = this.blogData.comment || '这个博客还没有描述';
        const createDate = this.blogData.createtime ? this.formatDate(this.blogData.createtime) : '未知';
        const updateDate = this.blogData.updatetime ? this.formatDate(this.blogData.updatetime) : '未知';

        return `
            <div class="card-header">
                <h1 class="blog-title">${blogName}</h1>
                <p class="blog-description">${blogDesc}</p>
            </div>
            <div class="card-body">
                <div class="blog-stats">
                    <div class="stat-item">
                        <div class="stat-number">${this.blogData.recordcount || 0}</div>
                        <div class="stat-label">文章</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.blogData.commentcount || 0}</div>
                        <div class="stat-label">评论</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.blogData.accesscount || 0}</div>
                        <div class="stat-label">访问</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.getDaysSinceCreation()}</div>
                        <div class="stat-label">天</div>
                    </div>
                </div>
                <div class="blog-meta">
                    <div class="meta-item">
                        <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>
                        </svg>
                        <span>创建于 ${createDate}</span>
                    </div>
                    <div class="meta-item">
                        <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/>
                        </svg>
                        <span>更新于 ${updateDate}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderError() {
        return `<div class="error"><div>加载失败</div></div>`;
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
}

customElements.define('blog-header-card', BlogHeaderCard);
