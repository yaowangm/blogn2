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
        this.isOwner = false;
        this.isAdmin = false;
    }


    async connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        await Promise.all([this.checkOwnership(), this.loadData()]);
        this.render();
    }

    getProjectIdFromUrl() {
        // 使用基类的统一方法
        return this.getProjectId();
    }

    async checkOwnership() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            this.isOwner = false;
            this.isAdmin = false;
            return;
        }

        // 如果未登录，不是所有者
        if (!UserManager.isLoggedIn()) {
            this.isOwner = false;
            this.isAdmin = false;
            return;
        }

        const currentUser = UserManager.getCurrentUser();
        
        // 检查是否为管理员（state为10表示管理员）
        this.isAdmin = currentUser.state === 10;

        if (this.projectId) {
            try {
                const blogData = await BaseComponent.getProject(this.projectId);
                this.isOwner = blogData ? currentUser.id === blogData.userid : false;
            } catch (error) {
                console.error('检查所有权失败:', error);
                this.isOwner = false;
            }
        } else {
            this.isOwner = false;
        }
    }

    async loadData() {
        try {
            // 首页无 projectId 时，尝试加载全站友情链接（project_id=0）
            const pid = this.projectId ? this.projectId : 0;
            const response = await fetch(`/api/projects/${pid}/friend-links`);
            if (response.ok) {
                const data = await response.json();
                // 接口成功则使用返回数据；为空则显示空列表
                this.friendLinks = Array.isArray(data) ? data : [];
            } else {
                // 接口失败显示空列表
                this.friendLinks = [];
            }
        } catch (error) {
            console.error('Error loading friend links:', error);
            this.friendLinks = [];
        } finally {
            this.loading = false;
            this.render();
            this.addEventListeners();
        }
    }

    addEventListeners() {
        // 延迟添加事件监听器，确保DOM已经渲染
        setTimeout(() => {
            const manageButton = this.shadowRoot.querySelector('.manage-button');
            if (manageButton) {
                manageButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    const projectId = this.projectId;
                    if (projectId !== undefined && projectId !== null) {
                        window.open(`/manage-friend-links?project_id=${projectId}`, '_blank');
                    } else {
                        // 全站友情链接管理（仅管理员有效）
                        window.open('/manage-friend-links', '_blank');
                    }
                });
            }
        }, 100);
    }

    getDefaultFriendLinks() {
        return [
            { subject: '无双谱', linkstr: 'http://wsp.bloggern.com' },
            { subject: '豌豆网', linkstr: 'http://www.OneDoor.cn' },
            { subject: '火网', linkstr: 'http://www.huooo.com' }
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
                    justify-content: space-between;
                }

                .card-title-left {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .manage-button {
                    padding: var(--spacing-1) var(--spacing-2);
                    background: var(--primary-color);
                    color: var(--white);
                    border: none;
                    border-radius: var(--radius-sm);
                    font-size: var(--font-size-xs);
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                }

                .manage-button:hover {
                    background: var(--primary-dark);
                    transform: translateY(-1px);
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
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
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
                    min-height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
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

                /* 响应式设计 */
                @media (max-width: 768px) {
                    .friend-links {
                        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                        gap: var(--spacing-2);
                    }

                    .friend-link {
                        padding: var(--spacing-2) var(--spacing-3);
                        font-size: var(--font-size-sm);
                        min-height: 36px;
                    }
                }

                @media (max-width: 480px) {
                    .friend-links {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }


            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <div class="card-title-left">
                            <svg class="card-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                            </svg>
                            友情链接
                        </div>
                        ${(this.isOwner || this.isAdmin) ? `
                            <a href="/manage-friend-links?project_id=${this.projectId}" 
                               class="manage-button" 
                               target="_blank" 
                               title="管理友情链接">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="3"></circle>
                                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                                </svg>
                                管理
                            </a>
                        ` : ''}
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