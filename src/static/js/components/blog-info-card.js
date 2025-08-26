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
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
                    padding: 24px;
                    margin-bottom: 24px;
                    border: 1px solid #e5e7eb;
                }
                
                .card-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 24px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid #e5e7eb;
                }
                
                .card-title {
                    font-size: 20px;
                    font-weight: 600;
                    color: #111827;
                    margin: 0;
                }
                
                .blog-info {
                    margin-bottom: 24px;
                }
                
                .blog-name {
                    font-size: 18px;
                    font-weight: 600;
                    color: #2563eb;
                    margin-bottom: 12px;
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
                    color: #4b5563;
                    margin-bottom: 16px;
                    line-height: 1.5;
                    word-break: break-word;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 16px;
                    margin-bottom: 24px;
                }
                
                .stat-item {
                    text-align: center;
                    padding: 12px;
                    background: #f9fafb;
                    border-radius: 6px;
                }
                
                .stat-number {
                    font-size: 20px;
                    font-weight: 700;
                    color: #2563eb;
                    display: block;
                }
                
                .stat-label {
                    font-size: 12px;
                    color: #6b7280;
                    margin-top: 4px;
                }
                
                .info-grid {
                    display: grid;
                    gap: 12px;
                }
                
                .info-item {
                    display: flex;
                    align-items: flex-start;
                    gap: 12px;
                }
                
                .info-label {
                    min-width: 100px;
                    font-weight: 500;
                    color: #374151;
                    font-size: 14px;
                }
                
                .info-value {
                    flex: 1;
                    color: #111827;
                    font-size: 14px;
                }
                
                .loading, .error {
                    text-align: center;
                    padding: 32px;
                    color: #6b7280;
                }
                
                .error {
                    color: #dc2626;
                }
            </style>
            
            <div class="card-header">
                <h2 class="card-title">博客信息</h2>
            </div>

            <div class="blog-info">
                <div class="blog-name">
                    <a href="/blog/${this.blogData.id}">${this.escapeHtml(this.blogData.name || '未设置')}</a>
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
