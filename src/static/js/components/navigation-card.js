class NavigationCard extends BaseComponent {
    constructor() {
        super();
    }

    connectedCallback() {
        this.render();
    }

    render() {
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
                            <div class="nav-icon">👥</div>
                            <span class="nav-text">用户列表</span>
                        </a>
                        <a href="/api/rss/site" class="nav-item" target="_blank">
                            <div class="nav-icon">📡</div>
                            <span class="nav-text">全站RSS</span>
                        </a>
                        <a href="/categories" class="nav-item">
                            <div class="nav-icon">📂</div>
                            <span class="nav-text">分类浏览</span>
                        </a>
                        <a href="/tags" class="nav-item">
                            <div class="nav-icon">🏷️</div>
                            <span class="nav-text">标签云</span>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('navigation-card', NavigationCard); 