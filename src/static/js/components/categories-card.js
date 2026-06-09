/**
 * 分类列表卡片组件
 * 显示文章的分类列表
 */
class CategoriesCard extends BaseComponent {
    constructor() {
        super();
        this.categories = [];
        this.loading = true;
        this.isOwner = false;
        this.projectId = null;
    }

    async connectedCallback() {
        this.render();
        await Promise.all([this.checkOwnership(), this.loadData()]);
        this.render();
    }

    async checkOwnership() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            this.isOwner = false;
            return;
        }

        // 如果未登录，不是所有者
        if (!UserManager.isLoggedIn()) {
            this.isOwner = false;
            return;
        }

        // 获取项目ID
        this.projectId = this.getProjectIdFromUrl();
        if (!this.projectId) {
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

    addEventListeners() {
        // 延迟添加事件监听器，确保DOM已经渲染
        setTimeout(() => {
            const categoryLinks = this.shadowRoot.querySelectorAll('.category-link');
            categoryLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const folderId = link.getAttribute('data-folder-id');
                    const folderName = link.getAttribute('data-folder-name');
                    this.handleCategoryClick(folderId, folderName);
                });
            });
        }, 100);
    }

    handleCategoryClick(folderId, folderName) {
        const url = FolderFilter.syncFolderIdToUrl(folderId);
        url.searchParams.delete('page');
        window.history.pushState({}, '', url);

        this.notifyBlogPostsList(folderId, folderName);
        
        // 更新分类卡片的激活状态
        this.updateActiveCategory(folderId);
    }

    notifyBlogPostsList(folderId, folderName) {
        const detail = { folderId, folderName };
        const event = new CustomEvent('categoryChanged', { detail });
        const blogPostsListCard = document.querySelector('blog-posts-list-card');
        if (blogPostsListCard) {
            blogPostsListCard.dispatchEvent(event);
            const innerCard = blogPostsListCard.shadowRoot?.querySelector('blog-list-card[show-category]');
            if (innerCard) {
                innerCard.dispatchEvent(new CustomEvent('categoryChanged', { detail }));
            }
        }
    }

    updateActiveCategory(folderId) {
        const categoryLinks = this.shadowRoot.querySelectorAll('.category-link');
        categoryLinks.forEach((link) => {
            const linkFolderId = link.getAttribute('data-folder-id');
            const isActive = folderId === '' || folderId === null || folderId === undefined
                ? linkFolderId === ''
                : String(linkFolderId) === String(folderId);
            link.classList.toggle('active', isActive);
        });
    }

    async loadData() {
        // 检测是否在博客页面
        const isBlogPage = this.isBlogPage();
        let apiUrl;
        
        if (isBlogPage) {
            // 在博客页面：获取当前博客的分类
            const projectId = this.getProjectIdFromUrl();
            if (projectId) {
                apiUrl = `/api/projects/${projectId}/categories`;
            } else {
                this.showError('无法获取博客ID');
                return;
            }
        } else {
            // 在首页：获取全站分类（如果有的话）
            // 目前使用模拟数据，后续可以添加全站分类API
            this.categories = this.getMockCategories();
            this.loading = false;
            this.render();
            return;
        }

        try {
            // 获取分类数据
            const response = await fetch(apiUrl);
            if (response.ok) {
                this.categories = await response.json();
            } else if (response.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                // 如果API不存在，使用模拟数据
                this.categories = this.getMockCategories();
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            this.categories = this.getMockCategories();
        } finally {
            this.loading = false;
            this.render();
            setTimeout(() => this.addEventListeners(), 100);
        }
    }

    /**
     * 检测是否在博客页面
     * @returns {boolean} 是否在博客页面
     */
    isBlogPage() {
        const path = window.location.pathname;
        return path.startsWith('/blog/');
    }

    getProjectIdFromUrl() {
        // 使用基类的统一方法
        return this.getProjectId();
    }

    getMockCategories() {
        return [
            { id: 1, name: '技术分享', count: 15, color: '#3b82f6' },
            { id: 2, name: '生活随笔', count: 8, color: '#10b981' },
            { id: 3, name: '读书笔记', count: 12, color: '#f59e0b' },
            { id: 4, name: '旅行记录', count: 6, color: '#8b5cf6' },
            { id: 5, name: '美食分享', count: 4, color: '#ef4444' }
        ];
    }

    isCategoryActive(folderId) {
        const current = FolderFilter.normalizeFolderId(this.getCurrentFolderId());
        if (folderId === '' || folderId === null || folderId === undefined) {
            return current === null;
        }
        return String(current) === String(folderId);
    }

    renderCategoryLink({ folderId, folderName, count, color, countLabel }) {
        const safeName = this.escapeHtml(folderName);
        const safeColor = this.escapeHtml(color || '#94a3b8');
        const activeClass = this.isCategoryActive(folderId) ? ' active' : '';
        const countText = countLabel ?? this.escapeHtml(String(count ?? 0));

        return `
            <li class="category-item">
                <a href="#"
                   class="category-link${activeClass}"
                   data-folder-id="${folderId}"
                   data-folder-name="${safeName}">
                    <span class="category-info">
                        <span class="category-indicator" style="color: ${safeColor}; background-color: ${safeColor};" aria-hidden="true"></span>
                        <span class="category-name">${safeName}</span>
                    </span>
                    <span class="category-count">${countText}</span>
                </a>
            </li>
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

                .card-title :is(svg, .title-icon) {
                    width: 18px;
                    height: 18px;
                    color: var(--primary-color);
                    flex-shrink: 0;
                }

                .categories-body {
                    padding: var(--spacing-2) var(--spacing-3) var(--spacing-3);
                }

                .categories-toolbar {
                    margin-bottom: var(--spacing-2);
                    padding-bottom: var(--spacing-2);
                    border-bottom: 1px solid var(--gray-100);
                }

                .maintain-button {
                    width: 100%;
                }

                .maintain-button .btn-icon {
                    width: 14px;
                    height: 14px;
                    flex-shrink: 0;
                }

                .categories-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    flex-direction: column;
                    gap: calc(var(--spacing-1) + 1px);
                }

                .category-link {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: var(--spacing-2);
                    padding: var(--spacing-2) var(--spacing-3);
                    border: 1px solid transparent;
                    border-radius: var(--radius-md);
                    color: var(--gray-700);
                    text-decoration: none;
                    font-size: var(--font-size-sm);
                    line-height: 1.35;
                    transition:
                        background-color var(--transition-fast),
                        border-color var(--transition-fast),
                        color var(--transition-fast),
                        box-shadow var(--transition-fast);
                }

                .category-link:hover {
                    background: var(--gray-50);
                    border-color: var(--gray-200);
                    color: var(--gray-900);
                }

                .category-link:focus {
                    outline: none;
                }

                .category-link:focus-visible {
                    outline: 2px solid var(--primary-color);
                    outline-offset: 1px;
                }

                .category-link.active {
                    background: #eff6ff;
                    border-color: #bfdbfe;
                    color: var(--primary-color);
                    box-shadow: var(--shadow-sm);
                }

                .category-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    min-width: 0;
                    flex: 1;
                }

                .category-indicator {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    opacity: 0.9;
                }

                .category-link.active .category-indicator {
                    box-shadow: 0 0 0 2px #eff6ff;
                }

                .category-name {
                    font-weight: 500;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .category-link.active .category-name {
                    font-weight: 600;
                    color: var(--primary-color);
                }

                .category-count {
                    flex-shrink: 0;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 1.75rem;
                    padding: 0.125rem 0.5rem;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    font-variant-numeric: tabular-nums;
                    color: var(--gray-500);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-full);
                    line-height: 1.3;
                }

                .category-link:hover .category-count {
                    background: var(--white);
                    border-color: var(--gray-300);
                    color: var(--gray-600);
                }

                .category-link.active .category-count {
                    background: var(--white);
                    border-color: #93c5fd;
                    color: var(--primary-color);
                }

                .loading,
                .empty-state,
                .error {
                    text-align: center;
                    padding: var(--spacing-4) var(--spacing-2);
                    color: var(--gray-500);
                    font-size: var(--font-size-sm);
                }

                .error {
                    color: var(--error-color);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.categories}
                        分类列表
                    </h3>
                </div>
                <div class="categories-body">
                    ${this.isOwner ? this.renderMaintainButton() : ''}
                    ${this.loading ? this.renderLoading() :
                      this.categories.length > 0 ? this.renderCategories() :
                      this.renderEmptyState()}
                </div>
            </div>
        `;
    }

    renderLoading() {
        return `
            <div class="loading">
                <div>加载中...</div>
            </div>
        `;
    }

    renderCategories() {
        return `
            <ul class="categories-list">
                ${this.renderCategoryLink({
                    folderId: '',
                    folderName: '全部文章',
                    color: '#64748b',
                    countLabel: '全部'
                })}
                ${this.categories.map((category) => this.renderCategoryLink({
                    folderId: category.id,
                    folderName: category.name,
                    count: category.count,
                    color: category.color
                })).join('')}
            </ul>
        `;
    }

    renderEmptyState() {
        return `
            <div class="empty-state">
                <div>暂无分类</div>
            </div>
        `;
    }

    renderError() {
        return `
            <div class="error">
                <div>加载失败</div>
            </div>
        `;
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }

    getCurrentFolderId() {
        const url = new URL(window.location);
        return url.searchParams.get('folderid');
    }

    renderMaintainButton() {
        return `
            <div class="categories-toolbar">
                <button type="button" class="btn btn-secondary btn-sm maintain-button" onclick="this.getRootNode().host.goToMaintenance()">
                    <svg class="btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                    <span>维护分类</span>
                </button>
            </div>
        `;
    }

    goToMaintenance() {
        if (this.projectId) {
            window.open(`/blog/${this.projectId}/categories/maintenance`, '_blank');
        }
    }
}

customElements.define('categories-card', CategoriesCard);
