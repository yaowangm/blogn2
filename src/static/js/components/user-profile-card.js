class UserProfileCard extends BaseComponent {
    constructor() {
        super();
        this.userData = null;
        this.projectData = null;
    }

    async connectedCallback() {
        try {
            this.render();
            
            // 如果在个人资料页面，等待targetUserIdReady事件
            if (window.location.pathname.startsWith('/profile')) {
                if (window.targetUserId) {
                    // 如果已经有targetUserId，直接加载数据
                    await this.loadUserData();
                } else {
                    // 等待targetUserIdReady事件
                    window.addEventListener('targetUserIdReady', async (event) => {
                        await this.loadUserData();
                    }, { once: true });
                }
            } else {
                // 不在个人资料页面，直接加载数据
                await this.loadUserData();
            }
        } catch (error) {
            console.error('UserProfileCard connectedCallback 错误:', error);
        }
    }

    async loadUserData() {
        try {
            // 优先使用全局目标用户ID，如果没有则使用当前登录用户
            let userId = window.targetUserId;
            
            if (!userId) {
                // 从localStorage获取当前用户信息
                const userInfo = localStorage.getItem('user_info');
                
                if (!userInfo) {
                    // 如果没有目标用户ID且未登录，显示错误
                    this.showError('无法获取用户ID');
                    return;
                }

                const currentUser = JSON.parse(userInfo);
                userId = currentUser.id;
            }

            // 获取用户详细信息
            const token = localStorage.getItem('access_token');
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const userResponse = await fetch(`/api/users/${userId}`, { headers });
            
            if (!userResponse.ok) {
                throw new Error(`获取用户信息失败: ${userResponse.status}`);
            }
            
            this.userData = await userResponse.json();

            // 获取用户的博客信息
            const projectResponse = await fetch(`/api/projects/user/${userId}`, { headers });
            
            if (projectResponse.ok) {
                this.projectData = await projectResponse.json();
            }

            this.render();
            
            // 更新页面标题
            if (this.userData && this.userData.name) {
                document.title = `${this.userData.name}的个人资料 - BlogN2`;
            }
        } catch (error) {
            console.error('加载用户数据失败:', error);
            this.showError('加载用户数据失败');
        }
    }

    getStateText(state) {
        switch (state) {
            case 10: return '管理员';
            case 1: return '普通用户';
            case 0: return '已冻结';
            default: return '未知';
        }
    }

    /**
     * 获取电子邮件显示文本
     * 区分"权限不够"和"根本没有设置"两种情况
     */
    getEmailDisplay() {
        // 检查当前用户是否有权限查看此字段
        const currentUserInfo = localStorage.getItem('user_info');
        if (currentUserInfo) {
            try {
                const currentUser = JSON.parse(currentUserInfo);
                // 如果是查看自己的资料或者是管理员，应该有权限看到所有字段
                if (currentUser.id === this.userData.id || currentUser.role === 'admin') {
                    return this.userData.email ? this.escapeHtml(this.userData.email) : '未设置';
                }
            } catch (error) {
                console.error('解析当前用户信息失败:', error);
            }
        }
        
        // 查看他人资料或未登录，根据返回的数据判断
        if (this.userData.email === null) {
            return '未显示'; // 权限不够，字段被隐藏
        } else if (this.userData.email === '') {
            return '未设置'; // 字段为空字符串，表示没有设置
        } else {
            return this.escapeHtml(this.userData.email); // 有数据，正常显示
        }
    }

    /**
     * 获取最后登录IP显示文本
     * 区分"权限不够"和"根本没有设置"两种情况
     */
    getIplogDisplay() {
        // 检查当前用户是否有权限查看此字段
        const currentUserInfo = localStorage.getItem('user_info');
        if (currentUserInfo) {
            try {
                const currentUser = JSON.parse(currentUserInfo);
                // 如果是查看自己的资料或者是管理员，应该有权限看到所有字段
                if (currentUser.id === this.userData.id || currentUser.role === 'admin') {
                    return this.userData.iplog ? this.escapeHtml(this.userData.iplog) : '未知';
                }
            } catch (error) {
                console.error('解析当前用户信息失败:', error);
            }
        }
        
        // 查看他人资料或未登录，根据返回的数据判断
        if (this.userData.iplog === null) {
            return '未显示'; // 权限不够，字段被隐藏
        } else if (this.userData.iplog === '') {
            return '未知'; // 字段为空字符串，表示没有设置
        } else {
            return this.escapeHtml(this.userData.iplog); // 有数据，正常显示
        }
    }

    formatDateTime(dateString) {
        if (!dateString) return '未设置';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    render() {
        if (!this.userData) {
            this.shadowRoot.innerHTML = `
                <div class="loading">加载中...</div>
            `;
            return;
        }

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    background: var(--card-bg);
                    border-radius: var(--card-radius);
                    box-shadow: var(--card-shadow);
                    padding: var(--card-padding);
                    margin-bottom: var(--card-margin);
                    border: 1px solid var(--card-border);
                }
                
                .card-header {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-bottom: var(--card-content-gap);
                    padding-bottom: var(--spacing-4);
                    border-bottom: 1px solid var(--card-header-border);
                }
                
                .card-title {
                    font-size: var(--card-title-size);
                    font-weight: var(--card-title-weight);
                    color: var(--card-title-color);
                    margin: 0;
                }
                
                .profile-grid {
                    display: grid;
                    gap: var(--card-content-gap);
                }
                
                .profile-item {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--spacing-3);
                }
                
                .profile-label {
                    min-width: 100px;
                    font-weight: 500;
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                }
                
                .profile-value {
                    flex: 1;
                    color: var(--gray-800);
                    font-size: var(--font-size-sm);
                    word-break: break-word;
                }
                
                .profile-value.state-admin {
                    color: var(--state-admin);
                    font-weight: 600;
                }
                
                .profile-value.state-user {
                    color: var(--state-user);
                    font-weight: 600;
                }
                
                .profile-value.state-frozen {
                    color: var(--state-frozen);
                    font-weight: 600;
                }
                
                .profile-value.intro {
                    font-style: italic;
                    color: var(--gray-500);
                    line-height: 1.5;
                }
                
                .intro-link {
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                    transition: color var(--transition-fast);
                }
                
                .intro-link:hover {
                    color: var(--primary-hover);
                    text-decoration: underline;
                }
                
                .loading, .error {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--loading-color);
                }
                
                .error {
                    color: var(--error-color);
                }
            </style>
            
            <div class="card-header">
                <h2 class="card-title">个人资料</h2>
            </div>

            <div class="profile-grid">
                <div class="profile-item">
                    <span class="profile-label">用户姓名</span>
                    <span class="profile-value">${this.escapeHtml(this.userData.name || '未设置')}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">电子邮件</span>
                    <span class="profile-value">${this.getEmailDisplay()}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">身份</span>
                    <span class="profile-value state-${this.userData.state === 10 ? 'admin' : this.userData.state === 1 ? 'user' : 'frozen'}">
                        ${this.getStateText(this.userData.state)}
                    </span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">注册时间</span>
                    <span class="profile-value">${this.formatDateTime(this.userData.regtime)}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">最后登录IP</span>
                    <span class="profile-value">${this.getIplogDisplay()}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">积分</span>
                    <span class="profile-value">${this.userData.point || 0}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">最后更新</span>
                    <span class="profile-value">${this.formatDateTime(this.userData.lastupdate)}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">自我介绍</span>
                    <span class="profile-value intro">
                        ${this.userData.intropiid ? 
                            `<a href="/article/${this.userData.intropiid}" class="intro-link" target="_blank" rel="noopener noreferrer">查看自我介绍</a>` : 
                            '未设置'
                        }
                    </span>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="error">${this.escapeHtml(message)}</div>
        `;
    }
}

customElements.define('user-profile-card', UserProfileCard);
