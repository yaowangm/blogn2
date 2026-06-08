/**
 * 博客导航卡片组件
 * 提供博客相关的导航链接
 */
class BlogNavigationCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.userData = null;
        this.loading = true;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadUserData();
    }

    getProjectIdFromUrl() {
        // 使用基类的统一方法
        return this.getProjectId();
    }

    async loadUserData() {
        if (!this.projectId) {
            this.loading = false;
            this.render();
            return;
        }

        try {
            const projectData = await BaseComponent.getProject(this.projectId);
            if (projectData === null) {
                window.location.href = '/static/error.html';
                return;
            }
            if (projectData.userid) {
                const userResponse = await fetch(`/api/users/${projectData.userid}`);
                if (userResponse.ok) {
                    this.userData = await userResponse.json();
                }
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        } finally {
            this.loading = false;
            this.render();
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css?v=20250609');
                .card-title {
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
                    padding: var(--spacing-3) var(--spacing-4);
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

                /* 为所有SVG图标设置默认尺寸 */
                .nav-link svg {
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
                    color: var(--gray-900);
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.menu}
                        博客导航
                    </h3>
                </div>
                ${this.loading ? this.renderLoading() : this.renderNavigation()}
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

    renderNavigation() {
        // 构建个人介绍链接
        let aboutLink = `/blog/${this.projectId}/about`; // 默认链接
        if (this.userData && this.userData.intropiid) {
            aboutLink = `/article/${this.userData.intropiid}`;
        }

        return `
            <nav>
                <ul class="nav-list">
                    <li class="nav-item">
                        <a href="/" class="nav-link">
                            ${Icons.home}
                            <span class="link-text">日志首页</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="${aboutLink}" class="nav-link">
                            ${Icons.about}
                            <span class="link-text">个人介绍</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="/blog/${this.projectId}/subscriptions" class="nav-link">
                            ${Icons.subscription}
                            <span class="link-text">订阅的博客</span>
                            <span class="link-badge">新</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="/api/rss/blog/${this.projectId}" class="nav-link rss-link" target="_blank">
                            ${Icons.rss}
                            <span class="link-text">RSS订阅</span>
                        </a>
                    </li>
                </ul>
            </nav>
        `;
    }
}

customElements.define('blog-navigation-card', BlogNavigationCard);
