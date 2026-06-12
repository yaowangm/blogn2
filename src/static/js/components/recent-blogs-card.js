class RecentBlogsCard extends BaseComponent {
    constructor() {
        super();
        this.blogs = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        BaseComponent.observeWhenVisible(this, () => this.loadData());
    }

    async loadData() {
        try {
            const response = await fetch('/api/blogs/recent?limit=10');
            if (!response.ok) {
                throw new Error('Failed to fetch recent blogs');
            }
            this.blogs = await response.json();
        } catch (error) {
            this.logError('Error loading recent blogs', error);
            this.blogs = [
                { id: 1, name: '技术探索者', join_date: '2天前', avatar: null, userid: 1 },
                { id: 2, name: '生活随笔', join_date: '3天前', avatar: null, userid: 2 },
                { id: 3, name: '编程日记', join_date: '5天前', avatar: null, userid: 3 },
                { id: 4, name: '摄影分享', join_date: '1周前', avatar: null, userid: 4 },
                { id: 5, name: '读书笔记', join_date: '1周前', avatar: null, userid: 5 }
            ];
        } finally {
            this.loading = false;
            this.render();
        }
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderBlogMetaItem(blog) {
        const safeName = this.escapeHtml(blog.name);
        const safeJoinDate = this.escapeHtml(blog.join_date);
        const avatarPath = blog.avatar || this.getSmallAvatarPath(blog.userid);
        const fallbackLetter = safeName ? safeName.charAt(0).toUpperCase() : '博';

        const avatarHtml = `
            <span class="blog-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="blog-avatar-fallback" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackLetter}</span>
            </span>
        `;

        return `
            <div class="blog-meta-row">
                ${avatarHtml}
                <span class="blog-name">${safeName}</span>
                <span class="blog-date">${safeJoinDate}</span>
            </div>
        `;
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

                .blog-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .blog-item {
                    border-bottom: 1px solid var(--gray-100);
                }

                .blog-item:last-child {
                    border-bottom: none;
                }

                .blog-link {
                    display: block;
                    padding: var(--spacing-3) var(--spacing-4);
                    text-decoration: none;
                    color: inherit;
                    transition: var(--transition-fast);
                }

                .blog-item:hover {
                    background: var(--gray-50);
                }

                .blog-meta-row {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    min-width: 0;
                }

                .blog-avatar {
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

                .blog-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                }

                .blog-avatar-fallback {
                    width: 100%;
                    height: 100%;
                    align-items: center;
                    justify-content: center;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    color: var(--gray-600);
                }

                .blog-name {
                    font-weight: 600;
                    color: var(--gray-900);
                    font-size: var(--font-size-sm);
                    min-width: 0;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .blog-date {
                    flex-shrink: 0;
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    white-space: nowrap;
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.recent}
                        最新加入
                    </h3>
                </div>
                ${this.loading ? `<div class="loading">${this.createLoadingHTML()}</div>` : `
                    <ul class="blog-list">
                        ${this.blogs.map(blog => `
                            <li class="blog-item">
                                <a href="/blog/${blog.id}" class="blog-link" target="_blank" rel="noopener noreferrer">
                                    ${this.renderBlogMetaItem(blog)}
                                </a>
                            </li>
                        `).join('')}
                    </ul>
                `}
            </div>
        `;
    }
}

customElements.define('recent-blogs-card', RecentBlogsCard);
