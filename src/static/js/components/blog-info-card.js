class BlogInfoCard extends BaseComponent {
    constructor() {
        super();
        this.blogData = null;
    }

    async connectedCallback() {
        try {
            this.render();
            await this.loadBlogData();
        } catch (error) {
            console.error('BlogInfoCard connectedCallback 错误:', error);
        }
    }

    async loadBlogData() {
        try {
            // 从localStorage获取当前用户信息
            const userInfo = localStorage.getItem('user_info');
            
            if (!userInfo) {
                // 在开发环境中使用测试数据
                this.blogData = {
                    id: 162,
                    name: '各路资源',
                    comment: '你不知道的，我这里都有',
                    recordcount: 0,
                    accesscount: 78329,
                    userid: 5503,
                    createtime: '2016-08-19T19:16:09',
                    updatetime: '2016-08-19T19:16:09',
                    commentcount: 0
                };
                this.render();
                return;
            }

            const currentUser = JSON.parse(userInfo);
            const userId = currentUser.id;

            // 获取用户的博客信息
            const response = await fetch(`/api/projects/user/${userId}`);
            
            if (!response.ok) {
                throw new Error(`获取博客信息失败: ${response.status}`);
            }
            
            this.blogData = await response.json();
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
        if (!this.blogData) {
            this.shadowRoot.innerHTML = `
                <div class="loading">加载中...</div>
            `;
            return;
        }

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
                    padding-bottom: var(--spacing-4);
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
                    font-size: var(--font-size-lg);
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
                    color: var(--gray-800);
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
}

customElements.define('blog-info-card', BlogInfoCard);
