/**
 * 评论设置卡片组件
 * 显示当前文章的评论设置信息
 */
class CommentSettingsCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
        this.isLoggedIn = false;
    }

    async connectedCallback() {
        this.articleId = this.getArticleIdFromUrl();
        if (!this.articleId) {
            this.hide();
            return;
        }

        // 检查登录状态
        this.isLoggedIn = UserManager.isLoggedIn();
        
        // 加载文章数据
        await this.loadArticleData();
        
        // 渲染组件
        this.render();
    }

    /**
     * 从URL获取文章ID
     */
    getArticleIdFromUrl() {
        return this.getArticleId();
    }

    /**
     * 检查登录状态
     */

    /**
     * 加载文章数据
     */
    async loadArticleData() {
        try {
            const articleData = await BaseComponent.getArticle(this.articleId);
            if (articleData) {
                this.articleData = articleData;
            } else {
                this.hide();
            }
        } catch (error) {
            this.hide();
        }
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.hide();
            return;
        }

        const allowpost = this.articleData.allowpost || 1;
        const settingsInfo = this.getCommentSettingsInfo(allowpost);
        
        this.shadowRoot.innerHTML = `
            <div class="card comment-settings-card">
                <div class="card-body">
                    <div class="comment-settings-info">
                        <div class="settings-icon">
                            ${settingsInfo.icon}
                        </div>
                        <div class="settings-content">
                            <div class="settings-title">${settingsInfo.title}</div>
                            <div class="settings-description">${settingsInfo.description}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.addStyles();
    }

    /**
     * 获取评论设置信息
     */
    getCommentSettingsInfo(allowpost) {
        switch (allowpost) {
            case 1:
                return {
                    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        <path d="M13 8H7"/>
                        <path d="M17 12H7"/>
                    </svg>`,
                    title: "允许匿名评论",
                    description: "任何人都可以发表评论，无需登录"
                };
            case 2:
                return {
                    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        <path d="M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z"/>
                    </svg>`,
                    title: "只允许登录用户评论",
                    description: this.isLoggedIn ? "您已登录，可以发表评论" : "需要登录后才能发表评论"
                };
            case 3:
                return {
                    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                    </svg>`,
                    title: "不允许任何评论",
                    description: "此文章已关闭评论功能"
                };
            default:
                return {
                    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>`,
                    title: "评论设置",
                    description: "评论功能状态未知"
                };
        }
    }

    /**
     * 检查是否可以发表评论
     */
    canComment() {
        if (!this.articleData) return false;
        
        const allowpost = this.articleData.allowpost || 1;
        
        switch (allowpost) {
            case 1: // 允许匿名评论
                return true;
            case 2: // 只允许登录用户评论
                return this.isLoggedIn;
            case 3: // 不允许任何评论
                return false;
            default:
                return false;
        }
    }

    /**
     * 隐藏组件
     */
    hide() {
        this.style.display = 'none';
    }

    /**
     * 添加样式
     */
    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                @import url('/static/css/common-components.css');

                .card { margin-bottom: 0; }

                .card-body {
                    padding: calc(var(--spacing-3) * 0.6) var(--spacing-4);
                }

                .comment-settings-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }
                
                .settings-icon {
                    flex-shrink: 0;
                    color: var(--primary-color);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .settings-content {
                    flex: 1;
                    min-width: 0;
                }
                
                .settings-title {
                    font-size: var(--font-size-sm);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-1);
                }
                
                .settings-description {
                    font-size: var(--font-size-xs);
                    color: var(--gray-600);
                    line-height: 1.4;
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('comment-settings-card', CommentSettingsCard);
