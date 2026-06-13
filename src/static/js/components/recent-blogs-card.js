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
            <div class="article-meta">
                <div class="meta-items-left">
                    <div class="meta-item meta-item-author">
                        ${avatarHtml}
                        <span class="author-name">${safeName}</span>
                    </div>
                </div>
                <div class="meta-item">
                    <span>${safeJoinDate}</span>
                </div>
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
                    <div class="card-body">
                        <div class="post-list">
                            ${this.blogs.map(blog => `
                                <a href="/blog/${blog.id}" class="post-item" target="_blank" rel="noopener noreferrer">
                                    <div class="post-content">
                                        ${this.renderBlogMetaItem(blog)}
                                    </div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                `}
            </div>
        `;
    }
}

customElements.define('recent-blogs-card', RecentBlogsCard);
