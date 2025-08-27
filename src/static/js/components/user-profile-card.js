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

    /**
     * 获取身份文本
     */
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
                    justify-content: space-between;
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
                
                .card-actions {
                    display: flex;
                    gap: var(--spacing-2);
                }
                
                .btn {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    padding: var(--spacing-2) var(--spacing-3);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    border-radius: var(--radius-md);
                    border: 1px solid transparent;
                    cursor: pointer;
                    transition: all var(--transition-fast);
                    text-decoration: none;
                    line-height: 1;
                }
                
                .btn-warning {
                    background-color: var(--warning-color, #f59e0b);
                    color: white;
                    border-color: var(--warning-color, #f59e0b);
                }
                
                .btn-warning:hover {
                    background-color: var(--warning-hover, #d97706);
                    border-color: var(--warning-hover, #d97706);
                }
                
                .btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
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
                
                .reset-password-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                
                .reset-password-modal.show {
                    display: flex;
                }
                
                .reset-password-content {
                    background: white;
                    padding: var(--spacing-6);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-xl);
                    max-width: 400px;
                    width: 90%;
                }
                
                .reset-password-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    margin-bottom: var(--spacing-4);
                    color: var(--gray-900);
                }
                
                .reset-password-form {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }
                
                .form-group {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-2);
                }
                
                .form-label {
                    font-weight: 500;
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                }
                
                .form-input {
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    transition: border-color var(--transition-fast);
                }
                
                .form-input:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                }
                
                .reset-password-actions {
                    display: flex;
                    gap: var(--spacing-3);
                    justify-content: flex-end;
                    margin-top: var(--spacing-4);
                }
                
                .btn-secondary {
                    background-color: var(--gray-100);
                    color: var(--gray-700);
                    border-color: var(--gray-300);
                }
                
                .btn-secondary:hover {
                    background-color: var(--gray-200);
                    border-color: var(--gray-400);
                }
                
                .btn-danger {
                    background-color: var(--error-color, #ef4444);
                    color: white;
                    border-color: var(--error-color, #ef4444);
                }
                
                .btn-danger:hover {
                    background-color: var(--error-hover, #dc2626);
                    border-color: var(--error-hover, #dc2626);
                }
            </style>
            
            <div class="card-header">
                <h2 class="card-title">个人资料</h2>
                ${this.canResetPassword() ? `
                    <div class="card-actions">
                        <button class="btn btn-danger" id="resetPasswordBtn">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 4v6h6"></path>
                                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                            </svg>
                            重置密码
                        </button>
                    </div>
                ` : ''}
            </div>

            <div class="profile-grid">
                <div class="profile-item">
                    <span class="profile-label">用户姓名</span>
                    <span class="profile-value">${this.escapeHtml(this.userData.name || '未设置')}</span>
                </div>

                <div class="profile-item">
                    <span class="profile-label">电子邮件</span>
                    <span class="profile-value">${this.userData.hasOwnProperty('email') ? (this.userData.email ? this.escapeHtml(this.userData.email) : '未设置') : '无权限查看'}</span>
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
                    <span class="profile-value">${this.userData.hasOwnProperty('iplog') ? (this.userData.iplog ? this.escapeHtml(this.userData.iplog) : '未知') : '无权限查看'}</span>
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
            
            <!-- 重置密码模态框 -->
            <div class="reset-password-modal" id="resetPasswordModal">
                <div class="reset-password-content">
                    <h3 class="reset-password-title">重置密码</h3>
                    <form class="reset-password-form" id="resetPasswordForm">
                        <div class="form-group">
                            <label class="form-label" for="newPassword">新密码</label>
                            <input type="password" id="newPassword" class="form-input" required minlength="6" placeholder="请输入新密码">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="confirmPassword">确认密码</label>
                            <input type="password" id="confirmPassword" class="form-input" required minlength="6" placeholder="请再次输入新密码">
                        </div>
                        <div class="reset-password-actions">
                            <button type="button" class="btn btn-secondary" id="cancelResetBtn">取消</button>
                            <button type="submit" class="btn btn-danger" id="confirmResetBtn">确认重置</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // 添加事件监听器
        this.addEventListeners();
    }

    /**
     * 检查当前用户是否有权限重置密码
     */
    canResetPassword() {
        try {
            // 获取当前登录用户信息
            const userInfo = localStorage.getItem('user_info');
            if (!userInfo) return false;
            
            const currentUser = JSON.parse(userInfo);
            
            // 管理员可以重置任何用户的密码
            if (currentUser.state === 10) return true;
            
            // 普通用户只能重置自己的密码
            if (currentUser.state === 1 && currentUser.id === this.userData.id) return true;
            
            return false;
        } catch (error) {
            console.error('检查重置密码权限失败:', error);
            return false;
        }
    }

    /**
     * 添加事件监听器
     */
    addEventListeners() {
        // 重置密码按钮
        const resetPasswordBtn = this.shadowRoot.querySelector('#resetPasswordBtn');
        if (resetPasswordBtn) {
            resetPasswordBtn.addEventListener('click', () => {
                this.showResetPasswordModal();
            });
        }

        // 取消重置密码
        const cancelResetBtn = this.shadowRoot.querySelector('#cancelResetBtn');
        if (cancelResetBtn) {
            cancelResetBtn.addEventListener('click', () => {
                this.hideResetPasswordModal();
            });
        }

        // 确认重置密码 - 现在在showResetPasswordModal中动态绑定
        // const resetPasswordForm = this.shadowRoot.querySelector('#resetPasswordForm');
        // if (resetPasswordForm) {
        //     resetPasswordForm.addEventListener('submit', (e) => {
        //         e.preventDefault();
        //         this.handleResetPassword();
        //     });
        // }

        // 点击模态框外部关闭
        const modal = this.shadowRoot.querySelector('#resetPasswordModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideResetPasswordModal();
                }
            });
        }
    }

    /**
     * 显示重置密码模态框
     */
    showResetPasswordModal() {
        const modal = this.shadowRoot.querySelector('#resetPasswordModal');
        if (modal) {
            modal.classList.add('show');
            // 清除之前的错误信息
            this.clearResetPasswordError();
            
            // 绑定确认按钮的点击事件
            const confirmBtn = modal.querySelector('#confirmResetBtn');
            if (confirmBtn) {
                // 移除之前的事件监听器（如果有的话）
                if (this.handleConfirmClick) {
                    confirmBtn.removeEventListener('click', this.handleConfirmClick);
                }
                
                // 添加新的事件监听器
                this.handleConfirmClick = (e) => {
                    e.preventDefault();
                    this.handleResetPassword();
                };
                confirmBtn.addEventListener('click', this.handleConfirmClick);
            }
            
            // 聚焦到第一个输入框
            const firstInput = modal.querySelector('#newPassword');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    /**
     * 隐藏重置密码模态框
     */
    hideResetPasswordModal() {
        const modal = this.shadowRoot.querySelector('#resetPasswordModal');
        if (modal) {
            modal.classList.remove('show');
            // 清空表单
            const form = modal.querySelector('#resetPasswordForm');
            if (form) {
                form.reset();
            }
            // 清除错误信息
            this.clearResetPasswordError();
        }
    }

    /**
     * 清除重置密码错误信息
     */
    clearResetPasswordError() {
        const modal = this.shadowRoot.querySelector('#resetPasswordModal');
        if (modal) {
            const errorDiv = modal.querySelector('.reset-password-error');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }

    /**
     * 处理重置密码
     */
    async handleResetPassword() {
        const newPassword = this.shadowRoot.querySelector('#newPassword').value;
        const confirmPassword = this.shadowRoot.querySelector('#confirmPassword').value;

        // 清除之前的错误信息
        this.clearResetPasswordError();

        // 验证密码
        if (newPassword.length < 6) {
            this.showResetPasswordError('密码长度至少6位');
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showResetPasswordError('两次输入的密码不一致');
            return;
        }

        try {
            // 获取当前用户token
            const token = localStorage.getItem('access_token');
            if (!token) {
                this.showResetPasswordError('请先登录');
                return;
            }

            // 调用重置密码API
            const response = await fetch(`/api/users/${this.userData.id}/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    new_password: newPassword
                })
            });

            if (response.ok) {
                this.showResetPasswordSuccess('密码重置成功！');
                this.hideResetPasswordModal();
            } else {
                const errorData = await response.json();
                this.showResetPasswordError(errorData.detail || '密码重置失败');
            }
        } catch (error) {
            console.error('重置密码失败:', error);
            this.showResetPasswordError('网络错误，请稍后重试');
        }
    }

    /**
     * 显示重置密码错误信息
     */
    showResetPasswordError(message) {
        // 在模态框中显示错误信息
        const modal = this.shadowRoot.querySelector('#resetPasswordModal');
        if (modal) {
            let errorDiv = modal.querySelector('.reset-password-error');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'reset-password-error';
                // 使用内联样式，确保不被CSS覆盖
                errorDiv.style.color = '#ef4444';
                errorDiv.style.fontSize = '14px';
                errorDiv.style.margin = '12px 0';
                errorDiv.style.textAlign = 'center';
                errorDiv.style.padding = '12px';
                errorDiv.style.backgroundColor = '#fef2f2';
                errorDiv.style.border = '1px solid #ef4444';
                errorDiv.style.borderRadius = '6px';
                errorDiv.style.fontWeight = '500';
                errorDiv.style.display = 'block';
                
                // 将错误信息插入到表单的第一个输入框之前
                const form = modal.querySelector('#resetPasswordForm');
                if (form) {
                    const firstInputGroup = form.querySelector('.form-group');
                    if (firstInputGroup) {
                        form.insertBefore(errorDiv, firstInputGroup);
                    } else {
                        form.insertBefore(errorDiv, form.firstChild);
                    }
                }
            }
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    /**
     * 显示重置密码成功信息
     */
    showResetPasswordSuccess(message) {
        // 显示全局成功提示
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
            font-size: 14px;
            font-weight: 500;
            min-width: 200px;
            text-align: center;
        `;
        successDiv.textContent = message;
        
        document.body.appendChild(successDiv);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
        
        // 添加点击关闭功能
        successDiv.addEventListener('click', () => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        });
        
        // 添加鼠标悬停样式
        successDiv.style.cursor = 'pointer';
        successDiv.style.transition = 'all 0.2s ease';
        
        successDiv.addEventListener('mouseenter', () => {
            successDiv.style.transform = 'scale(1.05)';
            successDiv.style.boxShadow = '0 6px 16px rgba(0,0,0,0.2)';
        });
        
        successDiv.addEventListener('mouseleave', () => {
            successDiv.style.transform = 'scale(1)';
            successDiv.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        });
    }

    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="error">${this.escapeHtml(message)}</div>
        `;
    }
}

customElements.define('user-profile-card', UserProfileCard);
