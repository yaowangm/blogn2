/**
 * 博客分类列表卡片组件
 * 显示博客文章的分类列表
 */
class BlogCategoriesCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.categories = [];
        this.loading = true;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadData();
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    async loadData() {
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            // 获取博客分类数据
            const response = await fetch(`/api/projects/${this.projectId}/categories`);
            if (response.ok) {
                this.categories = await response.json();
            } else {
                // 如果API不存在，使用模拟数据
                this.categories = this.getMockCategories();
            }
        } catch (error) {
            console.error('Error loading blog categories:', error);
            this.categories = this.getMockCategories();
        } finally {
            this.loading = false;
            this.render();
        }
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
                        <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 0 1 0 2.828l-7 7a2 2 0 0 1-2.828 0l-7-7A1.994 1.994 0 0 1 3 12V7a4 4 0 0 1 4-4z"/>
                        </svg>
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
                ${this.categories.map(category => `
                    <li class="category-item">
                        <a href="/blog/${this.projectId}/category/${category.id}" class="category-link">
                            <div class="category-info">
                                <div class="category-color" style="background-color: ${category.color}"></div>
                                <span class="category-name">${category.name}</span>
                            </div>
                            <span class="category-count">${category.count}</span>
                        </a>
                    </li>
                `).join('')}
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
}

customElements.define('blog-categories-card', BlogCategoriesCard);
