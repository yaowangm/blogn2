/**
 * 最近更新卡片组件
 * 显示最近更新的内容列表
 */
class RecentUpdatesCard extends BaseComponent {
    constructor() {
        super();
        this.recentUpdates = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        this.loadData();
    }

    async loadData() {
        // 检测是否在博客页面
        const isBlogPage = this.isBlogPage();
        let apiUrl;
        
        if (isBlogPage) {
            // 在博客页面：获取最近更新的博客文章（排除当前博客）
            const projectId = this.getProjectIdFromUrl();
            if (projectId) {
                // 使用最新博文API，在服务端过滤当前博客
                apiUrl = `/api/blogs/posts/latest?limit=5&exclude=${projectId}`;
            } else {
                this.showError('无法获取博客ID');
                return;
            }
        } else {
            // 在首页：获取最近更新的博客文章
            apiUrl = '/api/blogs/posts/latest?limit=5';
        }

        try {
            // 获取最近更新的博客文章数据
            const response = await fetch(apiUrl);
            if (response.ok) {
                this.recentUpdates = await response.json();
            } else {
                // 如果API不存在，使用模拟数据
                this.recentUpdates = this.getMockRecentUpdates();
            }
        } catch (error) {
            console.error('Error loading recent updates:', error);
            this.recentUpdates = this.getMockRecentUpdates();
        } finally {
            this.loading = false;
            this.render();
        }
    }

    /**
     * 检测是否在博客页面
     * @returns {boolean} 是否在博客页面
     */
    isBlogPage() {
        const path = window.location.pathname;
        return path.startsWith('/blog/');
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    getMockRecentUpdates() {
        return [
            {
                id: 123,
                title: '深入理解Docker容器技术',
                blog_name: '技术探索者',
                blog_id: 123,
                author: '张三',
                time: '2小时前'
            },
            {
                id: 456,
                title: '周末城市漫步记',
                blog_name: '生活记录者',
                blog_id: 456,
                author: '李四',
                time: '4小时前'
            },
            {
                id: 789,
                title: '《人类简史》读后感',
                blog_name: '读书分享家',
                blog_id: 789,
                author: '王五',
                time: '6小时前'
            }
        ];
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-xl);
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    margin-bottom: var(--spacing-6);
                }

                .card-header {
                    padding: var(--spacing-4) var(--spacing-6);
                    background: var(--gray-50);
                    border-bottom: 1px solid var(--gray-200);
                }

                .card-title {
                    margin: 0;
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-800);
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .updates-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .update-item {
                    border-bottom: 1px solid var(--gray-100);
                    padding: var(--spacing-4) var(--spacing-6);
                }

                .update-item:last-child {
                    border-bottom: none;
                }

                .update-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-2);
                }

                .blog-name {
                    font-weight: 500;
                    color: var(--primary-color);
                    font-size: var(--font-size-sm);
                    text-decoration: none;
                }

                .blog-name:hover {
                    text-decoration: underline;
                }

                .update-time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }

                .latest-post {
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                    line-height: 1.4;
                    background: var(--gray-50);
                    padding: var(--spacing-2) var(--spacing-3);
                    border-radius: var(--radius-md);
                    border-left: 3px solid var(--success-color);
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .error {
                    text-align: center;
                    padding: var(--spacing-6);
                    color: var(--error-color);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }

                .empty-state {
                    text-align: center;
                    padding: var(--spacing-6);
                    color: var(--gray-500);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                        </svg>
                        最近更新
                    </h3>
                </div>
                ${this.loading ? this.renderLoading() : 
                  this.recentUpdates.length > 0 ? this.renderUpdates() : 
                  this.renderEmptyState()}
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

    renderUpdates() {
        return `
            <ul class="updates-list">
                ${this.recentUpdates.map(update => `
                    <li class="update-item">
                        <div class="update-header">
                            <a href="/blog/${update.blog_id}" class="blog-name">${update.blog_name}</a>
                            <span class="update-time">${update.time}</span>
                        </div>
                        <div class="latest-post">${this.truncateText(update.title, 40)}</div>
                    </li>
                `).join('')}
            </ul>
        `;
    }

    renderEmptyState() {
        return `
            <div class="empty-state">
                <div>暂无更新</div>
            </div>
        `;
    }

    renderError() {
        return `
            <div class="error">
                <div>加载失败</div>
            </div>
        `;
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }

    /**
     * 截断文本
     * @param {string} text - 原始文本
     * @param {number} maxLength - 最大长度
     * @returns {string} 截断后的文本
     */
    truncateText(text, maxLength) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
    }
}

customElements.define('recent-updates-card', RecentUpdatesCard);
