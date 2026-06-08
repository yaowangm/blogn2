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

    async connectedCallback() {
        this.showCategoryInfo = this.shouldShowCategoryInfo();
        this.currentFolderId = FolderFilter.normalizeFolderId(this.getCurrentFolderId());
        this.currentCategoryName = FolderFilter.getCategoryLabel(this.currentFolderId);
        await this.loadPageSizeConfig();
        // 从 URL 读取 page，直接加载对应页（如 /blog/12?page=24 加载第 24 页）
        const initialPage = typeof this.getCurrentPageFromUrl === 'function' ? this.getCurrentPageFromUrl() : 1;
        this.currentPage = initialPage;
        this.render();
        this.loadContent(initialPage);
        this.addEventListeners();
    }

    addEventListeners() {
        // 监听分类变化事件
        this.addEventListener('categoryChanged', (event) => {
            const { folderId, folderName } = event.detail;
            this.currentFolderId = FolderFilter.normalizeFolderId(folderId);
            this.currentCategoryName = FolderFilter.getCategoryLabel(folderId, null, folderName);
            this.currentPage = 1;
            this.updatePagination();
            this.loadContent(1);
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
                        if (FolderFilter.shouldIncludeFolderInApi(this.currentFolderId)) {
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
        this.totalPosts = typeof data.total === 'number' ? data.total : this.posts.length;
        this.totalPages = typeof data.total_pages === 'number'
            ? data.total_pages
            : Math.ceil(this.totalPosts / this.pageSize);
        this.loading = false;
        this.currentCategoryName = FolderFilter.getCategoryLabel(
            this.currentFolderId,
            data.category
        );
        this.updatePagination();
        // 通知父级 blog-posts-list-card 同步总数，供分页校验
        const host = this.getRootNode().host;
        if (host && host !== this && typeof host.dispatchEvent === 'function') {
            host.dispatchEvent(new CustomEvent('blog-list-content-updated', {
                detail: { totalPosts: this.totalPosts, totalPages: this.totalPages },
                bubbles: true,
                composed: true
            }));
        }
        
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
                        </div>
                        ${image ? `<div class="post-attachment-image"><img src="${image}" alt="${safeTitle}" onerror="this.style.display='none'"></div>` : ''}
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
        let innerHtml = '';

        if (this.totalPages > 1) {
            const pagination = {
                current_page: this.currentPage,
                total_pages: this.totalPages,
                total: this.totalPosts,
                has_prev: this.currentPage > 1,
                has_next: this.currentPage < this.totalPages
            };

            innerHtml += `<navigation-card mode="pagination" compact pagination='${JSON.stringify(pagination)}'></navigation-card>`;
        }

        if (this.showCategoryInfo) {
            innerHtml += `
                <div class="pagination">
                    <div class="category-info">
                        <span class="category-label">分类：</span>
                        <span class="category-name">${this.escapeHtml(this.currentCategoryName)}</span>
                    </div>
                </div>
            `;
        }

        if (!innerHtml) {
            return '';
        }

        return `<div class="pagination-toolbar">${innerHtml}</div>`;
    }

    updatePagination() {
        const html = this.renderPagination();
        this.shadowRoot.querySelectorAll('.pagination-bar').forEach((placeholder) => {
            placeholder.innerHTML = html;
        });
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) return;
        
        // 更新URL参数
        const url = new URL(window.location);
        url.searchParams.set('page', page);
        if (FolderFilter.shouldIncludeFolderInApi(this.currentFolderId)) {
            url.searchParams.set('folderid', this.currentFolderId);
        } else {
            url.searchParams.delete('folderid');
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
                @import url('/static/css/common-components.css');

                :host {
                    display: block;
                }

                .card {
                    margin-bottom: 0;
                    max-width: 100%;
                    width: 100%;
                    transition: var(--transition-normal);
                }
                .pagination-bar {
                    max-width: 100%;
                    overflow: hidden;
                    margin: 0;
                    padding: var(--spacing-2) var(--spacing-4);
                    background: var(--gray-50);
                    box-sizing: border-box;
                }

                .pagination-bar--top {
                    border-bottom: 1px solid var(--gray-200);
                }

                .pagination-bar--bottom {
                    border-top: 1px solid var(--gray-200);
                }

                .pagination-bar:empty {
                    display: none;
                }

                .pagination-bar .pagination-toolbar {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: var(--spacing-2) var(--spacing-3);
                }

                .pagination-bar navigation-card {
                    flex: 1 1 auto;
                    min-width: min(100%, 16rem);
                    max-width: 100%;
                    margin: 0;
                }

                .pagination-bar .pagination {
                    flex: 0 0 auto;
                    margin: 0 0 0 auto;
                }

                .card-body {
                    max-width: 100%;
                    overflow: hidden;
                }

                .post-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-2);
                    max-width: 100%;
                    overflow: hidden;
                }

                .post-item {
                    display: grid;
                    grid-template-columns: 60px 1fr;
                    column-gap: var(--spacing-3);
                    row-gap: var(--spacing-3);
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
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
                    box-shadow: var(--shadow-sm);
                    border-color: var(--gray-300);
                }

                .post-item:focus {
                    outline: none;
                }

                .post-avatar {
                    grid-column: 1;
                    grid-row: 1;
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
                    font-size: var(--font-size-base);
                    overflow: hidden;
                    border: 2px solid var(--gray-200);
                    position: relative;
                    margin-top: 0;
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
                    grid-column: 2;
                    grid-row: 1;
                    min-width: 0;
                    max-width: 100%;
                    overflow: hidden;
                    /* 继承全局文本断行策略 */
                    /* 若common-components.css未作用于Shadow DOM，可用工具类兜底 */
                    /* 此处不重复具体规则，避免多层定义 */
                }

                .post-title {
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0 0 var(--spacing-1);
                    line-height: 1.4;
                    overflow: hidden;
                    max-width: 100%;
                }

                .post-meta {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-bottom: var(--spacing-1);
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
                    margin: 0;
                    max-width: 100%;
                    word-wrap: break-word;
                    word-break: break-word;
                    overflow-wrap: anywhere; /* 允许在任意位置断行，防止超长串撑破 */
                }

                .post-attachment-image {
                    grid-column: 2;
                    grid-row: 2;
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

                /* 单栏：头像左、正文右；配图占满卡片宽度 */
                @media (max-width: 1024px) {
                    .post-attachment-image {
                        grid-column: 1 / -1;
                    }

                    .post-attachment-image img {
                        max-width: 100%;
                        width: 100%;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">${this.getCardTitle()}</h3>
                </div>
                <div class="pagination-bar pagination-bar--top"></div>
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
                <div class="pagination-bar pagination-bar--bottom"></div>
            </div>
        `;
    }

    async loadPageSizeConfig() {
        try {
            const response = await fetch('/api/config/app');
            if (response.ok) {
                const config = await response.json();
                this.pageSize = config.blog_posts_page_size || 10;
            }
        } catch (error) {
            console.warn('⚠️ 加载应用配置失败，使用默认pagesize=10:', error);
        }
    }
}

customElements.define('blog-list-card', BlogListCard); 