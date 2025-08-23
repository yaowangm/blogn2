/**
 * 文章评论卡片组件
 * 显示文章的评论列表
 */
class ArticleCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
        this.userMap = {};
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
                
                // 如果有评论，获取每个评论的用户信息
                if (this.articleData.comments && this.articleData.comments.length > 0) {
                    await this.loadCommentUsers();
                }
            } else if (response.status === 404) {
                this.showError('文章不存在');
                return;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.logError('Failed to load article data', error);
            this.showError('加载文章数据失败');
        }
    }

    /**
     * 加载评论用户信息
     */
    async loadCommentUsers() {
        if (!this.articleData.comments) return;
        
        try {
            // 获取所有不重复的用户ID
            const userIds = [...new Set(this.articleData.comments
                .map(comment => comment.user_id)
                .filter(id => id))];
            
            // 批量获取用户信息
            const userPromises = userIds.map(async (userId) => {
                try {
                    const userResponse = await fetch(`/api/users/${userId}`);
                    if (userResponse.ok) {
                        return await userResponse.json();
                    }
                } catch (error) {
                    console.warn(`Failed to load user ${userId}:`, error);
                }
                return null;
            });
            
            const users = await Promise.all(userPromises);
            
            // 创建用户ID到用户信息的映射
            this.userMap = {};
            users.forEach(user => {
                if (user) {
                    this.userMap[user.id] = user;
                }
            });
        } catch (error) {
            console.warn('Failed to load comment users:', error);
            this.userMap = {};
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
        
        // 获取用户名和博客ID，如果没有则显示用户ID或匿名
        let userName = '匿名';
        let blogId = null;
        let userAvatar = null;
        
        if (user_id) {
            if (this.userMap && this.userMap[user_id]) {
                const user = this.userMap[user_id];
                userName = user.name || `用户${user_id}`;
                blogId = user.projectid || null;
                
                // 构建头像路径
                if (user.id) {
                    const prefix = Math.floor(user.id / 10000) + 1;
                    userAvatar = `/avatar/${prefix}/${user.id}.jpg`;
                }
            } else {
                userName = `用户${user_id}`;
            }
        }
        
        return `
            <div class="comment-item" data-comment-id="${id}">
                <div class="comment-avatar">
                    ${blogId ? `
                        <a href="/blog/${blogId}" class="avatar-link" title="查看博客">
                            <div class="user-avatar">
                                ${userAvatar ? 
                                    `<img src="${userAvatar}" alt="${this.escapeHtml(userName)}" 
                                          onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                                          onload="this.style.display='block'; this.nextElementSibling.style.display='none';"
                                          style="display: block;">` : 
                                    ''
                                }
                                <span style="display: ${userAvatar ? 'none' : 'flex'}; color: var(--gray-600);">${userName.charAt(0).toUpperCase()}</span>
                            </div>
                        </a>
                    ` : `
                        <div class="user-avatar">
                            <span style="color: var(--gray-600);">?</span>
                        </div>
                    `}
                </div>
                
                <div class="comment-content-wrapper">
                    <div class="comment-header">
                        <div class="comment-user">
                            ${blogId ? `
                                <a href="/blog/${blogId}" class="user-link" title="查看博客">
                                    <span class="user-name">${this.escapeHtml(userName)}</span>
                                </a>
                            ` : `
                                <span class="user-name">${this.escapeHtml(userName)}</span>
                            `}
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
                    border-bottom: 1px solid var(--gray-200);
                    background-color: var(--gray-50);
                }
                
                .card-header h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-800);
                    margin: 0;
                }

                .card-body {
                    padding: var(--spacing-6);
                }
                
                .comments-list {
                    max-height: 600px;
                    overflow-y: auto;
                }
                
                .comment-item {
                    display: flex;
                    gap: var(--spacing-4);
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

                .comment-avatar {
                    flex-shrink: 0;
                }

                .avatar-link {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }

                .user-avatar {
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 2px solid var(--gray-200);
                    overflow: hidden;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .comment-content-wrapper {
                    flex: 1;
                    min-width: 0;
                }
                
                .comment-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-3);
                }
                
                .comment-user .user-name {
                    font-weight: 600;
                    color: var(--primary-color);
                    font-size: var(--font-size-sm);
                }

                .user-link {
                    text-decoration: none;
                    color: inherit;
                    transition: color var(--transition-fast);
                }

                .user-link:hover .user-name {
                    color: var(--primary-hover);
                    text-decoration: underline;
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
