class RecentBlogsCard extends BaseComponent {
    constructor() {
        super();
        this.blogs = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        this.loadData();
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
                { name: '技术探索者', join_date: '2天前', avatar: '技' },
                { name: '生活随笔', join_date: '3天前', avatar: '生' },
                { name: '编程日记', join_date: '5天前', avatar: '编' },
                { name: '摄影分享', join_date: '1周前', avatar: '摄' },
                { name: '读书笔记', join_date: '1周前', avatar: '读' }
            ];
        } finally {
            this.loading = false;
            this.render();
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css?v=20250610');

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
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3) var(--spacing-4);
                    text-decoration: none;
                    color: inherit;
                    transition: var(--transition-fast);
                }

                .blog-item:hover {
                    background: var(--gray-50);
                }

                .blog-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 2px solid var(--gray-200);
                    overflow: hidden;
                }

                .blog-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .blog-info {
                    flex: 1;
                    min-width: 0;
                }

                .blog-name {
                    font-weight: 600;
                    color: var(--gray-900);
                    font-size: var(--font-size-sm);
                    margin: 0 0 var(--spacing-1) 0;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .blog-meta {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    margin: 0;
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
                        ${this.blogs.map(blog => {
                            const safeName = this.escapeHtml(blog.name);
                            const safeJoinDate = this.escapeHtml(blog.join_date);

                            return `
                                <li class="blog-item">
                                    <a href="/blog/${blog.id}" class="blog-link" target="_blank" rel="noopener noreferrer">
                                        <div class="blog-avatar">
                                            ${blog.avatar ?
                                                `<img src="${blog.avatar}" alt="${safeName}">` :
                                                `<span>${safeName ? safeName.charAt(0) : '博'}</span>`
                                            }
                                        </div>
                                        <div class="blog-info">
                                            <div class="blog-name">${safeName}</div>
                                            <div class="blog-meta">${safeJoinDate}</div>
                                        </div>
                                    </a>
                                </li>
                            `;
                        }).join('')}
                    </ul>
                `}
            </div>
        `;
    }
}

customElements.define('recent-blogs-card', RecentBlogsCard);
