class StatsCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
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
                            <span class="stat-number">1,234</span>
                            <span class="stat-label">注册用户</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">5,678</span>
                            <span class="stat-label">博文总数</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('stats-card', StatsCard); 