/**
 * 分类维护卡片组件
 * 提供分类的增删改功能
 */
class CategoryMaintenanceCard extends BaseComponent {
    constructor() {
        super();
        this.categories = [];
        this.loading = true;
        this.projectId = null;
        this.editingCategory = null;
        this.showAddForm = false;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadData();
    }

    async loadData() {
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            const response = await fetch(`/api/projects/${this.projectId}/categories`);
            if (response.ok) {
                this.categories = await response.json();
            } else {
                this.showError('加载分类失败');
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            this.showError('加载分类失败');
        } finally {
            this.loading = false;
            this.render();
        }
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

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .add-button {
                    background: var(--primary-color);
                    color: white;
                    border: none;
                    padding: var(--spacing-2) var(--spacing-4);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-1);
                }

                .add-button:hover {
                    background: var(--primary-hover);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .category-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .category-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: var(--spacing-3) var(--spacing-4);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-lg);
                    margin-bottom: var(--spacing-3);
                    background: var(--white);
                    transition: all 0.2s ease;
                }

                .category-item:hover {
                    box-shadow: var(--shadow-sm);
                    border-color: var(--primary-color);
                }

                .category-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    flex: 1;
                }

                .category-color {
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    flex-shrink: 0;
                }

                .category-name {
                    font-weight: 500;
                    color: var(--gray-900);
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

                .category-actions {
                    display: flex;
                    gap: var(--spacing-2);
                }

                .action-button {
                    background: none;
                    border: 1px solid var(--gray-300);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-sm);
                    cursor: pointer;
                    font-size: var(--font-size-xs);
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-1);
                }

                .edit-button {
                    color: var(--primary-color);
                    border-color: var(--primary-color);
                }

                .edit-button:hover {
                    background: var(--primary-color);
                    color: white;
                }

                .delete-button {
                    color: var(--error-color);
                    border-color: var(--error-color);
                }

                .delete-button:hover {
                    background: var(--error-color);
                    color: white;
                }

                .add-form {
                    background: var(--gray-50);
                    padding: var(--spacing-4);
                    border-radius: var(--radius-lg);
                    margin-bottom: var(--spacing-4);
                    border: 1px solid var(--gray-200);
                }

                .form-group {
                    margin-bottom: var(--spacing-4);
                }

                .form-group label {
                    display: block;
                    margin-bottom: var(--spacing-1);
                    font-weight: 500;
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                }

                .form-group input {
                    width: 100%;
                    padding: var(--spacing-2) var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    box-sizing: border-box;
                }

                .form-group input:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
                }

                .form-actions {
                    display: flex;
                    gap: var(--spacing-2);
                    justify-content: flex-end;
                }

                .btn {
                    padding: var(--spacing-2) var(--spacing-4);
                    border: none;
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    transition: all 0.2s ease;
                }

                .btn-primary {
                    background: var(--primary-color);
                    color: white;
                }

                .btn-primary:hover {
                    background: var(--primary-hover);
                }

                .btn-secondary {
                    background: var(--gray-200);
                    color: var(--gray-700);
                }

                .btn-secondary:hover {
                    background: var(--gray-300);
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .error {
                    text-align: center;
                    padding: var(--spacing-3) var(--spacing-4);
                    color: var(--error-color);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }

                .empty-state {
                    text-align: center;
                    padding: var(--spacing-3) var(--spacing-4);
                    color: var(--gray-500);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2H5a2 2 0 0 0-2-2z"></path>
                            <path d="M8 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2H8V5z"></path>
                        </svg>
                        分类维护
                    </h3>
                    <button class="add-button" onclick="this.getRootNode().host.toggleAddForm()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 5v14M5 12h14"></path>
                        </svg>
                        添加分类
                    </button>
                </div>
                <div class="card-body">
                    ${this.loading ? this.renderLoading() : 
                      this.showAddForm ? this.renderAddForm() + this.renderCategoryList() :
                      this.renderCategoryList()}
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

    renderAddForm() {
        return `
            <div class="add-form">
                <div class="form-group">
                    <label for="category-name">分类名称</label>
                    <input type="text" id="category-name" placeholder="请输入分类名称" value="${this.editingCategory ? this.escapeHtml(this.editingCategory.name) : ''}">
                </div>
                <div class="form-actions">
                    <button class="btn btn-secondary" onclick="this.getRootNode().host.cancelEdit()">取消</button>
                    <button class="btn btn-primary" onclick="this.getRootNode().host.saveCategory()">
                        ${this.editingCategory ? '更新' : '添加'}
                    </button>
                </div>
            </div>
        `;
    }

    renderCategoryList() {
        if (this.categories.length === 0) {
            return `
                <div class="empty-state">
                    <div>暂无分类</div>
                </div>
            `;
        }

        return `
            <ul class="category-list">
                ${this.categories.map(category => {
                    const safeName = this.escapeHtml(category.name);
                    const safeColor = this.escapeHtml(category.color || '#6b7280');
                    const safeCount = this.escapeHtml(category.count || 0);
                    
                    return `
                        <li class="category-item">
                            <div class="category-info">
                                <div class="category-color" style="background-color: ${safeColor}"></div>
                                <span class="category-name">${safeName}</span>
                                <span class="category-count">${safeCount}</span>
                            </div>
                            <div class="category-actions">
                                <button class="action-button edit-button" onclick="this.getRootNode().host.editCategory(${category.id})">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                    </svg>
                                    编辑
                                </button>
                                <button class="action-button delete-button" onclick="this.getRootNode().host.deleteCategory(${category.id})">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                    删除
                                </button>
                            </div>
                        </li>
                    `;
                }).join('')}
            </ul>
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

    toggleAddForm() {
        this.showAddForm = !this.showAddForm;
        this.editingCategory = null;
        this.render();
    }

    editCategory(categoryId) {
        const category = this.categories.find(c => c.id === categoryId);
        if (category) {
            this.editingCategory = category;
            this.showAddForm = true;
            this.render();
        }
    }

    cancelEdit() {
        this.showAddForm = false;
        this.editingCategory = null;
        this.render();
    }

    async saveCategory() {
        const nameInput = this.shadowRoot.querySelector('#category-name');
        const name = nameInput.value.trim();
        
        if (!name) {
            alert('请输入分类名称');
            return;
        }

        try {
            const url = this.editingCategory 
                ? `/api/projects/${this.projectId}/categories/${this.editingCategory.id}`
                : `/api/projects/${this.projectId}/categories`;
            
            const method = this.editingCategory ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${UserManager.getAccessToken()}`
                },
                body: JSON.stringify({ name })
            });

            if (response.ok) {
                await this.loadData();
                this.cancelEdit();
                alert(this.editingCategory ? '分类更新成功' : '分类添加成功');
            } else {
                const error = await response.json();
                alert(error.detail || '操作失败');
            }
        } catch (error) {
            console.error('Save category error:', error);
            alert('操作失败，请重试');
        }
    }

    async deleteCategory(categoryId) {
        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '删除分类',
            message: '确定要删除这个分类吗？',
            danger: true,
        })) {
            return;
        }

        try {
            const response = await fetch(`/api/projects/${this.projectId}/categories/${categoryId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${UserManager.getAccessToken()}`
                }
            });

            if (response.ok) {
                await this.loadData();
                alert('分类删除成功');
            } else {
                const error = await response.json();
                alert(error.detail || '删除失败');
            }
        } catch (error) {
            console.error('Delete category error:', error);
            alert('删除失败，请重试');
        }
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)\/categories\/maintenance/);
        return match ? parseInt(match[1]) : null;
    }
}

customElements.define('category-maintenance-card', CategoryMaintenanceCard);
