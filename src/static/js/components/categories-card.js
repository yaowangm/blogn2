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
        // 更新URL参数
        const url = new URL(window.location);
        if (folderId) {
            url.searchParams.set('folderid', folderId);
        } else {
            url.searchParams.delete('folderid');
        }
        url.searchParams.delete('page'); // 重置页码
        window.history.pushState({}, '', url);
        
        // 通知博客文章列表卡片更新
        this.notifyBlogPostsList(folderId, folderName);
        
        // 更新分类卡片的激活状态
        this.updateActiveCategory(folderId);
    }

    notifyBlogPostsList(folderId, folderName) {
        // 查找博客文章列表卡片并通知它更新
        const blogPostsListCard = document.querySelector('blog-posts-list-card');
        if (blogPostsListCard) {
            // 触发自定义事件
            const event = new CustomEvent('categoryChanged', {
                detail: { folderId, folderName }
            });
            blogPostsListCard.dispatchEvent(event);
        }
    }

    updateActiveCategory(folderId) {
        // 更新分类卡片的激活状态
        const categoryLinks = this.shadowRoot.querySelectorAll('.category-link');
        categoryLinks.forEach(link => {
            const currentFolderId = link.getAttribute('data-folder-id');
            if (currentFolderId === folderId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
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

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-xl);
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    margin-bottom: var(--card-margin);
                }

                .card-header {
                    padding: var(--spacing-4) var(--spacing-6);
                    background: var(--gray-50);
                    border-bottom: 1px solid var(--gray-200);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .card-title {
                    margin: 0;
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-800);
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .categories-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .category-item {
                    border-bottom: 1px solid var(--gray-100);
                }

                .category-item:last-child {
                    border-bottom: none;
                }

                .category-link {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: var(--spacing-4) var(--spacing-6);
                    color: var(--gray-700);
                    text-decoration: none;
                    transition: var(--transition-fast);
                    font-size: var(--font-size-sm);
                }

                .category-link:hover {
                    background: var(--gray-50);
                    color: var(--primary-color);
                }

                .category-link.active {
                    background: var(--primary-color);
                    color: var(--white);
                }

                .category-link.active .category-count {
                    background: var(--white);
                    color: var(--primary-color);
                }

                .category-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }

                .category-color {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    flex-shrink: 0;
                }

                .category-name {
                    font-weight: 500;
                }

                .category-count {
                    background: var(--gray-100);
                    color: var(--gray-600);
                    font-size: var(--font-size-xs);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-full);
                    font-weight: 500;
                    min-width: 24px;
                    text-align: center;
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .error {
                    text-align: center;
                    padding: var(--spacing-6);
                    color: var(--error-color);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }

                .empty-state {
                    text-align: center;
                    padding: var(--spacing-6);
                    color: var(--gray-500);
                }

                .maintain-button {
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    padding: var(--spacing-2) var(--spacing-4);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    margin: var(--spacing-3) var(--spacing-6) var(--spacing-4) var(--spacing-6);
                }

                .maintain-button:hover {
                    background: var(--primary-hover);
                    transform: translateY(-1px);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.categories}
                        分类列表
                    </h3>
                </div>
                ${this.isOwner ? this.renderMaintainButton() : ''}
                ${this.loading ? this.renderLoading() : 
                  this.categories.length > 0 ? this.renderCategories() : 
                  this.renderEmptyState()}
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
                <li class="category-item">
                    <a href="#" class="category-link ${!this.getCurrentFolderId() ? 'active' : ''}" data-folder-id="" data-folder-name="全部文章">
                        <div class="category-info">
                            <div class="category-color" style="background-color: #6b7280"></div>
                            <span class="category-name">全部文章</span>
                        </div>
                        <span class="category-count">全部</span>
                    </a>
                </li>
                ${this.categories.map(category => {
                    // 安全处理所有文本字段，防止HTML注入和XSS攻击
                    const safeName = this.escapeHtml(category.name);
                    const safeColor = this.escapeHtml(category.color);
                    const safeCount = this.escapeHtml(category.count);
                    
                    return `
                        <li class="category-item">
                            <a href="#" class="category-link ${this.getCurrentFolderId() == category.id ? 'active' : ''}" data-folder-id="${category.id}" data-folder-name="${safeName}">
                                <div class="category-info">
                                    <div class="category-color" style="background-color: ${safeColor}"></div>
                                    <span class="category-name">${safeName}</span>
                                </div>
                                <span class="category-count">${safeCount}</span>
                            </a>
                        </li>
                    `;
                }).join('')}
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
            <button class="maintain-button" onclick="this.getRootNode().host.goToMaintenance()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
                维护分类
            </button>
        `;
    }

    goToMaintenance() {
        if (this.projectId) {
            window.open(`/blog/${this.projectId}/categories/maintenance`, '_blank');
        }
    }
}

customElements.define('categories-card', CategoriesCard);
