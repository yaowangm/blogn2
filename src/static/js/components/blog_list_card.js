class BlogListCard extends BaseComponent {
    static get CATEGORY_MENU_PANEL_ID() {
        return 'blogn-category-menu-panel';
    }

    static get CATEGORY_MENU_STYLE_ID() {
        return 'blogn-category-menu-styles';
    }

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
        this.categories = [];
        this.categoriesLoading = false;
        this.categoryMenuOpen = false;
        this.isOwner = false;
        this.projectId = null;
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
        const initialPage = typeof this.getCurrentPageFromUrl === 'function' ? this.getCurrentPageFromUrl() : 1;
        this.currentPage = initialPage;
        this._shellRendered = false;

        const bootTasks = [this.loadPageSizeConfig()];
        if (this.showCategoryInfo) {
            this.projectId = this.getProjectIdFromUrl();
            this.setupCategoryMenuDismiss();
            bootTasks.push(this.checkOwnership(), this.loadCategories());
        }

        this.render();
        this._shellRendered = true;
        this.loadContent(initialPage);
        Promise.all(bootTasks).catch((error) => {
            console.warn('博客列表初始化任务失败:', error);
        });
        this.addEventListeners();
    }

    disconnectedCallback() {
        if (this._boundDocumentClick) {
            document.removeEventListener('click', this._boundDocumentClick);
            this._boundDocumentClick = null;
        }
        if (this._boundDocumentKeydown) {
            document.removeEventListener('keydown', this._boundDocumentKeydown);
            this._boundDocumentKeydown = null;
        }
        if (this._boundCategoryMenuLayout) {
            window.removeEventListener('resize', this._boundCategoryMenuLayout);
            window.removeEventListener('scroll', this._boundCategoryMenuLayout, true);
            this._boundCategoryMenuLayout = null;
        }
        this.removeCategoryMenuPortal();
    }

    setupCategoryMenuDismiss() {
        if (this._boundDocumentClick) {
            return;
        }
        this._boundDocumentClick = (event) => {
            if (!this.categoryMenuOpen) {
                return;
            }
            const path = event.composedPath();
            if (path.includes(this)) {
                return;
            }
            const panel = document.getElementById(BlogListCard.CATEGORY_MENU_PANEL_ID);
            if (panel && path.includes(panel)) {
                return;
            }
            this.closeCategoryMenu();
        };
        this._boundDocumentKeydown = (event) => {
            if (event.key === 'Escape' && this.categoryMenuOpen) {
                this.closeCategoryMenu();
            }
        };
        document.addEventListener('click', this._boundDocumentClick);
        document.addEventListener('keydown', this._boundDocumentKeydown);
    }

    async checkOwnership() {
        if (typeof UserManager === 'undefined' || !UserManager.isLoggedIn() || !this.projectId) {
            this.isOwner = false;
            return;
        }
        try {
            const blogData = await BaseComponent.getProject(this.projectId);
            if (blogData) {
                const currentUser = UserManager.getCurrentUser();
                this.isOwner = currentUser.id === blogData.userid;
            } else {
                this.isOwner = false;
            }
        } catch (error) {
            console.error('检查所有权失败:', error);
            this.isOwner = false;
        }
    }

    async loadCategories() {
        if (!this.projectId) {
            return;
        }
        this.categoriesLoading = true;
        if (this.categoryMenuOpen) {
            this.updateCategoryMenuPortal();
        }
        try {
            const response = await fetch(`/api/projects/${this.projectId}/categories`);
            if (response.ok) {
                this.categories = await response.json();
            } else {
                this.categories = [];
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            this.categories = [];
        } finally {
            this.categoriesLoading = false;
            this.updatePagination();
            if (this.categoryMenuOpen) {
                this.updateCategoryMenuPortal();
            }
        }
    }

    ensureCategoryMenuPortalStyles() {
        if (document.getElementById(BlogListCard.CATEGORY_MENU_STYLE_ID)) {
            return;
        }
        const style = document.createElement('style');
        style.id = BlogListCard.CATEGORY_MENU_STYLE_ID;
        style.textContent = `
            .blogn-category-menu-panel {
                position: fixed;
                z-index: 1000;
                min-width: 14rem;
                max-width: min(20rem, calc(100vw - 2rem));
                max-height: min(20rem, calc(100vh - 6rem));
                overflow-y: auto;
                background: var(--white, #fff);
                border: 1px solid var(--gray-200, #e5e7eb);
                border-radius: var(--radius-md, 0.375rem);
                box-shadow: var(--shadow-md, 0 4px 6px -1px rgb(0 0 0 / 0.1));
                padding: var(--spacing-2, 0.5rem);
                box-sizing: border-box;
            }
            .blogn-category-menu-panel .category-dropdown-loading {
                padding: var(--spacing-3, 0.75rem);
                text-align: center;
                color: var(--gray-500, #6b7280);
                font-size: var(--font-size-sm, 0.875rem);
            }
            .blogn-category-menu-panel .category-dropdown-header {
                margin-bottom: var(--spacing-2, 0.5rem);
            }
            .blogn-category-menu-panel .category-dropdown-divider {
                height: 1px;
                margin: 0 0 var(--spacing-2, 0.5rem);
                background: var(--gray-100, #f3f4f6);
            }
            .blogn-category-menu-panel .categories-list {
                list-style: none;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                gap: calc(var(--spacing-1, 0.25rem) + 1px);
            }
            .blogn-category-menu-panel .category-link {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: var(--spacing-2, 0.5rem);
                padding: var(--spacing-2, 0.5rem) var(--spacing-3, 0.75rem);
                border: 1px solid transparent;
                border-radius: var(--radius-md, 0.375rem);
                color: var(--gray-700, #374151);
                text-decoration: none;
                font-size: var(--font-size-sm, 0.875rem);
                line-height: 1.35;
                transition:
                    background-color var(--transition-fast, 150ms ease),
                    border-color var(--transition-fast, 150ms ease),
                    color var(--transition-fast, 150ms ease),
                    box-shadow var(--transition-fast, 150ms ease);
            }
            .blogn-category-menu-panel .category-link:hover {
                background: var(--gray-50, #f9fafb);
                border-color: var(--gray-200, #e5e7eb);
                color: var(--gray-900, #111827);
            }
            .blogn-category-menu-panel .category-link:focus {
                outline: none;
            }
            .blogn-category-menu-panel .category-link:focus-visible {
                outline: 2px solid var(--primary-color, #2f6fd6);
                outline-offset: 1px;
            }
            .blogn-category-menu-panel .category-link.active {
                background: #eff6ff;
                border-color: #bfdbfe;
                color: var(--primary-color, #2f6fd6);
                box-shadow: var(--shadow-sm, 0 1px 2px 0 rgb(0 0 0 / 0.05));
            }
            .blogn-category-menu-panel .category-info {
                display: flex;
                align-items: center;
                gap: var(--spacing-2, 0.5rem);
                min-width: 0;
                flex: 1;
            }
            .blogn-category-menu-panel .category-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                flex-shrink: 0;
                opacity: 0.9;
            }
            .blogn-category-menu-panel .category-link.active .category-indicator {
                box-shadow: 0 0 0 2px #eff6ff;
            }
            .blogn-category-menu-panel .category-name {
                font-weight: 500;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .blogn-category-menu-panel .category-link.active .category-name {
                font-weight: 600;
                color: var(--primary-color, #2f6fd6);
            }
            .blogn-category-menu-panel .category-count {
                flex-shrink: 0;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 1.75rem;
                padding: 0.125rem 0.5rem;
                font-size: var(--font-size-xs, 0.75rem);
                font-weight: 600;
                font-variant-numeric: tabular-nums;
                color: var(--gray-500, #6b7280);
                background: var(--gray-50, #f9fafb);
                border: 1px solid var(--gray-200, #e5e7eb);
                border-radius: var(--radius-full, 9999px);
                line-height: 1.3;
            }
            .blogn-category-menu-panel .category-link:hover .category-count {
                background: var(--white, #fff);
                border-color: var(--gray-300, #d1d5db);
                color: var(--gray-600, #4b5563);
            }
            .blogn-category-menu-panel .category-link.active .category-count {
                background: var(--white, #fff);
                border-color: #93c5fd;
                color: var(--primary-color, #2f6fd6);
            }
            .blogn-category-menu-panel .category-maintain-link {
                display: flex;
                align-items: center;
                gap: var(--spacing-2, 0.5rem);
                padding: var(--spacing-2, 0.5rem) var(--spacing-3, 0.75rem);
                border: 1px solid transparent;
                border-radius: var(--radius-md, 0.375rem);
                color: var(--gray-700, #374151);
                text-decoration: none;
                font-size: var(--font-size-sm, 0.875rem);
                font-weight: 500;
                transition:
                    background-color var(--transition-fast, 150ms ease),
                    border-color var(--transition-fast, 150ms ease),
                    color var(--transition-fast, 150ms ease);
            }
            .blogn-category-menu-panel .category-maintain-link:hover {
                background: var(--gray-50, #f9fafb);
                border-color: var(--gray-200, #e5e7eb);
                color: var(--gray-900, #111827);
            }
            .blogn-category-menu-panel .category-maintain-link:focus {
                outline: none;
            }
            .blogn-category-menu-panel .category-maintain-link:focus-visible {
                outline: 2px solid var(--primary-color, #2f6fd6);
                outline-offset: 1px;
            }
            .blogn-category-menu-panel .maintain-icon {
                flex-shrink: 0;
                color: var(--gray-500, #6b7280);
            }
        `;
        document.head.appendChild(style);
    }

    removeCategoryMenuPortal() {
        document.getElementById(BlogListCard.CATEGORY_MENU_PANEL_ID)?.remove();
        if (this._boundCategoryMenuLayout) {
            window.removeEventListener('resize', this._boundCategoryMenuLayout);
            window.removeEventListener('scroll', this._boundCategoryMenuLayout, true);
            this._boundCategoryMenuLayout = null;
        }
    }

    positionCategoryMenuPanel() {
        const trigger = this.shadowRoot?.querySelector('.category-picker-trigger');
        const panel = document.getElementById(BlogListCard.CATEGORY_MENU_PANEL_ID);
        if (!trigger || !panel) {
            return;
        }
        const rect = trigger.getBoundingClientRect();
        panel.style.top = `${Math.round(rect.bottom + 4)}px`;
        panel.style.right = `${Math.round(window.innerWidth - rect.right)}px`;
        panel.style.left = 'auto';
        panel.style.minWidth = `${Math.max(Math.round(rect.width), 224)}px`;
    }

    bindCategoryMenuPortalEvents(panel) {
        panel.querySelectorAll('.category-link').forEach((link) => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                this.handleCategorySelect(
                    link.getAttribute('data-folder-id'),
                    link.getAttribute('data-folder-name')
                );
            });
        });
        panel.querySelectorAll('.category-maintain-link').forEach((link) => {
            link.addEventListener('click', () => {
                this.closeCategoryMenu();
            });
        });
    }

    updateCategoryMenuPortal() {
        this.removeCategoryMenuPortal();
        if (!this.categoryMenuOpen) {
            return;
        }

        this.ensureCategoryMenuPortalStyles();

        const panel = document.createElement('div');
        panel.id = BlogListCard.CATEGORY_MENU_PANEL_ID;
        panel.className = 'blogn-category-menu-panel';
        panel.setAttribute('role', 'listbox');
        panel.innerHTML = this.categoriesLoading
            ? this.renderCategoryMenuLoading()
            : this.renderCategoryMenuList();
        document.body.appendChild(panel);

        this.positionCategoryMenuPanel();
        this.bindCategoryMenuPortalEvents(panel);

        if (!this._boundCategoryMenuLayout) {
            this._boundCategoryMenuLayout = () => {
                if (this.categoryMenuOpen) {
                    this.positionCategoryMenuPanel();
                }
            };
            window.addEventListener('resize', this._boundCategoryMenuLayout);
            window.addEventListener('scroll', this._boundCategoryMenuLayout, true);
        }
    }

    isCategoryActive(folderId) {
        const current = FolderFilter.normalizeFolderId(this.currentFolderId);
        if (folderId === '' || folderId === null || folderId === undefined) {
            return current === null;
        }
        return String(current) === String(folderId);
    }

    renderCategoryMenuItem({ folderId, folderName, count, color, countLabel }) {
        const safeName = this.escapeHtml(folderName);
        const safeColor = this.escapeHtml(color || '#94a3b8');
        const activeClass = this.isCategoryActive(folderId) ? ' active' : '';
        const countText = countLabel ?? this.escapeHtml(String(count ?? 0));

        return `
            <li class="category-item">
                <a href="#"
                   class="category-link${activeClass}"
                   data-folder-id="${folderId}"
                   data-folder-name="${safeName}"
                   role="option"
                   aria-selected="${activeClass ? 'true' : 'false'}">
                    <span class="category-info">
                        <span class="category-indicator" style="color: ${safeColor}; background-color: ${safeColor};" aria-hidden="true"></span>
                        <span class="category-name">${safeName}</span>
                    </span>
                    <span class="category-count">${countText}</span>
                </a>
            </li>
        `;
    }

    renderCategoryMenuList() {
        const maintainLink = this.isOwner && this.projectId ? `
            <div class="category-dropdown-header">
                <a href="/blog/${this.projectId}/categories/maintenance"
                   target="_blank"
                   rel="noopener"
                   class="category-maintain-link">
                    <svg class="maintain-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span>维护分类</span>
                </a>
            </div>
            <div class="category-dropdown-divider"></div>
        ` : '';

        const items = [
            this.renderCategoryMenuItem({
                folderId: '',
                folderName: '全部文章',
                color: '#64748b',
                countLabel: '全部'
            }),
            ...this.categories.map((category) => this.renderCategoryMenuItem({
                folderId: category.id,
                folderName: category.name,
                count: category.count,
                color: category.color
            }))
        ].join('');

        return `
            ${maintainLink}
            <ul class="categories-list">${items}</ul>
        `;
    }

    renderCategoryMenuLoading() {
        return `<div class="category-dropdown-loading">加载中...</div>`;
    }

    renderCategoryPicker() {
        return `
            <div class="pagination">
                <div class="category-picker${this.categoryMenuOpen ? ' is-open' : ''}">
                    <button type="button"
                            class="category-picker-trigger"
                            aria-expanded="${this.categoryMenuOpen ? 'true' : 'false'}"
                            aria-haspopup="listbox">
                        <span class="category-label">分类：</span>
                        <span class="category-picker-name">${this.escapeHtml(this.currentCategoryName)}</span>
                        <svg class="category-picker-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }

    toggleCategoryMenu() {
        this.categoryMenuOpen = !this.categoryMenuOpen;
        this.updatePagination();
        this.updateCategoryMenuPortal();
    }

    closeCategoryMenu() {
        if (!this.categoryMenuOpen) {
            return;
        }
        this.categoryMenuOpen = false;
        this.updatePagination();
        this.removeCategoryMenuPortal();
    }

    handleCategorySelect(folderId, folderName) {
        const url = FolderFilter.syncFolderIdToUrl(folderId);
        url.searchParams.delete('page');
        window.history.pushState({}, '', url);

        this.currentFolderId = FolderFilter.normalizeFolderId(folderId);
        this.currentCategoryName = FolderFilter.getCategoryLabel(folderId, null, folderName);
        this.currentPage = 1;
        this.closeCategoryMenu();

        const host = this.getRootNode().host;
        if (host && host !== this) {
            host.currentFolderId = this.currentFolderId;
            host.currentCategoryName = this.currentCategoryName;
            host.currentPage = 1;
        }

        this.loadContent(1);
    }

    bindCategoryMenuEvents() {
        const trigger = this.shadowRoot.querySelector('.category-picker-trigger');
        if (trigger && !trigger._categoryMenuBound) {
            trigger._categoryMenuBound = true;
            trigger.addEventListener('click', (event) => {
                event.stopPropagation();
                this.toggleCategoryMenu();
            });
        }
    }

    addEventListeners() {
        // 监听分类变化事件
        this.addEventListener('categoryChanged', (event) => {
            const { folderId, folderName } = event.detail;
            this.currentFolderId = FolderFilter.normalizeFolderId(folderId);
            this.currentCategoryName = FolderFilter.getCategoryLabel(folderId, null, folderName);
            this.currentPage = 1;
            this.closeCategoryMenu();
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
            if (!this._shellRendered) {
                this.render();
                this._shellRendered = true;
            } else {
                this.showListLoading();
            }
            
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
                const excerpt = post.excerpt || post.comment || '';
                const image = post.image || (post.attachment ? `/upload/${post.attachment}` : null);
                const safeTitle = this.escapeHtml(title);
                const safeExcerpt = this.escapeHtml(
                    post.excerpt ? excerpt : this.stripMarkdown(excerpt)
                );

                return `
                    <a href="/article/${post.id}" class="post-item" target="_blank">
                        <div class="post-content">
                            <h4 class="post-title">${safeTitle}</h4>
                            ${this.renderPostMeta(post)}
                            <p class="post-excerpt">${safeExcerpt}</p>
                        </div>
                        ${image ? `<div class="post-attachment-image"><img src="${image}" alt="${safeTitle}" loading="lazy" onerror="this.style.display='none'"></div>` : ''}
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
            innerHtml += this.renderCategoryPicker();
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
        if (this.showCategoryInfo) {
            this.bindCategoryMenuEvents();
        }
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

                .post-item:hover,
                .post-item:focus-visible {
                    background: var(--interactive-hover-bg);
                    border-color: var(--interactive-hover-border);
                    box-shadow: none;
                }

                .post-item:hover .post-title,
                .post-item:focus-visible .post-title {
                    color: var(--interactive-hover-text);
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
                    transition: color var(--transition-fast);
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

                .category-picker {
                    position: relative;
                }

                .category-picker-trigger {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    background: var(--gray-100);
                    padding: var(--spacing-1) var(--spacing-2);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    cursor: pointer;
                    transition:
                        background-color var(--transition-fast),
                        border-color var(--transition-fast),
                        box-shadow var(--transition-fast);
                }

                .category-picker-trigger:hover {
                    background: var(--white);
                    border-color: var(--gray-300);
                }

                .category-picker-trigger:focus {
                    outline: none;
                }

                .category-picker-trigger:focus-visible {
                    outline: 2px solid var(--primary-color);
                    outline-offset: 1px;
                }

                .category-picker.is-open .category-picker-trigger {
                    background: var(--white);
                    border-color: var(--primary-color);
                    box-shadow: var(--shadow-sm);
                }

                .category-label {
                    font-weight: 500;
                }

                .category-picker-name {
                    font-weight: 600;
                    color: var(--primary-color);
                    max-width: 8rem;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .category-picker-chevron {
                    flex-shrink: 0;
                    color: var(--gray-500);
                    transition: transform var(--transition-fast);
                }

                .category-picker.is-open .category-picker-chevron {
                    transform: rotate(180deg);
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

    showListLoading() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = `
                <div class="post-list">
                    <div class="post-item">
                        <div class="post-content">
                            <p class="post-excerpt">正在加载博文...</p>
                        </div>
                    </div>
                </div>
            `;
        }
        this.updatePagination();
    }

    async loadPageSizeConfig() {
        try {
            const config = await BaseComponent.getAppConfig();
            this.pageSize = config.blog_posts_page_size || 10;
        } catch (error) {
            console.warn('⚠️ 加载应用配置失败，使用默认pagesize=10:', error);
        }
    }
}

customElements.define('blog-list-card', BlogListCard); 