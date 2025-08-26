class UserProfileCard extends BaseComponent {
    constructor() {
        super();
        this.userData = null;
        this.projectData = null;
    }

    async connectedCallback() {
        try {
            this.render();
            await this.loadUserData();
        } catch (error) {
            console.error('UserProfileCard connectedCallback 错误:', error);
        }
    }

    async loadUserData() {
        try {
            // 从localStorage获取当前用户信息
            const userInfo = localStorage.getItem('user_info');
            
            if (!userInfo) {
                // 在开发环境中使用测试数据
                this.userData = {
                    id: 5503,
                    name: 'hjy12227',
                    email: '2465226798@qq.com',
                    state: 1,
                    regtime: '2016-12-19T19:15:33',
                    iplog: '118.163.0.211',
                    point: 0,
                    lastupdate: '2025-08-25T21:03:11.511482',
                    intropiid: 0
                };
                this.render();
                return;
            }

            const currentUser = JSON.parse(userInfo);
            const userId = currentUser.id;

            // 获取用户详细信息
            const userResponse = await fetch(`/api/users/${userId}`);
            
            if (!userResponse.ok) {
                throw new Error(`获取用户信息失败: ${userResponse.status}`);
            }
            
            this.userData = await userResponse.json();

            // 获取用户的博客信息
            const projectResponse = await fetch(`/api/projects/user/${userId}`);
            
            if (projectResponse.ok) {
                this.projectData = await projectResponse.json();
            }

            this.render();
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
                    <span class="profile-value">${this.escapeHtml(this.userData.email || '未设置')}</span>
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
                    <span class="profile-label">最后登录</span>
                    <span class="profile-value">${this.formatDateTime(this.userData.iplog)}</span>
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
                        ${this.userData.intropiid ? '已设置' : '未设置'}
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
