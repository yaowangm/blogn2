class BlogListCard extends BaseComponent {
    constructor() {
        super();
        this.currentPage = 1;
        this.pageSize = 10; // 默认值，后续会被BLOG_POSTS_PAGE_SIZE配置参数覆盖
        this.totalPosts = 0;
        this.totalPages = 0;
        this.posts = [];
        this.currentFolderId = null;
        this.currentCategoryName = '全部文章';
        this.showCategoryInfo = false; // 控制是否显示分类信息
        this.loadPageSizeConfig();
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
        // 使用基类的统一方法
        return this.getProjectId();
    }

    /**
     * 从URL中获取当前文件夹ID
     * @returns {string|null} 文件夹ID
     */
    getCurrentFolderId() {
        const url = new URL(window.location);
        return url.searchParams.get('folderid');
    }

    /**
     * 获取卡片标题
     * @returns {string} 卡片标题
     */
    getCardTitle() {
        if (this.id === 'subscription-posts-card') {
            return '订阅文章';
        }
        return this.isBlogPage() ? '博客文章' : '最新博文';
    }

    /**
     * 检查是否应该显示分类信息
     * @returns {boolean} 是否显示分类信息
     */
    shouldShowCategoryInfo() {
        // 只有在博客页面的原创文章中才显示分类信息
        return this.isBlogPage() && 
               this.id !== 'subscription-posts-card' && 
               this.hasAttribute('show-category');
    }


    connectedCallback() {
        // 检查是否应该显示分类信息
        this.showCategoryInfo = this.shouldShowCategoryInfo();
        this.currentFolderId = this.getCurrentFolderId();
        this.render();
        this.loadContent();
        this.addEventListeners();
    }

    addEventListeners() {
        // 监听分类变化事件
        this.addEventListener('categoryChanged', (event) => {
            const { folderId, folderName } = event.detail;
            this.currentFolderId = folderId || null;
            this.currentCategoryName = folderName || '全部文章';
            this.currentPage = 1; // 重置页码
            this.loadContent();
        });
        
        // 监听分页变化事件
        this.addEventListener('page-change', (event) => {
            const { page } = event.detail;
            this.goToPage(page);
        });
    }

    async loadContent(page = 1) {
        try {
            this.currentPage = page;
            this.loading = true;
            this.render();
            
            // 检测是否在博客页面
            const isBlogPage = this.isBlogPage();
            let apiUrl;
            
            if (isBlogPage) {
                // 在博客页面：获取当前博客的文章
                const projectId = this.getProjectIdFromUrl();
                if (projectId) {
                    // 检查是否是订阅文章卡片
                    if (this.id === 'subscription-posts-card') {
                        apiUrl = `/api/projects/${projectId}/posts?page=${page}&limit=${this.pageSize}&type=subscription`;
                    } else {
                        apiUrl = `/api/projects/${projectId}/posts?page=${page}&limit=${this.pageSize}&type=original`;
                        // 添加folderid参数
                        if (this.currentFolderId) {
                            apiUrl += `&folderid=${this.currentFolderId}`;
                        }
                    }
                } else {
                    this.showError('无法获取博客ID');
                    return;
                }
            } else {
                // 在首页：获取所有博客的最新文章
                apiUrl = `/api/blogs/posts/latest?page=${page}&page_size=${this.pageSize}`;
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

    updateContent(data) {
        this.posts = data.posts || data;
        this.totalPosts = data.total || this.posts.length;
        this.totalPages = Math.ceil(this.totalPosts / this.pageSize);
        this.loading = false;
        
        // 从API响应中获取分类信息
        if (data.category) {
            this.currentCategoryName = data.category;
        }
        
        // 更新导航栏
        this.updatePagination();
        
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            if (this.posts.length === 0) {
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
            
            
            const postsHtml = this.posts.map(post => {
                // 处理不同的数据格式
                const title = post.title || post.name;
                const author = post.author || post.author_name || '未知作者';
                const time = post.time || post.createtime || '未知时间';
                // 订阅文章使用 comment 字段，原创文章使用 excerpt 字段
                const excerpt = post.comment || post.excerpt || '';
                const image = post.image || (post.attachment ? `/upload/${post.attachment}` : null);
                const avatar = post.avatar;
                
                // 安全处理所有文本字段，防止HTML注入和XSS攻击
                const safeTitle = this.escapeHtml(title);
                const safeAuthor = this.escapeHtml(author);
                // 移除Markdown标记，显示纯文本摘要
                const safeExcerpt = this.escapeHtml(this.stripMarkdown(excerpt));
                const safeBlogName = post.blog_name ? this.escapeHtml(post.blog_name) : '';
                const safeTime = this.escapeHtml(time || '未知时间');
                
                // 如果是订阅文章，显示博客名称
                const blogInfo = safeBlogName ? `<span class="post-blog">来自: ${safeBlogName}</span>` : '';
                
                return `
                    <a href="/article/${post.id}" class="post-item" target="_blank">
                        <div class="post-avatar">
                            ${avatar ? 
                                `<img src="${avatar}" alt="${safeAuthor}" onerror="this.style.display='none'">` :
                                `<span>${safeAuthor ? safeAuthor.charAt(0) : '用'}</span>`
                            }
                        </div>
                        <div class="post-content">
                            <h4 class="post-title">${safeTitle}</h4>
                            <div class="post-meta">
                                <span class="post-author">${safeAuthor}</span>
                                <span class="post-date">${safeTime.replace('T', ' ')}</span>
                                ${blogInfo}
                            </div>
                            <p class="post-excerpt">${safeExcerpt}</p>
                            ${image ? `<div class="post-attachment-image"><img src="${image}" alt="${safeTitle}" onerror="this.style.display='none'"></div>` : ''}
                        </div>
                    </a>
                `;
            }).join('');
            
            cardBody.innerHTML = `
                <div class="post-list">
                    ${postsHtml}
                </div>
            `;
        }
    }

    renderPagination() {
        let paginationHtml = '';
        
        if (this.totalPages > 1) {
            const pagination = {
                current_page: this.currentPage,
                total_pages: this.totalPages,
                total: this.totalPosts,
                has_prev: this.currentPage > 1,
                has_next: this.currentPage < this.totalPages
            };
            
            paginationHtml = `<navigation-card mode="pagination" pagination='${JSON.stringify(pagination)}'></navigation-card>`;
        }
        
        // 添加分类信息（如果启用的话）
        if (this.showCategoryInfo) {
            paginationHtml += `
                <div class="pagination">
                    <div class="pagination-right">
                        <div class="category-info">
                            <span class="category-label">分类：</span>
                            <span class="category-name">${this.escapeHtml(this.currentCategoryName)}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return paginationHtml;
    }

    updatePagination() {
        const placeholder = this.shadowRoot.querySelector('#pagination-placeholder');
        if (placeholder) {
            placeholder.innerHTML = this.renderPagination();
        }
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) return;
        
        // 更新URL参数
        const url = new URL(window.location);
        url.searchParams.set('page', page);
        if (this.currentFolderId) {
            url.searchParams.set('folderid', this.currentFolderId);
        }
        window.history.pushState({}, '', url);
        
        this.loadContent(page);
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
                    max-width: 100%;
                    width: 100%;
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
                    max-width: 100%;
                    overflow: hidden;
                }

                .post-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                    max-width: 100%;
                    overflow: hidden;
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
                    max-width: 100%;
                    overflow: hidden;
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
                    max-width: 100%;
                    overflow: hidden;
                }

                .post-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-2);
                    line-height: 1.4;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    max-width: 100%;
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

                .post-blog {
                    color: var(--accent-color);
                    font-weight: 500;
                    font-size: var(--font-size-xs);
                    background: var(--gray-100);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-sm);
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
                    max-width: 100%;
                    word-wrap: break-word;
                    word-break: break-word;
                    overflow-wrap: break-word;
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

                .pagination {
                    display: flex;
                    justify-content: space-between; /* Changed to space-between */
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-top: var(--spacing-5);
                    padding: var(--spacing-5) 20px;
                    border-top: 1px solid var(--gray-200);
                }

                .pagination-left {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }

                .pagination-right {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }

                .category-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    background: var(--gray-100);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                }

                .category-label {
                    font-weight: 500;
                }

                .category-name {
                    font-weight: 600;
                    color: var(--primary-color);
                }

                .nav-btn {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    padding: var(--spacing-2) var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    background: var(--white);
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    cursor: pointer;
                    transition: var(--transition-fast);
                }

                .nav-btn:hover:not(:disabled) {
                    background: var(--gray-100);
                    border-color: var(--gray-400);
                }

                .nav-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    color: var(--gray-400);
                }

                .nav-icon {
                    font-size: var(--font-size-md);
                }

                .page-info {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: var(--spacing-1);
                    padding: var(--spacing-2) var(--spacing-4);
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                    min-width: 120px;
                }

                .page-text {
                    font-weight: 500;
                    color: var(--gray-700);
                }

                .total-text {
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
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
                    <h3 class="card-title">${this.getCardTitle()}</h3>
                </div>
                <div id="pagination-placeholder"></div>
                <div class="card-body">
                    <div class="post-list">
                        <div class="post-item">
                            <div class="post-avatar"><span>加</span></div>
                            <div class="post-content">
                                <p class="post-excerpt">${this.loading ? '正在加载博文...' : '暂无博文'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    loadPageSizeConfig() {
        fetch('/api/config/app')
            .then(response => response.json())
            .then(config => {
                // 使用BLOG_POSTS_PAGE_SIZE环境变量对应的配置参数覆盖默认值
                // 环境变量: BLOG_POSTS_PAGE_SIZE -> API配置键: blog_posts_page_size
                this.pageSize = config.blog_posts_page_size || 10;
        
            })
            .catch(error => {
                console.warn('⚠️ 加载应用配置失败，使用默认pagesize=10:', error);
            });
    }
}

customElements.define('blog-list-card', BlogListCard); 