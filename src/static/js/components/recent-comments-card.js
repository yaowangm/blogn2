class RecentCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.comments = [];
        this.loading = true;
        this.error = false;
        this.errorMessage = '';
    }

    connectedCallback() {
        this.render();
        BaseComponent.observeWhenVisible(this, () => this.loadData());
    }

    async loadData() {
        try {
            const isBlogRelatedPage = this.isBlogRelatedPage();
            let apiUrl;

            if (isBlogRelatedPage) {
                const projectId = await this.getProjectIdFromCurrentPage();
                if (projectId) {
                    apiUrl = `/api/projects/${projectId}/comments/recent?limit=5`;
                } else {
                    apiUrl = '/api/comments/recent?limit=5';
                }
            } else {
                apiUrl = '/api/comments/recent?limit=5';
            }

            const response = await fetch(apiUrl);
            if (response.ok) {
                this.comments = await response.json();
            } else if (response.status === 404) {
                window.location.href = '/static/error.html';
                return;
            } else {
                throw new Error('Failed to fetch recent comments');
            }

            this.comments = this.comments.map(comment => ({
                ...comment,
                time: this.formatTime(comment.time)
            }));
        } catch (error) {
            this.logError('Error loading recent comments', error);
            this.error = true;
            this.errorMessage = '加载评论失败，请稍后重试';
        } finally {
            this.loading = false;
            this.render();
        }
    }

    isBlogRelatedPage() {
        const path = window.location.pathname;
        return path.startsWith('/blog/') || path.startsWith('/article/');
    }

    async getProjectIdFromCurrentPage() {
        const path = window.location.pathname;

        if (path.startsWith('/blog/')) {
            return this.getProjectId();
        }
        if (path.startsWith('/article/')) {
            return await this.getProjectIdFromArticlePage();
        }

        return null;
    }

    async getProjectIdFromArticlePage() {
        const articleId = this.getArticleId();
        if (!articleId) {
            return null;
        }

        try {
            const articleData = await BaseComponent.getArticle(articleId);
            if (articleData) {
                return articleData.project?.id;
            }
        } catch (error) {
            console.warn('Failed to fetch article data for project ID:', error);
        }

        const articleHeaderCard = document.querySelector('article-header-card');
        if (articleHeaderCard && articleHeaderCard.articleData) {
            return articleHeaderCard.articleData.projectid;
        }

        const articleContentCard = document.querySelector('article-content-card');
        if (articleContentCard && articleContentCard.articleData) {
            return articleContentCard.articleData.projectid;
        }

        return null;
    }

    formatTime(time) {
        if (!time) {
            return '未知时间';
        }

        if (typeof time === 'string' && (time.includes('前') || time.includes('小时') || time.includes('分钟'))) {
            return time;
        }

        try {
            const dateObj = new Date(time);
            const now = new Date();
            const diff = now - dateObj;
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);

            if (seconds < 60) {
                return '刚刚';
            }
            if (minutes < 60) {
                return `${minutes}分钟前`;
            }
            if (hours < 24) {
                return `${hours}小时前`;
            }
            if (days < 7) {
                return `${days}天前`;
            }
            return dateObj.toLocaleDateString('zh-CN');
        } catch (error) {
            return '未知时间';
        }
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderAuthorMetaItem(authorName, avatar, userId) {
        const safeAuthor = this.escapeHtml(authorName || '匿名用户');
        const isAnonymous = this.isAnonymousUser(userId);
        const avatarPath = !isAnonymous ? (avatar || this.getSmallAvatarPath(userId)) : null;
        const fallbackContent = this.getAuthorAvatarFallbackContent(authorName, userId);
        const fallbackClass = isAnonymous
            ? 'author-avatar-fallback author-avatar-fallback--default-user'
            : 'author-avatar-fallback';

        const avatarHtml = `
            <span class="author-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="${fallbackClass}" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackContent}</span>
            </span>
        `;

        return `
            <div class="meta-item meta-item-author">
                ${avatarHtml}
                <span class="author-name">${safeAuthor}</span>
            </div>
        `;
    }

    getNavigationUrl(comment) {
        if (!comment.projectitemid || comment.projectitemid === undefined || comment.projectitemid === null) {
            return null;
        }

        if (!comment.id || comment.id === undefined || comment.id === null) {
            return null;
        }

        const projectitemid = parseInt(comment.projectitemid, 10);
        const commentId = parseInt(comment.id, 10);
        if (isNaN(projectitemid) || projectitemid <= 0 || isNaN(commentId) || commentId <= 0) {
            return null;
        }

        return `/article/${projectitemid}#post${commentId}`;
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');

                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .comment-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .comment-item {
                    border-bottom: 1px solid var(--gray-100);
                    padding: var(--spacing-3) var(--spacing-4);
                    transition: var(--transition-normal);
                }

                .comment-item:hover,
                .comment-item:focus-within {
                    background: var(--interactive-hover-bg);
                }

                .comment-item:hover .author-name,
                .comment-item:focus-within .author-name {
                    color: var(--interactive-hover-text);
                }

                .comment-link {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                    width: 100%;
                }

                .comment-link:hover {
                    text-decoration: none;
                }

                .comment-item:last-child {
                    border-bottom: none;
                }

                .comment-item.disabled {
                    cursor: default;
                    opacity: 0.7;
                }

                .comment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: var(--spacing-2);
                    margin-bottom: var(--spacing-1);
                }

                .meta-item {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    min-width: 0;
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                    white-space: nowrap;
                }

                .meta-item-author {
                    gap: var(--spacing-2);
                }

                .author-avatar {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                }

                .author-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                }

                .author-avatar-fallback {
                    width: 100%;
                    height: 100%;
                    align-items: center;
                    justify-content: center;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    color: var(--gray-600);
                }

                .author-name {
                    font-weight: 500;
                    color: var(--gray-700);
                    transition: color var(--transition-fast);
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .comment-time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }

                .comment-text {
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                    font-weight: 400;
                    line-height: 1.6;
                    margin: 0;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .error {
                    text-align: center;
                    padding: var(--spacing-3) var(--spacing-4);
                    color: var(--error-color);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.comments}
                        最近评论
                    </h3>
                </div>
                ${this.loading ? this.renderLoading() :
                  this.error ? this.renderError() :
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
            <ul class="comment-list">
                ${this.comments.map((comment) => {
                    const commentUrl = this.getNavigationUrl(comment);
                    const authorMeta = this.renderAuthorMetaItem(
                        comment.author,
                        comment.avatar,
                        comment.userid
                    );
                    const contentHtml = `
                        <div class="comment-header">
                            ${authorMeta}
                            <span class="comment-time">${this.escapeHtml(comment.time)}</span>
                        </div>
                        <div class="comment-text">${this.escapeHtml(this.truncateText(comment.content, 20))}</div>
                    `;

                    if (commentUrl) {
                        return `
                            <li class="comment-item">
                                <a href="${commentUrl}" class="comment-link" target="_blank" title="查看评论">
                                    ${contentHtml}
                                </a>
                            </li>
                        `;
                    }

                    return `
                        <li class="comment-item disabled">
                            ${contentHtml}
                        </li>
                    `;
                }).join('')}
            </ul>
        `;
    }

    renderEmptyState() {
        return `
            <div class="loading">
                <div>暂无评论</div>
            </div>
        `;
    }

    renderError() {
        return `
            <div class="error">
                <div>${Icons.warning} ${this.errorMessage}</div>
            </div>
        `;
    }
}

customElements.define('recent-comments-card', RecentCommentsCard);
