/**
 * 友情链接卡片组件
 * 从数据库urllink表获取友情链接数据
 * subject字段表示链接名称，linkstr字段表示链接URL
 * projectid表示所属的project的id，按ordernum排序
 */
class FriendLinksCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.friendLinks = [];
        this.loading = true;
    }


    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadData();
    }

    getProjectIdFromUrl() {
        // 使用基类的统一方法
        return this.getProjectId();
    }

    async loadData() {
        try {
            let apiUrl;
            
            if (this.projectId) {
                // 如果在博客页面，获取指定项目的友情链接
                apiUrl = `/api/projects/${this.projectId}/friend-links`;
            } else if (this.isArticlePage()) {
                // 如果在文章页面，需要从文章ID获取项目ID
                const articleId = this.getArticleId();
                if (articleId) {
                    try {
                        // 先获取文章信息，从中提取项目ID
                        const articleResponse = await fetch(`/api/articles/${articleId}`);
                        if (articleResponse.ok) {
                            const articleData = await articleResponse.json();
                            const projectId = articleData.project?.id;
                            if (projectId) {
                                apiUrl = `/api/projects/${projectId}/friend-links`;
                            } else {
                                apiUrl = '/api/friend-links';
                            }
                        } else {
                            apiUrl = '/api/friend-links';
                        }
                    } catch (error) {
                        console.warn('获取文章信息失败，使用默认API');
                        apiUrl = '/api/friend-links';
                    }
                } else {
                    apiUrl = '/api/friend-links';
                }
            } else {
                // 如果在首页，获取所有友情链接
                apiUrl = '/api/friend-links';
            }

            const response = await fetch(apiUrl);
            if (response.ok) {
                this.friendLinks = await response.json();
            } else {
                console.warn('获取友情链接失败，使用默认数据');
                this.friendLinks = this.getDefaultFriendLinks();
            }
        } catch (error) {
            console.error('Error loading friend links:', error);
            this.friendLinks = this.getDefaultFriendLinks();
        } finally {
            this.loading = false;
            this.render();
        }
    }

    getDefaultFriendLinks() {
        return [
            { subject: 'GitHub', linkstr: 'https://github.com' },
            { subject: 'Stack Overflow', linkstr: 'https://stackoverflow.com' },
            { subject: '掘金', linkstr: 'https://juejin.cn' },
            { subject: 'CSDN', linkstr: 'https://csdn.net' },
            { subject: '博客园', linkstr: 'https://cnblogs.com' },
            { subject: '简书', linkstr: 'https://jianshu.com' }
        ];
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
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .card-title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .card-body {
                    padding: var(--spacing-5);
                }

                .friend-links {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-2);
                }

                .friend-link {
                    padding: var(--spacing-2) var(--spacing-3);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    text-decoration: none;
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                    text-align: center;
                    transition: var(--transition-fast);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .friend-link:hover {
                    background: var(--primary-color);
                    color: var(--white);
                    border-color: var(--primary-color);
                    transform: translateY(-1px);
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-4);
                    color: var(--gray-500);
                }

                .empty-state {
                    text-align: center;
                    padding: var(--spacing-4);
                    color: var(--gray-500);
                    font-style: italic;
                }


            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.friendLinks}
                        友情链接
                    </h3>
                </div>
                <div class="card-body">
                    ${this.loading ? this.renderLoading() : 
                      this.friendLinks.length > 0 ? this.renderFriendLinks() : 
                      this.renderEmptyState()}
                </div>
            </div>
        `;
    }

    renderLoading() {
        return `<div class="loading">加载中...</div>`;
    }

    renderFriendLinks() {
        return `
            <div class="friend-links">
                ${this.friendLinks.map(link => {
                    // 安全处理所有文本字段，防止HTML注入和XSS攻击
                    const safeSubject = this.escapeHtml(link.subject);
                    const safeLinkStr = this.escapeHtml(link.linkstr);
                    
                    return `
                        <a href="${safeLinkStr}" class="friend-link" target="_blank" rel="noopener noreferrer" title="${safeSubject}">
                            ${safeSubject}
                        </a>
                    `;
                }).join('')}
            </div>
        `;
    }

    renderEmptyState() {
        return `<div class="empty-state">暂无友情链接</div>`;
    }
}

customElements.define('friend-links-card', FriendLinksCard); 