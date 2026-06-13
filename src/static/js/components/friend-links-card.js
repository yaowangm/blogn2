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
        BaseComponent.observeWhenVisible(this, async () => {
            await Promise.all([this.checkOwnership(), this.loadData()]);
            this.render();
        });
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
                @import url('/static/css/common-components.css');
                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    min-width: 0;
                }

                .card-title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                    flex-shrink: 0;
                }

                .manage-button {
                    flex-shrink: 0;
                }
                .friend-link-icon {
                    flex-shrink: 0;
                    width: 14px;
                    height: 14px;
                    color: var(--gray-400);
                    transition: color var(--transition-fast);
                }

                .post-item.friend-link-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .post-item.friend-link-item:hover .friend-link-icon,
                .post-item.friend-link-item:focus-visible .friend-link-icon {
                    color: var(--interactive-hover-text);
                }

                .friend-link-text {
                    flex: 1;
                    min-width: 0;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    font-size: var(--font-size-sm);
                    line-height: 1.35;
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
                        <svg class="card-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                        </svg>
                        友情链接
                    </h3>
                    ${(this.isOwner || this.isAdmin) ? `
                        <a href="/manage-friend-links?project_id=${this.projectId}"
                           class="btn btn-secondary btn-sm btn-icon-only manage-button"
                           target="_blank"
                           title="管理友情链接"
                           aria-label="管理友情链接">
                            ${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.settings) : ''}
                        </a>
                    ` : ''}
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
            <div class="post-list">
                ${this.friendLinks.map((link) => {
                    const safeSubject = this.escapeHtml(link.subject);
                    const safeLinkStr = this.escapeHtml(link.linkstr);

                    return `
                        <a href="${safeLinkStr}"
                           class="post-item friend-link-item"
                           target="_blank"
                           rel="noopener noreferrer"
                           title="${safeSubject}">
                            <span class="friend-link-text author-name">${safeSubject}</span>
                            <svg class="friend-link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" y1="14" x2="21" y2="3"></line>
                            </svg>
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