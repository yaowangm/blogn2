/**
 * 文章头部卡片组件
 * 显示文章的标题、作者、日期、分类、点击数等基本信息
 */
class ArticleHeaderCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
    }

    async connectedCallback() {
        // 从URL获取文章ID
        this.articleId = this.getArticleIdFromUrl();
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        // 加载文章数据
        await this.loadArticleData();
        
        // 渲染组件
        this.render();
    }

    /**
     * 从URL获取文章ID
     */
    getArticleIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        const articleIndex = pathParts.indexOf('article');
        if (articleIndex !== -1 && pathParts[articleIndex + 1]) {
            return parseInt(pathParts[articleIndex + 1]);
        }
        return null;
    }

    /**
     * 加载文章数据
     */
    async loadArticleData() {
        try {
            const response = await fetch(`/api/articles/${this.articleId}`);
            if (response.ok) {
                this.articleData = await response.json();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.logError('Failed to load article data', error);
            this.showError('加载文章数据失败');
        }
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.shadowRoot.innerHTML = `
                <div class="card article-header-card">
                    <div class="card-body">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            `;
            return;
        }

        const { title, author, project, category, hits, created_at, updated_at, comment_count } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-header-card">
                <div class="card-body">
                    <div class="article-title">
                        <h1>${title || '无标题'}</h1>
                    </div>
                    
                    <div class="article-meta">
                        <div class="meta-item">
                            <span class="meta-label">作者:</span>
                            <span class="meta-value">${author?.name || '未知作者'}</span>
                        </div>
                        
                        <div class="meta-item">
                            <span class="meta-label">发布时间:</span>
                            <span class="meta-value">${this.formatDate(created_at)}</span>
                        </div>
                        
                        ${updated_at && updated_at !== created_at ? `
                            <div class="meta-item">
                                <span class="meta-label">更新时间:</span>
                                <span class="meta-value">${this.formatDate(updated_at)}</span>
                            </div>
                        ` : ''}
                        
                        ${project?.name ? `
                            <div class="meta-item">
                                <span class="meta-label">博客:</span>
                                <span class="meta-value">${project.name}</span>
                            </div>
                        ` : ''}
                        
                        <div class="meta-item">
                            <span class="meta-label">点击数:</span>
                            <span class="meta-value">${hits || 0}</span>
                        </div>
                        
                        <div class="meta-item">
                            <span class="meta-label">评论数:</span>
                            <span class="meta-value">${comment_count || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.addStyles();
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="card article-header-card">
                <div class="card-body">
                    <div class="error-message">${message}</div>
                </div>
            </div>
        `;
        this.addStyles();
    }

    /**
     * 添加样式
     */
    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                .article-header-card {
                    margin-bottom: var(--spacing-6);
                }
                
                .article-title h1 {
                    font-size: var(--font-size-3xl);
                    font-weight: 700;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-6);
                    line-height: 1.2;
                }
                
                .article-meta {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: var(--spacing-4);
                    padding: var(--spacing-4);
                    background-color: var(--gray-50);
                    border-radius: var(--radius-lg);
                    border: 1px solid var(--gray-200);
                }
                
                .meta-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                
                .meta-label {
                    font-weight: 600;
                    color: var(--gray-600);
                    min-width: 80px;
                }
                
                .meta-value {
                    color: var(--gray-800);
                }
                
                .loading {
                    text-align: center;
                    color: var(--gray-500);
                    padding: var(--spacing-8);
                }
                
                .error-message {
                    text-align: center;
                    color: var(--error-color);
                    padding: var(--spacing-8);
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('article-header-card', ArticleHeaderCard);
