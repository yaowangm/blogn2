/**
 * 文章评论卡片组件
 * 显示文章的评论列表
 */
class ArticleCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
    }

    async connectedCallback() {
        // 从URL获取文章ID
        this.articleId = this.getArticleIdFromUrl();
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        // 加载文章数据
        await this.loadArticleData();
        
        // 渲染组件
        this.render();
    }

    /**
     * 从URL获取文章ID
     */
    getArticleIdFromUrl() {
        // 使用基类的统一方法
        return this.getArticleId();
    }

    /**
     * 加载文章数据
     */
    async loadArticleData() {
        try {
            const response = await fetch(`/api/articles/${this.articleId}`);
            if (response.ok) {
                this.articleData = await response.json();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.logError('Failed to load article data', error);
            this.showError('加载文章数据失败');
        }
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.shadowRoot.innerHTML = `
                <div class="card article-comments-card">
                    <div class="card-body">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            `;
            return;
        }

        const { comments, comment_count } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-comments-card">
                <div class="card-header">
                    <h3>评论 (${comment_count || 0})</h3>
                </div>
                <div class="card-body">
                    ${this.renderComments(comments)}
                </div>
            </div>
        `;

        this.addStyles();
    }

    /**
     * 渲染评论列表
     */
    renderComments(comments) {
        if (!comments || comments.length === 0) {
            return `
                <div class="no-comments">
                    <p>暂无评论，成为第一个评论者吧！</p>
                </div>
            `;
        }

        return `
            <div class="comments-list">
                ${comments.map(comment => this.renderComment(comment)).join('')}
            </div>
        `;
    }

    /**
     * 渲染单个评论
     */
    renderComment(comment) {
        const { id, content, user_id, post_time, reply_count } = comment;
        
        return `
            <div class="comment-item" data-comment-id="${id}">
                <div class="comment-header">
                    <div class="comment-user">
                        <span class="user-id">用户 ${user_id || '匿名'}</span>
                    </div>
                    <div class="comment-time">
                        ${this.formatDate(post_time)}
                    </div>
                </div>
                
                <div class="comment-content">
                    ${this.escapeHtml(content || '')}
                </div>
                
                ${reply_count > 0 ? `
                    <div class="comment-replies">
                        <span class="reply-count">${reply_count} 条回复</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="card article-comments-card">
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
                .article-comments-card {
                    margin-bottom: var(--spacing-6);
                }
                
                .card-header {
                    padding: var(--spacing-4) var(--spacing-6);
                    border-bottom: 1px solid var(--gray-200);
                    background-color: var(--gray-50);
                }
                
                .card-header h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-800);
                    margin: 0;
                }
                
                .comments-list {
                    max-height: 600px;
                    overflow-y: auto;
                }
                
                .comment-item {
                    padding: var(--spacing-4);
                    border-bottom: 1px solid var(--gray-100);
                    transition: background-color var(--transition-fast);
                }
                
                .comment-item:last-child {
                    border-bottom: none;
                }
                
                .comment-item:hover {
                    background-color: var(--gray-50);
                }
                
                .comment-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-3);
                }
                
                .comment-user .user-id {
                    font-weight: 600;
                    color: var(--primary-color);
                    font-size: var(--font-size-sm);
                }
                
                .comment-time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }
                
                .comment-content {
                    line-height: 1.6;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-3);
                    word-wrap: break-word;
                }
                
                .comment-replies {
                    display: flex;
                    justify-content: flex-end;
                }
                
                .reply-count {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    cursor: pointer;
                    transition: color var(--transition-fast);
                }
                
                .reply-count:hover {
                    color: var(--primary-color);
                }
                
                .no-comments {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
                
                .no-comments p {
                    margin: 0;
                    font-style: italic;
                }
                
                .loading {
                    text-align: center;
                    color: var(--gray-500);
                    padding: var(--spacing-8);
                }
                
                .error-message {
                    text-align: center;
                    color: var(--error-color);
                    padding: var(--spacing-8);
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('article-comments-card', ArticleCommentsCard);
