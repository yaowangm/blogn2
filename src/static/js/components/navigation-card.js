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
    
    disconnectedCallback() {
        // 清理事件监听器，避免内存泄漏
        this.removePaginationEventListeners();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'mode') {
            this.mode = newValue || 'navigation';
            this.render();
        } else if (name === 'pagination' && newValue) {
            try {
                this.pagination = JSON.parse(newValue);
                this.render();
            } catch (error) {
                console.error('NavigationCard: Invalid pagination JSON:', error);
                this.pagination = null;
            }
        }
    }

    setPagination(pagination, onPageChange) {
        this.mode = 'pagination';
        this.pagination = pagination;
        this.onPageChange = onPageChange;
        this.render();
    }
    
    // 新增方法：设置导航项（保持向后兼容）
    setNavigationItems(items) {
        this.navigationItems = items;
        if (this.mode === 'navigation') {
            this.render();
        }
    }
    
    // 获取默认导航项
    getDefaultNavigationItems() {
        return [
            { href: '/users', text: '用户列表', icon: Icons.usersList, target: '' },
            { href: '/api/rss/site', text: '全站RSS', icon: Icons.rss, target: '_blank' },
            { href: '/categories', text: '分类浏览', icon: Icons.folder, target: '' },
            { href: '/tags', text: '标签云', icon: Icons.tag, target: '' },
            { href: '/messages', text: '留言本', icon: Icons.message, target: '_blank' }
        ];
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
                        ${this.renderNavigationItems()}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderNavigationItems() {
        const items = this.navigationItems || this.getDefaultNavigationItems();
        return items.map(item => `
            <a href="${item.href}" class="nav-item" ${item.target ? `target="${item.target}"` : ''}>
                <div class="nav-icon">${item.icon}</div>
                <span class="nav-text">${item.text}</span>
            </a>
        `).join('');
    }

    renderPagination() {
        if (!this.pagination || this.pagination.total_pages <= 1) {
            this.shadowRoot.innerHTML = '';
            return;
        }

        // 先移除旧的事件监听器，避免重复绑定
        this.removePaginationEventListeners();

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

            <nav class="pagination-container" role="navigation" aria-label="分页导航">
                ${this.renderPaginationButtons()}
                ${this.renderPaginationInfo()}
            </nav>
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
        return `<div class="pagination-info" role="status" aria-live="polite">第 ${current_page} 页，共 ${total_pages} 页，总计 ${count} ${itemType}</div>`;
    }

    createPaginationButton(text, enabled, onClick, isActive = false) {
        const classes = `pagination-btn ${isActive ? 'active' : ''} ${!enabled ? 'disabled' : ''}`;
        const dataAction = enabled ? `data-action="${text}"` : '';
        const ariaLabel = this.getPaginationButtonAriaLabel(text, isActive);
        
        return `<a href="#" class="${classes}" ${dataAction} aria-label="${ariaLabel}" role="button" tabindex="${enabled ? '0' : '-1'}">${text}</a>`;
    }
    
    getPaginationButtonAriaLabel(text, isActive) {
        if (text === '上一页') return '转到上一页';
        if (text === '下一页') return '转到下一页';
        if (text === '...') return '更多页码';
        if (isActive) return `当前第${text}页`;
        return `转到第${text}页`;
    }

    removePaginationEventListeners() {
        // 移除旧的事件监听器，避免重复绑定
        if (this.shadowRoot && this.handleClick && this.handleKeydown) {
            this.shadowRoot.removeEventListener('click', this.handleClick);
            this.shadowRoot.removeEventListener('keydown', this.handleKeydown);
        }
    }

    attachPaginationEventListeners() {
        // 先移除旧的事件监听器
        this.removePaginationEventListeners();
        
        // 绑定事件处理器到实例方法，便于清理
        this.handleClick = (e) => {
            if (e.target.classList.contains('pagination-btn') && e.target.hasAttribute('data-action')) {
                e.preventDefault();
                const action = e.target.getAttribute('data-action');
                this.handleButtonClick(action);
            }
        };
        
        this.handleKeydown = (e) => {
            if (e.target.classList.contains('pagination-btn') && e.target.hasAttribute('data-action')) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const action = e.target.getAttribute('data-action');
                    this.handleButtonClick(action);
                }
            }
        };
        
        // 使用事件委托提高性能
        this.shadowRoot.addEventListener('click', this.handleClick);
        
        // 添加键盘支持
        this.shadowRoot.addEventListener('keydown', this.handleKeydown);
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
        // 验证页码有效性
        if (!this.pagination || page < 1 || page > this.pagination.total_pages) {
            return;
        }
        
        // 调用回调函数（保持向后兼容）
        if (this.onPageChange) {
            this.onPageChange(page);
        }
        
        // 触发自定义事件，使用composed: true让事件能够穿越Shadow DOM边界
        // 事件会自动冒泡到document，无需重复触发
        const event = new CustomEvent('page-change', {
            detail: { page },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(event);
    }
}

customElements.define('navigation-card', NavigationCard); 