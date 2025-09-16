/**
 * 分类列表卡片组件
 * 显示文章的分类列表
 */
class CategoriesCard extends BaseComponent {
    constructor() {
        super();
        this.categories = [];
        this.loading = true;
    }

    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */


    connectedCallback() {
        this.render();
        this.loadData();
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
            // 延迟添加事件监听器，确保DOM已经渲染
            setTimeout(() => {
                this.addEventListeners();
            }, 100);
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
                    margin-bottom: var(--spacing-6);
                }

                .card-header {
                    padding: var(--spacing-4) var(--spacing-6);
                    background: var(--gray-50);
                    border-bottom: 1px solid var(--gray-200);
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
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.categories}
                        分类列表
                    </h3>
                </div>
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
}

customElements.define('categories-card', CategoriesCard);
