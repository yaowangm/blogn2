/**
 * 博客导航卡片组件
 * 提供博客相关的导航链接
 */
class BlogNavigationCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
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

                .nav-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .nav-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .nav-item {
                    border-bottom: 1px solid var(--gray-100);
                }

                .nav-item:last-child {
                    border-bottom: none;
                }

                .nav-link {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-4) var(--spacing-6);
                    color: var(--gray-700);
                    text-decoration: none;
                    transition: var(--transition-fast);
                    font-size: var(--font-size-sm);
                }

                .nav-link:hover {
                    background: var(--gray-50);
                    color: var(--primary-color);
                }

                .nav-link.active {
                    background: var(--primary-color);
                    color: var(--white);
                }

                .link-icon {
                    width: 18px;
                    height: 18px;
                    color: inherit;
                    flex-shrink: 0;
                }

                .link-text {
                    flex: 1;
                }

                .link-badge {
                    background: var(--accent-color);
                    color: var(--white);
                    font-size: var(--font-size-xs);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-full);
                    font-weight: 500;
                }

                .rss-link {
                    background: var(--gray-100);
                    color: var(--gray-700);
                    font-weight: 500;
                }

                .rss-link:hover {
                    background: var(--gray-200);
                    color: var(--gray-800);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                        博客导航
                    </h3>
                </div>
                <nav>
                    <ul class="nav-list">
                        <li class="nav-item">
                            <a href="/" class="nav-link">
                                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                                    <polyline points="9,22 9,12 15,12 15,22"/>
                                </svg>
                                <span class="link-text">日志首页</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="/blog/${this.projectId}/about" class="nav-link">
                                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                    <circle cx="12" cy="7" r="4"/>
                                </svg>
                                <span class="link-text">个人介绍</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="/blog/${this.projectId}/subscriptions" class="nav-link">
                                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
                                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
                                </svg>
                                <span class="link-text">订阅的博客</span>
                                <span class="link-badge">新</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="/api/projects/${this.projectId}/rss" class="nav-link rss-link" target="_blank">
                                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M4 11a9 9 0 0 1 9 9"/>
                                    <path d="M4 4a16 16 0 0 1 16 16"/>
                                    <circle cx="5" cy="19" r="1"/>
                                </svg>
                                <span class="link-text">RSS订阅</span>
                            </a>
                        </li>
                    </ul>
                </nav>
            </div>
        `;
    }
}

customElements.define('blog-navigation-card', BlogNavigationCard);
