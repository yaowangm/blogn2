/**
 * 博客头部信息卡片组件
 * 显示博客名称、描述和统计信息
 */
class BlogHeaderCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.blogData = null;
        this.loading = true;
        this.subscriptionStatus = null;
        this.isCurrentUserBlog = false;
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
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            // 获取博客信息
            const response = await fetch(`/api/projects/${this.projectId}`);
            if (response.ok) {
                this.blogData = await response.json();
            } else if (response.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                // 其他错误，使用模拟数据
                this.blogData = this.getMockBlogData();
            }
            
            // 检查是否为当前用户的博客
            this.checkIfCurrentUserBlog();
            
            // 检查订阅状态
            await this.loadSubscriptionStatus();
            
        } catch (error) {
            console.error('Error loading blog data:', error);
            this.blogData = this.getMockBlogData();
        } finally {
            this.loading = false;
            this.render();
            // 动态更新页面title
            this.updatePageTitle();
        }
    }

    /**
     * 加载博客头部信息
     */
    async loadBlogHeader() {
        try {
            this.loading = true;
            this.render();
            
            const response = await fetch(`/api/projects/${this.projectId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch blog data');
            }
            this.blogData = await response.json();
            
            // 更新页面标题
            this.updatePageTitle();
            
        } catch (error) {
            console.error('Error loading blog header data:', error);
            this.showError('加载博客信息失败');
        } finally {
            this.loading = false;
            this.render();
        }
    }


    /**
     * 检查是否为当前用户的博客
     */
    checkIfCurrentUserBlog() {
        if (!this.blogData || !UserManager.isLoggedIn()) {
            this.isCurrentUserBlog = false;
            return;
        }
        
        const currentUser = UserManager.getCurrentUser();
        this.isCurrentUserBlog = currentUser.id === this.blogData.userid;
    }

    getMockBlogData() {
        return {
            id: this.projectId,
            name: '我的技术博客',
            comment: '分享技术心得、学习笔记和生活感悟的地方。记录成长，分享快乐。',
            recordcount: 25,
            commentcount: 18,
            accesscount: 1250,
            createtime: '2023-06-15T00:00:00Z',
            updatetime: '2024-01-15T10:30:00Z'
        };
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');
                .card-header { padding: var(--spacing-8) var(--spacing-6); background: var(--gray-50); color: var(--gray-800); text-align: center; border-bottom: 1px solid var(--gray-200); }
                .blog-title { margin: 0 0 var(--spacing-4) 0; font-size: var(--font-size-3xl); font-weight: 700; color: var(--gray-800); }
                .blog-description { margin: 0; font-size: var(--font-size-lg); color: var(--gray-600); opacity: 0.9; line-height: 1.6; max-width: 650px; margin-left: auto; margin-right: auto; }
                .blog-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--spacing-4); margin-bottom: var(--spacing-6); }
                .stat-item { text-align: center; padding: var(--spacing-4); background: var(--gray-50); border-radius: var(--radius-lg); border: 1px solid var(--gray-200); }
                .stat-number { font-size: var(--font-size-2xl); font-weight: 700; color: var(--primary-color); margin: 0 0 var(--spacing-2) 0; }
                .stat-label { font-size: var(--font-size-sm); color: var(--gray-600); margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
                .blog-meta { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-4) var(--spacing-6); background: var(--gray-50); border-radius: var(--radius-lg); }
                .meta-items-left { 
                    display: flex; 
                    align-items: center; 
                    gap: var(--spacing-6); 
                }
                .meta-item { display: flex; align-items: center; gap: var(--spacing-2); color: var(--gray-600); font-size: var(--font-size-sm); }
                .meta-icon { width: 16px; height: 16px; color: var(--gray-500); }
                .meta-subscription-right { 
                    display: flex; 
                    align-items: center; 
                }
                .subscription-section { 
                    margin-top: var(--spacing-4); 
                    padding: var(--spacing-4); 
                    background: var(--gray-50); 
                    border-radius: var(--radius-lg); 
                    border: 1px solid var(--gray-200);
                    text-align: center;
                }
                .subscription-button { 
                    background: var(--primary-color); 
                    color: white; 
                    border: none; 
                    padding: var(--spacing-3) var(--spacing-6); 
                    border-radius: var(--radius-md); 
                    cursor: pointer; 
                    font-size: var(--font-size-sm); 
                    font-weight: 500; 
                    transition: all 0.2s ease;
                    display: inline-block;
                    text-decoration: none;
                    min-width: 80px;
                    min-height: 36px;
                    position: relative;
                    z-index: 1;
                }
                .subscription-button:hover { 
                    background: #1d4ed8; 
                    transform: translateY(-1px); 
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                .subscription-button:disabled { 
                    background: var(--gray-400); 
                    cursor: not-allowed; 
                    transform: none; 
                    box-shadow: none;
                }
                .subscription-button.unsubscribe { 
                    background: var(--red-500); 
                }
                .subscription-button.unsubscribe:hover {
                    background: #dc2626;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                .subscription-button-inline { 
                    background: var(--primary-color); 
                    color: white; 
                    border: none; 
                    padding: var(--spacing-2) var(--spacing-4); 
                    border-radius: var(--radius-md); 
                    cursor: pointer; 
                    font-size: var(--font-size-xs); 
                    font-weight: 500; 
                    transition: all 0.2s ease;
                    display: inline-block;
                    text-decoration: none;
                    min-width: 60px;
                    min-height: 28px;
                    position: relative;
                    z-index: 1;
                }
                .subscription-button-inline:hover { 
                    background: #1d4ed8; 
                    transform: translateY(-1px); 
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .subscription-button-inline:disabled { 
                    background: var(--gray-400); 
                    cursor: not-allowed; 
                    transform: none; 
                    box-shadow: none;
                }
                .subscription-button-inline.unsubscribe {
                    background: var(--red-500);
                }
                .subscription-button-inline.unsubscribe:hover {
                    background: #dc2626;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
            </style>

            <div class="card">
                ${this.loading ? this.renderLoading() : 
                  this.blogData ? this.renderContent() : 
                  this.renderError()}
            </div>
        `;
    }

    renderLoading() {
        return `<div class="loading"><div>加载中...</div></div>`;
    }

    renderContent() {
        // 安全处理所有文本字段，防止HTML注入和XSS攻击
        const safeBlogName = this.escapeHtml(this.blogData.name || '未命名博客');
        const safeBlogDesc = this.escapeHtml(this.blogData.comment || '这个博客还没有描述');
        const createDate = this.blogData.createtime ? this.formatDate(this.blogData.createtime) : '未知';
        const updateDate = this.blogData.updatetime ? this.formatDate(this.blogData.updatetime) : '未知';

        return `
            <div class="card-header">
                <h1 class="blog-title">${safeBlogName}</h1>
                <p class="blog-description">${safeBlogDesc}</p>
            </div>
            <div class="card-body">
                <div class="blog-stats">
                    <div class="stat-item">
                        <div class="stat-number">${this.blogData.recordcount || 0}</div>
                        <div class="stat-label">文章</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.blogData.commentcount || 0}</div>
                        <div class="stat-label">评论</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.blogData.accesscount || 0}</div>
                        <div class="stat-label">访问</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.getDaysSinceCreation()}</div>
                        <div class="stat-label">天</div>
                    </div>
                </div>
                <div class="blog-meta">
                    <div class="meta-items-left">
                        <div class="meta-item">
                            <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>
                            </svg>
                            <span>创建于 ${createDate}</span>
                        </div>
                        <div class="meta-item">
                            <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/>
                            </svg>
                            <span>更新于 ${updateDate}</span>
                        </div>
                    </div>
                    <div class="meta-subscription-right">
                        ${this.renderSubscriptionButton()}
                    </div>
                </div>
            </div>
        `;
    }

    renderError() {
        return `<div class="error"><div>加载失败</div></div>`;
    }

    /**
     * 渲染订阅按钮（内联版本）
     */
    renderSubscriptionButton() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            console.error('UserManager not available in renderSubscriptionButton');
            return '';
        }

        // 如果未登录，不显示订阅按钮
        if (!UserManager.isLoggedIn()) {
            return '';
        }

        // 如果是当前用户的博客，不显示订阅按钮
        if (this.isCurrentUserBlog) {
            return '';
        }

        // 如果订阅状态未加载，显示加载中
        if (this.subscriptionStatus === null) {
            return `<button class="subscription-button-inline" disabled>加载中...</button>`;
        }

        // 根据订阅状态显示相应按钮
        const isSubscribed = this.subscriptionStatus.is_subscribed;
        const buttonText = isSubscribed ? '取消订阅' : '订阅';
        const buttonClass = isSubscribed ? 'subscription-button-inline unsubscribe' : 'subscription-button-inline';

        return `<button class="${buttonClass}" onclick="this.getRootNode().host.handleSubscription()">${buttonText}</button>`;
    }

    /**
     * 渲染订阅区域（保留原方法以兼容）
     */
    renderSubscriptionSection() {
        // 检查UserManager是否可用
        if (typeof UserManager === 'undefined') {
            console.error('UserManager not available in renderSubscriptionSection');
            return '';
        }

        // 如果未登录，不显示订阅区域
        if (!UserManager.isLoggedIn()) {
            return '';
        }

        // 如果是当前用户的博客，不显示订阅区域
        if (this.isCurrentUserBlog) {
            return '';
        }

        // 如果订阅状态未加载，显示加载中
        if (this.subscriptionStatus === null) {
            return `
                <div class="subscription-section">
                    <button class="subscription-button" disabled>加载中...</button>
                </div>
            `;
        }

        // 根据订阅状态显示相应按钮
        const isSubscribed = this.subscriptionStatus.is_subscribed;
        const buttonText = isSubscribed ? '取消订阅' : '订阅';
        const buttonClass = isSubscribed ? 'subscription-button unsubscribe' : 'subscription-button';

        return `
            <div class="subscription-section">
                <button class="${buttonClass}" onclick="this.getRootNode().host.handleSubscription()">
                    ${buttonText}
                </button>
            </div>
        `;
    }

    getDaysSinceCreation() {
        if (!this.blogData.createtime) return 0;
        const createDate = new Date(this.blogData.createtime);
        const now = new Date();
        const diffTime = Math.abs(now - createDate);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }

    updatePageTitle() {
        if (this.blogData && this.blogData.name) {
            const blogName = this.blogData.name;
            document.title = `${blogName} - BlogN`;
        }
    }

    /**
     * 加载订阅状态
     */
    async loadSubscriptionStatus() {
        try {
            // 检查UserManager是否可用
            if (typeof UserManager === 'undefined') {
                console.error('UserManager not available');
                this.subscriptionStatus = null;
                return;
            }

            // 检查用户是否登录
            if (!UserManager.isLoggedIn()) {
                this.subscriptionStatus = null;
                return;
            }

            // 检查是否是当前用户的博客
            const currentUser = UserManager.getCurrentUser();
            if (currentUser && currentUser.projectid == this.projectId) {
                this.isCurrentUserBlog = true;
                this.subscriptionStatus = null;
                return;
            }

            // 获取订阅状态
            const headers = UserManager.createHeaders();
            const response = await fetch(`/api/subscriptions/status/${this.projectId}`, { headers });
            
            if (response.ok) {
                this.subscriptionStatus = await response.json();
            } else {
                console.error('Failed to load subscription status:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error response:', errorText);
                this.subscriptionStatus = null;
            }
        } catch (error) {
            console.error('Error loading subscription status:', error);
            this.subscriptionStatus = null;
        }
    }

    /**
     * 处理订阅操作
     */
    async handleSubscription() {
        if (!UserManager.isLoggedIn()) {
            alert('请先登录');
            return;
        }

        if (this.isCurrentUserBlog) {
            alert('不能订阅自己的博客');
            return;
        }

        try {
            const headers = UserManager.createHeaders();
            let response;
            
            if (this.subscriptionStatus && this.subscriptionStatus.is_subscribed) {
                // 取消订阅
                response = await fetch(`/api/subscriptions/unsubscribe/${this.projectId}`, {
                    method: 'DELETE',
                    headers
                });
            } else {
                // 订阅
                response = await fetch(`/api/subscriptions/subscribe/${this.projectId}`, {
                    method: 'POST',
                    headers
                });
            }

            if (response.ok) {
                const result = await response.json();
                console.log(result.message);
                
                // 重新加载订阅状态
                await this.loadSubscriptionStatus();
                this.render();
            } else {
                const error = await response.json();
                alert(error.detail || '操作失败');
            }
        } catch (error) {
            console.error('Subscription error:', error);
            alert('操作失败，请重试');
        }
    }
}

customElements.define('blog-header-card', BlogHeaderCard);
