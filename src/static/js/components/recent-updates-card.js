/**
 * 最近更新卡片组件
 * 显示最近更新的内容列表
 */
class RecentUpdatesCard extends BaseComponent {
    constructor() {
        super();
        this.recentUpdates = [];
        this.loading = true;
        this.error = false;
        this.errorMessage = '';
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
                const data = await response.json();
                // API返回的是 { posts: [...], total: ... } 格式，我们需要提取 posts 数组
                this.recentUpdates = data.posts || [];
            } else if (response.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                // 其他错误，设置错误状态
                this.error = true;
                this.errorMessage = '加载失败，请稍后重试';
            }
        } catch (error) {
            console.error('Error loading recent updates:', error);
            this.error = true;
            this.errorMessage = '加载失败，请稍后重试';
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
        // 使用基类的统一方法
        return this.getProjectId();
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderAuthorMetaItem(authorName, avatar, userId) {
        const safeAuthor = this.escapeHtml(authorName || '未知作者');
        const avatarPath = avatar || this.getSmallAvatarPath(userId);
        const fallbackLetter = safeAuthor.charAt(0).toUpperCase();

        const avatarHtml = `
            <span class="author-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="author-avatar-fallback" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackLetter}</span>
            </span>
        `;

        return `
            <div class="meta-item meta-item-author">
                ${avatarHtml}
                <span class="author-name">${safeAuthor}</span>
            </div>
        `;
    }

    getMockRecentUpdates() {
        return [
            {
                id: 123,
                title: '深入理解Docker容器技术',
                blog_name: '技术探索者',
                blog_id: 123,
                author: '张三',
                time: '2小时前',
                avatar: null
            },
            {
                id: 456,
                title: '周末城市漫步记',
                blog_name: '生活记录者',
                blog_id: 456,
                author: '李四',
                time: '4小时前',
                avatar: null
            },
            {
                id: 789,
                title: '《人类简史》读后感',
                blog_name: '读书分享家',
                blog_id: 789,
                author: '王五',
                time: '6小时前',
                avatar: null
            }
        ];
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

                .updates-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .update-item {
                    border-bottom: 1px solid var(--gray-100);
                    padding: var(--spacing-3) var(--spacing-4);
                    transition: var(--transition-normal);
                }

                .update-item:hover {
                    background: var(--gray-50);
                }

                .update-link {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                    width: 100%;
                }

                .update-link:hover {
                    text-decoration: none;
                }

                .update-item:last-child {
                    border-bottom: none;
                }

                .update-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: var(--spacing-2);
                    margin-bottom: var(--spacing-1);
                }

                .meta-item {
                    display: flex;
                    align-items: center;
                    min-width: 0;
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
                    font-weight: 700;
                    color: var(--gray-900);
                    font-size: var(--font-size-sm);
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
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
                    padding: 0;
                    border-radius: var(--radius-md);
                    margin: 0;
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

                .empty-state {
                    text-align: center;
                    padding: var(--spacing-3) var(--spacing-4);
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
                  this.error ? this.renderError() :
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
                ${this.recentUpdates.map((update) => {
                    const safeTime = this.escapeHtml(update.time);
                    const safeTitle = this.escapeHtml(update.title);
                    const authorMeta = this.renderAuthorMetaItem(update.blog_name, update.avatar, update.userid);
                    const contentHtml = `
                        <div class="update-header">
                            ${authorMeta}
                            <span class="update-time">${safeTime}</span>
                        </div>
                        <div class="latest-post">${this.truncateText(safeTitle, 40)}</div>
                    `;

                    if (update.id) {
                        return `
                            <li class="update-item">
                                <a href="/article/${update.id}" class="update-link" target="_blank" title="查看文章">
                                    ${contentHtml}
                                </a>
                            </li>
                        `;
                    }

                    return `
                        <li class="update-item disabled">
                            ${contentHtml}
                        </li>
                    `;
                }).join('')}
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
                <div>${Icons.warning} ${this.errorMessage}</div>
            </div>
        `;
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }

}

customElements.define('recent-updates-card', RecentUpdatesCard);
