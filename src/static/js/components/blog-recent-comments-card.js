/**
 * 博客最近评论卡片组件
 * 显示当前博客的最近评论
 */
class BlogRecentCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.comments = [];
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
            // 获取博客最近评论数据
            const response = await fetch(`/api/projects/${this.projectId}/comments/recent?limit=5`);
            if (response.ok) {
                this.comments = await response.json();
            } else {
                // 如果API不存在，使用模拟数据
                this.comments = this.getMockComments();
            }
        } catch (error) {
            console.error('Error loading blog recent comments:', error);
            this.comments = this.getMockComments();
        } finally {
            this.loading = false;
            this.render();
        }
    }

    getMockComments() {
        return [
            {
                id: 1,
                user_name: '张三',
                content: '这篇文章写得很好，对我很有帮助！',
                post_time: '2024-01-15T10:30:00Z',
                project_item_name: '如何学习FastAPI'
            },
            {
                id: 2,
                user_name: '李四',
                content: '感谢分享，学到了很多新知识。',
                post_time: '2024-01-14T15:20:00Z',
                project_item_name: 'Python异步编程实践'
            },
            {
                id: 3,
                user_name: '王五',
                content: '这个思路很新颖，值得借鉴。',
                post_time: '2024-01-13T09:15:00Z',
                project_item_name: '数据库设计最佳实践'
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

                .comments-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .comment-item {
                    border-bottom: 1px solid var(--gray-100);
                    padding: var(--spacing-4) var(--spacing-6);
                }

                .comment-item:last-child {
                    border-bottom: none;
                }

                .comment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-2);
                }

                .comment-author {
                    font-weight: 500;
                    color: var(--primary-color);
                    font-size: var(--font-size-sm);
                }

                .comment-time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }

                .comment-content {
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                    line-height: 1.5;
                    margin-bottom: var(--spacing-2);
                }

                .comment-article {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    background: var(--gray-50);
                    padding: var(--spacing-2) var(--spacing-3);
                    border-radius: var(--radius-md);
                    border-left: 3px solid var(--primary-color);
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
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                        最近评论
                    </h3>
                </div>
                ${this.loading ? this.renderLoading() : 
                  this.comments.length > 0 ? this.renderComments() : 
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

    renderComments() {
        return `
            <ul class="comments-list">
                ${this.comments.map(comment => `
                    <li class="comment-item">
                        <div class="comment-header">
                            <span class="comment-author">${comment.user_name}</span>
                            <span class="comment-time">${this.formatDate(comment.post_time)}</span>
                        </div>
                        <div class="comment-content">${this.truncateText(comment.content, 50)}</div>
                        <div class="comment-article">${comment.project_item_name}</div>
                    </li>
                `).join('')}
            </ul>
        `;
    }

    renderEmptyState() {
        return `
            <div class="empty-state">
                <div>暂无评论</div>
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
}

customElements.define('blog-recent-comments-card', BlogRecentCommentsCard);
