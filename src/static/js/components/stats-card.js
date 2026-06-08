class StatsCard extends BaseComponent {
    constructor() {
        super();
    }

    async connectedCallback() {
        await this.loadMetadata();
        this.render();
    }

    render() {
        const userCount = this.metadata?.user_count || 0;
        const postCount = this.metadata?.post_count || 0;

        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css?v=20250609');
                :host {
                    display: block;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: var(--spacing-4);
                }

                .stat-item {
                    text-align: center;
                    padding: var(--spacing-4);
                    background: var(--gray-50);
                    border-radius: var(--radius-md);
                    border: 1px solid var(--gray-200);
                }

                .stat-number {
                    font-size: var(--font-size-2xl);
                    font-weight: 700;
                    color: var(--primary-color);
                    display: block;
                    margin-bottom: var(--spacing-1);
                }

                .stat-label {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    font-weight: 500;
                }

                .loading {
                    opacity: 0.6;
                }

                @media (max-width: 768px) {
                    .stats-grid {
                        grid-template-columns: 1fr;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">网站统计</h3>
                </div>
                <div class="card-body">
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-number">${userCount.toLocaleString()}</span>
                            <span class="stat-label">注册用户</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${postCount.toLocaleString()}</span>
                            <span class="stat-label">博文总数</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('stats-card', StatsCard); 