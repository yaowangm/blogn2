class NavigationCard extends BaseComponent {
    constructor() {
        super();
        this.mode = 'navigation'; // 'navigation' 或 'pagination'
        this.pagination = null;
        this.onPageChange = null;
    }

    static get observedAttributes() {
        return ['mode', 'pagination', 'on-page-change'];
    }

    connectedCallback() {
        this.render();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'mode') {
            this.mode = newValue || 'navigation';
            this.render();
        } else if (name === 'pagination' && newValue) {
            this.pagination = JSON.parse(newValue);
            this.render();
        }
    }

    setPagination(pagination, onPageChange) {
        this.mode = 'pagination';
        this.pagination = pagination;
        this.onPageChange = onPageChange;
        this.render();
    }

    render() {
        if (this.mode === 'pagination') {
            this.renderPagination();
        } else {
            this.renderNavigation();
        }
    }

    renderNavigation() {
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

                .nav-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-2);
                }

                .nav-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    transition: var(--transition-fast);
                    text-decoration: none;
                    color: var(--gray-700);
                }

                .nav-item:hover {
                    background: var(--gray-50);
                    color: var(--primary-color);
                }

                .nav-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--gray-500);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .nav-item:hover .nav-icon {
                    color: var(--primary-color);
                }

                .nav-text {
                    font-weight: 500;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">全站导航</h3>
                </div>
                <div class="card-body">
                    <div class="nav-list">
                        <a href="/users" class="nav-item">
                            <div class="nav-icon">${Icons.usersList}</div>
                            <span class="nav-text">用户列表</span>
                        </a>
                        <a href="/api/rss/site" class="nav-item" target="_blank">
                            <div class="nav-icon">${Icons.rss}</div>
                            <span class="nav-text">全站RSS</span>
                        </a>
                        <a href="/categories" class="nav-item">
                            <div class="nav-icon">${Icons.folder}</div>
                            <span class="nav-text">分类浏览</span>
                        </a>
                        <a href="/tags" class="nav-item">
                            <div class="nav-icon">${Icons.tag}</div>
                            <span class="nav-text">标签云</span>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination() {
        if (!this.pagination || this.pagination.total_pages <= 1) {
            this.shadowRoot.innerHTML = '';
            return;
        }

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .pagination-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: var(--spacing-2);
                    margin: var(--spacing-6) 0;
                    padding: var(--spacing-4);
                }

                .pagination-btn {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-2) var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    background: var(--white);
                    color: var(--gray-700);
                    text-decoration: none;
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    transition: var(--transition-fast);
                    cursor: pointer;
                    min-width: 40px;
                }

                .pagination-btn:hover:not(.disabled) {
                    background: var(--gray-50);
                    border-color: var(--gray-400);
                    color: var(--gray-900);
                }

                .pagination-btn.disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .pagination-btn.active {
                    background: var(--primary-color);
                    border-color: var(--primary-color);
                    color: var(--white);
                }

                .pagination-info {
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                    margin: 0 var(--spacing-4);
                }

                @media (max-width: 768px) {
                    .pagination-container {
                        flex-wrap: wrap;
                        gap: var(--spacing-1);
                    }

                    .pagination-info {
                        margin: var(--spacing-2) 0;
                        width: 100%;
                        text-align: center;
                    }
                }
            </style>

            <div class="pagination-container">
                ${this.renderPaginationButtons()}
                ${this.renderPaginationInfo()}
            </div>
        `;

        this.attachPaginationEventListeners();
    }

    renderPaginationButtons() {
        const { current_page, total_pages, has_prev, has_next } = this.pagination;
        
        let buttons = '';

        // 上一页按钮
        buttons += this.createPaginationButton(
            '上一页', 
            has_prev, 
            () => this.handlePageChange(current_page - 1)
        );

        // 页码按钮
        const startPage = Math.max(1, current_page - 2);
        const endPage = Math.min(total_pages, current_page + 2);

        if (startPage > 1) {
            buttons += this.createPaginationButton('1', true, () => this.handlePageChange(1));
            if (startPage > 2) {
                buttons += this.createPaginationButton('...', false);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === current_page;
            buttons += this.createPaginationButton(
                i.toString(), 
                true, 
                () => this.handlePageChange(i),
                isActive
            );
        }

        if (endPage < total_pages) {
            if (endPage < total_pages - 1) {
                buttons += this.createPaginationButton('...', false);
            }
            buttons += this.createPaginationButton(
                total_pages.toString(), 
                true, 
                () => this.handlePageChange(total_pages)
            );
        }

        // 下一页按钮
        buttons += this.createPaginationButton(
            '下一页', 
            has_next, 
            () => this.handlePageChange(current_page + 1)
        );

        return buttons;
    }

    renderPaginationInfo() {
        const { current_page, total_pages, total, total_count } = this.pagination;
        const count = total || total_count || 0;
        const itemType = this.pagination.item_type || '条记录';
        return `<div class="pagination-info">第 ${current_page} 页，共 ${total_pages} 页，总计 ${count} ${itemType}</div>`;
    }

    createPaginationButton(text, enabled, onClick, isActive = false) {
        const classes = `pagination-btn ${isActive ? 'active' : ''} ${!enabled ? 'disabled' : ''}`;
        const dataAction = enabled ? `data-action="${text}"` : '';
        
        return `<a href="#" class="${classes}" ${dataAction}>${text}</a>`;
    }

    attachPaginationEventListeners() {
        const buttons = this.shadowRoot.querySelectorAll('.pagination-btn[data-action]');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const action = button.getAttribute('data-action');
                this.handleButtonClick(action);
            });
        });
    }

    handleButtonClick(action) {
        const { current_page, total_pages } = this.pagination;
        
        switch (action) {
            case '上一页':
                this.handlePageChange(current_page - 1);
                break;
            case '下一页':
                this.handlePageChange(current_page + 1);
                break;
            default:
                // 页码按钮
                const page = parseInt(action);
                if (!isNaN(page) && page >= 1 && page <= total_pages) {
                    this.handlePageChange(page);
                }
                break;
        }
    }

    handlePageChange(page) {
        if (this.onPageChange) {
            this.onPageChange(page);
        }
        
        // 触发自定义事件
        this.dispatchEvent(new CustomEvent('page-change', {
            detail: { page },
            bubbles: true
        }));
    }
}

customElements.define('navigation-card', NavigationCard); 