class BlogListCard extends BaseComponent {
    constructor() {
        super();
    }

    /**
     * 检测是否在博客页面
     * @returns {boolean} 是否在博客页面
     */
    isBlogPage() {
        const path = window.location.pathname;
        return path.match(/\/blog\/(\d+)/) !== null;
    }

    /**
     * 从URL中获取项目ID
     * @returns {number|null} 项目ID
     */
    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    connectedCallback() {
        this.render();
        this.loadContent();
    }

    async loadContent() {
        try {
            // 检测是否在博客页面
            const isBlogPage = this.isBlogPage();
            let apiUrl;
            
            if (isBlogPage) {
                // 在博客页面：获取当前博客的文章
                const projectId = this.getProjectIdFromUrl();
                if (projectId) {
                    apiUrl = `/api/blogs/posts/latest?blogid=${projectId}`;
                } else {
                    this.showError('无法获取博客ID');
                    return;
                }
            } else {
                // 在首页：获取所有博客的最新文章
                apiUrl = '/api/blogs/posts/latest';
            }
            
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error('Failed to fetch posts');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading posts', error);
            this.showError();
        }
    }

    updateContent(posts) {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            if (posts.length === 0) {
                cardBody.innerHTML = `
                    <div class="post-list">
                        <div class="post-item">
                            <div class="post-content">
                                <p class="post-excerpt">暂无博文</p>
                            </div>
                        </div>
                    </div>
                `;
                return;
            }
            
            const postsHtml = posts.map(post => `
                <a href="/projectitem/${post.id}" class="post-item">
                    <div class="post-avatar">
                        ${post.avatar ? 
                            `<img src="${post.avatar}" alt="${post.author}" onerror="this.style.display='none'">` :
                            `<span>${post.author ? post.author.charAt(0) : '用'}</span>`
                        }
                    </div>
                    <div class="post-content">
                        <h4 class="post-title">${post.title}</h4>
                        <div class="post-meta">
                            <span class="post-author">${post.author}</span>
                            <span class="post-date">${post.time}</span>
                        </div>
                        <p class="post-excerpt">${post.excerpt}</p>
                        ${post.image ? `<div class="post-attachment-image"><img src="${post.image}" alt="${post.title}" onerror="this.style.display='none'"></div>` : ''}
                    </div>
                </a>
            `).join('');
            
            cardBody.innerHTML = `
                <div class="post-list">
                    ${postsHtml}
                </div>
            `;
        }
    }

    showError() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML('加载失败，请稍后重试');
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

                .post-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }

                .post-item {
                    display: flex;
                    gap: var(--spacing-4);
                    padding: var(--spacing-4);
                    border-radius: var(--radius-lg);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    transition: var(--transition-fast);
                    text-decoration: none;
                    color: inherit;
                }

                .post-item:hover {
                    background: var(--white);
                    box-shadow: var(--shadow-md);
                    transform: translateY(-2px);
                }

                .post-avatar {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: var(--accent-color);
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--white);
                    font-weight: 600;
                    font-size: var(--font-size-lg);
                    overflow: hidden;
                    border: 2px solid var(--gray-200);
                    position: relative;
                    margin-top: 20px;
                }

                .post-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 50%;
                }

                .post-avatar span {
                    font-weight: 600;
                    font-size: var(--font-size-xl);
                    line-height: 1;
                }

                .post-content {
                    flex: 1;
                    min-width: 0;
                }

                .post-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-2);
                    line-height: 1.4;
                }

                .post-meta {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-bottom: var(--spacing-2);
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                .post-author {
                    font-weight: 500;
                    color: var(--primary-color);
                }

                .post-date {
                    color: var(--gray-500);
                }

                .post-excerpt {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    line-height: 1.6;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    margin-bottom: var(--spacing-3);
                }

                .post-attachment-image {
                    margin-top: var(--spacing-3);
                    border-radius: var(--radius-md);
                    overflow: hidden;
                    max-width: 100%;
                }

                .post-attachment-image img {
                    width: 100%;
                    max-width: 400px;
                    height: auto;
                    border-radius: var(--radius-md);
                    transition: var(--transition-fast);
                }

                .post-attachment-image img:hover {
                    transform: scale(1.02);
                }

                @media (max-width: 768px) {
                    .post-item {
                        flex-direction: column;
                        gap: var(--spacing-3);
                    }
                    
                    .post-avatar {
                        width: 80px;
                        height: 80px;
                        align-self: center;
                        margin-top: 25px;
                    }

                    .post-attachment-image img {
                        max-width: 100%;
                        height: auto;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">${this.isBlogPage() ? '博客文章' : '最新博文'}</h3>
                </div>
                <div class="card-body">
                    <div class="post-list">
                        <div class="post-item">
                            <div class="post-avatar"><span>加</span></div>
                            <div class="post-content">
                                <p class="post-excerpt">正在加载博文...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('blog-list-card', BlogListCard); 