/**
 * 外站链接卡片组件
 * 显示外部链接
 */
class ExternalLinksCard extends BaseComponent {
    constructor() {
        super();
        this.externalLinks = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        this.loadData();
    }

    async loadData() {
        // 检测是否在博客页面
        const isBlogPage = this.isBlogPage();
        let apiUrl;
        
        if (isBlogPage) {
            // 在博客页面：获取当前博客的外部链接
            const projectId = this.getProjectIdFromUrl();
            if (projectId) {
                apiUrl = `/api/projects/${projectId}/external-links`;
            } else {
                this.showError('无法获取博客ID');
                return;
            }
        } else {
            // 在首页：获取全站外部链接（如果有的话）
            // 目前使用模拟数据，后续可以添加全站外部链接API
            this.externalLinks = this.getMockExternalLinks();
            this.loading = false;
            this.render();
            return;
        }

        try {
            const response = await fetch(apiUrl);
            if (response.ok) {
                this.externalLinks = await response.json();
            } else {
                this.externalLinks = this.getMockExternalLinks();
            }
        } catch (error) {
            console.error('Error loading external links:', error);
            this.externalLinks = this.getMockExternalLinks();
        } finally {
            this.loading = false;
            this.render();
        }
    }

    /**
     * 检测是否在博客页面
     * @returns {boolean} 是否在博客页面
     */
    isBlogPage() {
        const path = window.location.pathname;
        return path.startsWith('/blog/');
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    getMockExternalLinks() {
        return [
            { id: 1, name: 'GitHub', url: 'https://github.com', description: '代码托管平台' },
            { id: 2, name: 'Stack Overflow', url: 'https://stackoverflow.com', description: '程序员问答社区' },
            { id: 3, name: '掘金', url: 'https://juejin.cn', description: '开发者社区' }
        ];
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host { display: block; font-family: var(--font-family); }
                .card { background: var(--white); border-radius: var(--radius-xl); box-shadow: var(--shadow-md); border: 1px solid var(--gray-200); overflow: hidden; margin-bottom: var(--spacing-6); }
                .card-header { padding: var(--spacing-4) var(--spacing-6); background: var(--gray-50); border-bottom: 1px solid var(--gray-200); }
                .card-title { margin: 0; font-size: var(--font-size-lg); font-weight: 600; color: var(--gray-800); display: flex; align-items: center; gap: var(--spacing-2); }
                .title-icon { width: 20px; height: 20px; color: var(--primary-color); }
                .links-list { list-style: none; margin: 0; padding: 0; }
                .link-item { border-bottom: 1px solid var(--gray-100); }
                .link-item:last-child { border-bottom: none; }
                .link-content { display: flex; align-items: center; gap: var(--spacing-3); padding: var(--spacing-4) var(--spacing-6); color: var(--gray-700); text-decoration: none; transition: var(--transition-fast); }
                .link-content:hover { background: var(--gray-50); color: var(--primary-color); }
                .link-icon { width: 24px; height: 24px; color: var(--gray-600); flex-shrink: 0; }
                .link-info { flex: 1; min-width: 0; }
                .link-name { font-weight: 500; color: inherit; margin: 0 0 var(--spacing-1) 0; font-size: var(--font-size-sm); }
                .link-description { color: var(--gray-500); font-size: var(--font-size-xs); margin: 0; line-height: 1.3; }
                .external-indicator { color: var(--gray-400); font-size: var(--font-size-xs); }
                .loading { text-align: center; padding: var(--spacing-8); color: var(--gray-500); }
                .error { text-align: center; padding: var(--spacing-6); color: var(--error-color); background: var(--gray-50); border-radius: var(--radius-lg); }
                .empty-state { text-align: center; padding: var(--spacing-6); color: var(--gray-500); }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                            <polyline points="15,3 21,3 21,9"/>
                            <line x1="10" y1="14" x2="21" y2="3"/>
                        </svg>
                        外站链接
                    </h3>
                </div>
                ${this.loading ? this.renderLoading() : 
                  this.externalLinks.length > 0 ? this.renderLinks() : 
                  this.renderEmptyState()}
            </div>
        `;
    }

    renderLoading() {
        return `<div class="loading"><div>加载中...</div></div>`;
    }

    renderLinks() {
        return `
            <ul class="links-list">
                ${this.externalLinks.map(link => `
                    <li class="link-item">
                        <a href="${link.url}" class="link-content" target="_blank" rel="noopener noreferrer">
                            <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                            </svg>
                            <div class="link-info">
                                <div class="link-name">${link.name}</div>
                                <div class="link-description">${link.description}</div>
                            </div>
                            <div class="external-indicator">↗</div>
                        </a>
                    </li>
                `).join('')}
            </ul>
        `;
    }

    renderEmptyState() {
        return `<div class="empty-state"><div>暂无外站链接</div></div>`;
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }
}

customElements.define('external-links-card', ExternalLinksCard);
