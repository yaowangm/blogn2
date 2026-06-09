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

    static get ICON_STROKE() {
        return 'currentColor';
    }

    getMetaIcon(type) {
        const s = BlogListCard.ICON_STROKE;
        const svg = (paths) =>
            `<svg class="meta-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        switch (type) {
            case 'category':
                return svg('<path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 0 1 0 2.828l-7 7a2 2 0 0 1-2.828 0l-7-7A1.994 1.994 0 0 1 3 12V7a4 4 0 0 1 4-4z"/>');
            case 'created':
                return svg('<path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>');
            case 'blog':
                return svg('<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>');
            default:
                return svg('<circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>');
        }
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

    getPostCategoryName(post) {
        if (!this.showCategoryInfo) {
            return '';
        }
        const raw = typeof post.category === 'object' ? post.category?.name : post.category;
        if (!raw) {
            return '';
        }
        const name = String(raw).trim();
        if (!name || name === '全部文章') {
            return '';
        }
        return name;
    }

    renderPostMeta(post) {
        const authorName = post.author || post.author_name || '未知作者';
        const createDate = post.createtime
            ? this.formatDate(post.createtime)
            : this.escapeHtml(post.time || '未知时间');
        const categoryName = this.getPostCategoryName(post);
        const safeCategory = categoryName ? this.escapeHtml(categoryName) : '';
        const safeBlogName = post.blog_name ? this.escapeHtml(post.blog_name) : '';
        const showBlogSource = safeBlogName && !this.isBlogPage();

        return `
            <div class="article-meta">
                <div class="meta-items-left">
                    ${this.renderAuthorMetaItem(authorName, post.avatar, post.userid)}
                    <div class="meta-item">
                        ${this.getMetaIcon('created')}
                        <span>发布于 ${createDate}</span>
                    </div>
                    ${showBlogSource ? `
                        <div class="meta-item">
                            ${this.getMetaIcon('blog')}
                            <span>${safeBlogName}</span>
                        </div>
                    ` : ''}
                    ${safeCategory ? `
                        <div class="meta-item">
                            ${this.getMetaIcon('category')}
                            <span>${safeCategory}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
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
                const title = post.title || post.name;
                const excerpt = post.comment || post.excerpt || '';
                const image = post.image || (post.attachment ? `/upload/${post.attachment}` : null);
                const safeTitle = this.escapeHtml(title);
                const safeExcerpt = this.escapeHtml(this.stripMarkdown(excerpt));

                return `
                    <a href="/article/${post.id}" class="post-item" target="_blank">
                        <div class="post-content">
                            <h4 class="post-title">${safeTitle}</h4>
                            ${this.renderPostMeta(post)}
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
                    gap: calc(var(--spacing-2) + 2px);
                    max-width: 100%;
                    overflow: hidden;
                }

                .post-item {
                    display: grid;
                    grid-template-columns: 1fr;
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

                .post-content {
                    min-width: 0;
                    max-width: 100%;
                    overflow: hidden;
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

                .meta-icon {
                    display: block;
                    width: 18px;
                    height: 18px;
                    flex-shrink: 0;
                }

                .article-meta {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: var(--spacing-2) var(--spacing-3);
                    margin-bottom: var(--spacing-2);
                    padding-top: var(--spacing-1);
                }

                .meta-items-left {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: var(--spacing-3);
                    min-width: 0;
                }

                .meta-item {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                    white-space: nowrap;
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
                    font-weight: 500;
                    color: var(--gray-700);
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

                @media (max-width: 1024px) {
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