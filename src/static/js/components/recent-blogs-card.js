class RecentBlogsCard extends BaseComponent {
    constructor() {
        super();
        this.blogs = [];
        this.loading = true;
    }

    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
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
            // 使用默认数据作为后备
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
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }

                .card-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                }

                .icon {
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .icon svg {
                    width: 20px;
                    height: 20px;
                    stroke: var(--primary-color);
                    stroke-width: 2;
                    fill: none;
                    stroke-linecap: round;
                    stroke-linejoin: round;
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

                .loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .loading-spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--gray-200);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: var(--spacing-2);
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <div class="icon">
                        ${Icons.recent}
                    </div>
                    <h3 class="card-title">最新加入</h3>
                </div>
                <div class="card-body">
                    ${this.loading ? this.createLoadingHTML() : `
                        <div class="blog-list">
                            ${this.blogs.map(blog => {
                                // 安全处理所有文本字段，防止HTML注入和XSS攻击
                                const safeName = this.escapeHtml(blog.name);
                                const safeJoinDate = this.escapeHtml(blog.join_date);
                                
                                return `
                                    <a href="/blog/${blog.id}" class="blog-item" target="_blank" rel="noopener noreferrer">
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
                                `;
                            }).join('')}
                        </div>
                    `}
                </div>
            </div>
        `;
    }
}

customElements.define('recent-blogs-card', RecentBlogsCard); 