class RecentBlogsCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const recentBlogs = [
            { name: '技术探索者', joinDate: '2天前', avatar: '技' },
            { name: '生活随笔', joinDate: '3天前', avatar: '生' },
            { name: '编程日记', joinDate: '5天前', avatar: '编' },
            { name: '摄影分享', joinDate: '1周前', avatar: '摄' },
            { name: '读书笔记', joinDate: '1周前', avatar: '读' }
        ];

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    transition: var(--transition-normal);
                }

                .card:hover {
                    box-shadow: var(--shadow-md);
                    transform: translateY(-2px);
                }

                .card-header {
                    padding: var(--spacing-4) var(--spacing-5);
                    border-bottom: 1px solid var(--gray-200);
                    background: var(--gray-50);
                }

                .card-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                }

                .card-body {
                    padding: var(--spacing-5);
                }

                .blog-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-3);
                }

                .blog-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    transition: var(--transition-fast);
                    text-decoration: none;
                    color: var(--gray-700);
                }

                .blog-item:hover {
                    background: var(--gray-50);
                    color: var(--primary-color);
                }

                .blog-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: var(--primary-color);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--white);
                    font-weight: 600;
                    font-size: var(--font-size-sm);
                    flex-shrink: 0;
                }

                .blog-info {
                    flex: 1;
                    min-width: 0;
                }

                .blog-name {
                    font-weight: 500;
                    margin-bottom: var(--spacing-1);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .blog-meta {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最新加入</h3>
                </div>
                <div class="card-body">
                    <div class="blog-list">
                        ${recentBlogs.map(blog => `
                            <a href="/blog/${blog.name}" class="blog-item">
                                <div class="blog-avatar">${blog.avatar}</div>
                                <div class="blog-info">
                                    <div class="blog-name">${blog.name}</div>
                                    <div class="blog-meta">${blog.joinDate}</div>
                                </div>
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('recent-blogs-card', RecentBlogsCard); 