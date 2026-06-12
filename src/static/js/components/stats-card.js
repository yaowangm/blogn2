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

                :host {
                    display: block;
                    min-width: 0;
                }

                .card {
                    min-width: 0;
                }

                .stats-body.card-body {
                    padding: var(--spacing-3);
                }

                .stats-body {
                    display: grid;
                    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
                    gap: var(--spacing-2);
                    min-width: 0;
                    container-type: inline-size;
                }

                .stat-block {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    gap: var(--spacing-2);
                    padding: var(--spacing-3) var(--spacing-2);
                    background: var(--stat-tint, var(--gray-50));
                    border: 1px solid var(--stat-tint-border, var(--gray-200));
                    border-radius: var(--radius-lg);
                    min-width: 0;
                    overflow: hidden;
                }

                .stat-icon {
                    flex-shrink: 0;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--stat-icon-bg, var(--gray-100));
                    color: var(--primary-color);
                }

                .stat-icon svg {
                    width: 16px;
                    height: 16px;
                }

                .stat-content {
                    min-width: 0;
                    width: 100%;
                }

                .stat-number {
                    display: block;
                    font-size: clamp(0.875rem, 16cqi, 1.25rem);
                    font-weight: 700;
                    font-variant-numeric: tabular-nums;
                    color: var(--gray-900);
                    line-height: 1.2;
                    letter-spacing: -0.02em;
                    max-width: 100%;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .stat-label {
                    display: block;
                    margin-top: var(--spacing-1);
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    color: var(--gray-600);
                    max-width: 100%;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                @container (max-width: 220px) {
                    .stats-body {
                        grid-template-columns: 1fr;
                    }
                }

                @media (max-width: 768px) {
                    .stats-body {
                        grid-template-columns: 1fr 1fr;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.stats}
                        网站统计
                    </h3>
                </div>
                <div class="card-body stats-body">
                    <div class="stat-block">
                        <div class="stat-icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                                <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                        </div>
                        <div class="stat-content">
                            <span class="stat-number">${userCount.toLocaleString()}</span>
                            <span class="stat-label">注册用户</span>
                        </div>
                    </div>
                    <div class="stat-block">
                        <div class="stat-icon" aria-hidden="true">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                                <line x1="16" y1="13" x2="8" y2="13"></line>
                                <line x1="16" y1="17" x2="8" y2="17"></line>
                            </svg>
                        </div>
                        <div class="stat-content">
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
