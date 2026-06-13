class PopularBlogsCard extends BaseComponent {
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
            const response = await fetch('/api/blogs/popular?limit=10');
            if (!response.ok) {
                throw new Error('Failed to fetch popular blogs');
            }
            this.blogs = await response.json();
        } catch (error) {
            this.logError('Error loading popular blogs', error);
            this.blogs = [
                { id: 1, name: '技术前沿', join_date: '1周前', followers: '1.2k', avatar: null, userid: 1, rank: 1 },
                { id: 2, name: '生活美学', join_date: '2周前', followers: '856', avatar: null, userid: 2, rank: 2 },
                { id: 3, name: '编程之道', join_date: '3周前', followers: '743', avatar: null, userid: 3, rank: 3 },
                { id: 4, name: '摄影艺术', join_date: '1月前', followers: '621', avatar: null, userid: 4, rank: 4 },
                { id: 5, name: '读书会', join_date: '1月前', followers: '589', avatar: null, userid: 5, rank: 5 }
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
        const safeJoinDate = this.escapeHtml(blog.join_date || '');
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

                .blog-rank {
                    font-size: var(--font-size-xs);
                    color: var(--accent-color);
                    font-weight: 600;
                    flex-shrink: 0;
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
                        ${Icons.popular}
                        最热门
                    </h3>
                </div>
                ${this.loading ? `<div class="loading">${this.createLoadingHTML()}</div>` : `
                    <div class="card-body">
                        <div class="post-list">
                            ${this.blogs.map(blog => {
                                const safeRank = this.escapeHtml(blog.rank);
                                return `
                                    <a href="/blog/${blog.id}" class="post-item" target="_blank" rel="noopener noreferrer">
                                        <div class="post-content">
                                            ${this.renderBlogMetaItem(blog)}
                                            <div class="meta-item blog-rank">#${safeRank}</div>
                                        </div>
                                    </a>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `}
            </div>
        `;
    }
}

customElements.define('popular-blogs-card', PopularBlogsCard);
