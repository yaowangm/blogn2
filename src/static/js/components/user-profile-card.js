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
                // 从UserManager获取当前用户信息
                if (!UserManager.isLoggedIn()) {
                    // 如果没有目标用户ID且未登录，显示错误
                    this.showError('无法获取用户ID');
                    return;
                }

                const currentUser = UserManager.getCurrentUser();
                userId = currentUser.id;
            }

            // 获取用户详细信息
            const headers = UserManager.createHeaders();
            
            const userResponse = await fetch(`/api/users/${userId}`, { headers });
            
            if (!userResponse.ok) {
                throw new Error(`获取用户信息失败: ${userResponse.status}`);
            }
            
            this.userData = await userResponse.json();

            if (this.userData.projectid) {
                const projectData = await BaseComponent.getProject(this.userData.projectid);
                if (projectData) this.projectData = projectData;
            } else {
                // 用户没有博客
                this.projectData = null;
            }

            this.render();
            
            // 更新页面标题
            if (this.userData && this.userData.name) {
                document.title = `${this.userData.name}的个人资料 - BlogN`;
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

    getCardStyles() {
        return `
            @import url('/static/css/common-components.css');
            :host { display: block; }
            .card-title {
                display: flex;
                align-items: center;
                gap: var(--spacing-2);
            }
            .title-icon {
                width: 20px;
                height: 20px;
                color: var(--primary-color);
                flex-shrink: 0;
            }
            .title-icon svg {
                width: 100%;
                height: 100%;
                display: block;
            }
            .detail-list {
                margin: 0;
                padding: 0;
            }
            .detail-row {
                display: flex;
                align-items: flex-start;
                gap: var(--spacing-3);
                padding: var(--spacing-2) 0;
                border-bottom: 1px solid var(--gray-100);
            }
            .detail-row:last-child {
                border-bottom: none;
                padding-bottom: 0;
            }
            .detail-row:first-child {
                padding-top: 0;
            }
            .detail-label {
                min-width: 88px;
                flex-shrink: 0;
                font-weight: 500;
                color: var(--gray-500);
                font-size: var(--font-size-sm);
            }
            .detail-value {
                flex: 1;
                min-width: 0;
                color: var(--gray-900);
                font-size: var(--font-size-sm);
                word-break: break-word;
            }
            .detail-value.state-admin {
                color: var(--state-admin);
                font-weight: 600;
            }
            .detail-value.state-user {
                color: var(--state-user);
                font-weight: 600;
            }
            .detail-value.state-frozen {
                color: var(--state-frozen);
                font-weight: 600;
            }
            .intro-link {
                color: var(--primary-color);
                text-decoration: none;
                font-weight: 500;
            }
            .intro-link:hover {
                color: var(--primary-hover);
                text-decoration: underline;
            }
            .loading, .error {
                text-align: center;
                padding: var(--spacing-8);
                color: var(--gray-500);
            }
            .error { color: var(--error-color); }
            .modal-overlay {
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.5);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            .modal-overlay.show { display: flex; }
            .modal-panel {
                background: var(--white);
                padding: var(--spacing-4);
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-xl);
                border: 1px solid var(--gray-200);
                max-width: 400px;
                width: 90%;
            }
            .modal-title {
                font-size: var(--font-size-base);
                font-weight: 600;
                margin: 0 0 var(--spacing-4);
                color: var(--gray-900);
            }
            .modal-form {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-3);
            }
            .form-group {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-1);
            }
            .form-label {
                font-weight: 500;
                color: var(--gray-700);
                font-size: var(--font-size-sm);
            }
            .form-input {
                padding: var(--spacing-2) var(--spacing-3);
                border: 1px solid var(--gray-300);
                border-radius: var(--radius-md);
                font-size: var(--font-size-sm);
            }
            .form-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px var(--primary-color-10);
            }
            .modal-actions {
                display: flex;
                gap: var(--spacing-2);
                justify-content: flex-end;
                margin-top: var(--spacing-2);
            }
            .btn svg {
                width: 16px;
                height: 16px;
                flex-shrink: 0;
            }
        `;
    }

    render() {
        if (!this.userData) {
            this.shadowRoot.innerHTML = `
                <style>${this.getCardStyles()}</style>
                <div class="card"><div class="loading">加载中...</div></div>
            `;
            return;
        }

        const safeName = this.escapeHtml(this.userData.name || '未设置');
        const emailValue = this.userData.hasOwnProperty('email')
            ? (this.userData.email ? this.escapeHtml(this.userData.email) : '未设置')
            : '无权限查看';
        const ipValue = this.userData.hasOwnProperty('iplog')
            ? (this.userData.iplog ? this.escapeHtml(this.userData.iplog) : '未知')
            : '无权限查看';
        const stateClass = this.userData.state === 10 ? 'admin' : this.userData.state === 1 ? 'user' : 'frozen';
        const introHtml = this.userData.intropiid
            ? `<a href="/article/${this.userData.intropiid}" class="intro-link" target="_blank" rel="noopener noreferrer">查看自我介绍</a>`
            : '未设置';

        this.shadowRoot.innerHTML = `
            <style>${this.getCardStyles()}</style>
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="title-icon">${Icons.user}</span>
                        个人资料
                    </h2>
                    ${this.canResetPassword() || this.canUpdateEmail() ? `
                        <div class="btn-toolbar">
                            ${this.canUpdateEmail() ? `
                                <button type="button" class="btn btn-secondary btn-sm" id="updateEmailBtn">
                                    ${Icons.subscription}
                                    修改邮箱
                                </button>
                            ` : ''}
                            ${this.canResetPassword() ? `
                                <button type="button" class="btn btn-danger btn-sm" id="resetPasswordBtn">
                                    ${Icons.settings}
                                    重置密码
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="card-body">
                    <dl class="detail-list">
                        <div class="detail-row">
                            <dt class="detail-label">用户姓名</dt>
                            <dd class="detail-value">${safeName}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">电子邮件</dt>
                            <dd class="detail-value">${emailValue}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">身份</dt>
                            <dd class="detail-value state-${stateClass}">${this.getStateText(this.userData.state)}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">注册时间</dt>
                            <dd class="detail-value">${this.formatDateTime(this.userData.regtime)}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">最后登录IP</dt>
                            <dd class="detail-value">${ipValue}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">积分</dt>
                            <dd class="detail-value">${this.userData.point || 0}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">最后更新</dt>
                            <dd class="detail-value">${this.formatDateTime(this.userData.lastupdate)}</dd>
                        </div>
                        <div class="detail-row">
                            <dt class="detail-label">自我介绍</dt>
                            <dd class="detail-value">${introHtml}</dd>
                        </div>
                    </dl>
                </div>
            </div>
            
            <div class="modal-overlay" id="resetPasswordModal">
                <div class="modal-panel">
                    <h3 class="modal-title">重置密码</h3>
                    <form class="modal-form" id="resetPasswordForm">
                        <div class="form-group">
                            <label class="form-label" for="newPassword">新密码</label>
                            <input type="password" id="newPassword" class="form-input" required minlength="6" placeholder="请输入新密码">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="confirmPassword">确认密码</label>
                            <input type="password" id="confirmPassword" class="form-input" required minlength="6" placeholder="请再次输入新密码">
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary btn-sm" id="cancelResetBtn">取消</button>
                            <button type="submit" class="btn btn-danger btn-sm" id="confirmResetBtn">确认重置</button>
                        </div>
                    </form>
                </div>
            </div>

            <div class="modal-overlay" id="updateEmailModal">
                <div class="modal-panel">
                    <h3 class="modal-title">修改邮箱</h3>
                    <form class="modal-form" id="updateEmailForm">
                        <div class="form-group">
                            <label class="form-label" for="currentEmail">当前邮箱</label>
                            <input type="email" id="currentEmail" class="form-input" readonly value="${this.userData.hasOwnProperty('email') ? (this.userData.email || '未设置') : '无权限查看'}">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="newEmail">新邮箱</label>
                            <input type="email" id="newEmail" class="form-input" required placeholder="请输入新邮箱地址">
                        </div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary btn-sm" id="cancelUpdateEmailBtn">取消</button>
                            <button type="submit" class="btn btn-primary btn-sm" id="confirmUpdateEmailBtn">确认修改</button>
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
            if (!UserManager.isLoggedIn()) return false;
            
            const currentUser = UserManager.getCurrentUser();
            
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
     * 检查当前用户是否有权限修改邮箱
     */
    canUpdateEmail() {
        try {
            // 获取当前登录用户信息
            if (!UserManager.isLoggedIn()) return false;
            
            const currentUser = UserManager.getCurrentUser();
            
            // 管理员可以修改任何用户的邮箱
            if (currentUser.state === 10) return true;
            
            // 普通用户只能修改自己的邮箱
            if (currentUser.state === 1 && currentUser.id === this.userData.id) return true;
            
            return false;
        } catch (error) {
            console.error('检查修改邮箱权限失败:', error);
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

        // 修改邮箱按钮
        const updateEmailBtn = this.shadowRoot.querySelector('#updateEmailBtn');
        if (updateEmailBtn) {
            updateEmailBtn.addEventListener('click', () => {
                this.showUpdateEmailModal();
            });
        }

        // 取消重置密码
        const cancelResetBtn = this.shadowRoot.querySelector('#cancelResetBtn');
        if (cancelResetBtn) {
            cancelResetBtn.addEventListener('click', () => {
                this.hideResetPasswordModal();
            });
        }

        // 取消修改邮箱
        const cancelUpdateEmailBtn = this.shadowRoot.querySelector('#cancelUpdateEmailBtn');
        if (cancelUpdateEmailBtn) {
            cancelUpdateEmailBtn.addEventListener('click', () => {
                this.hideUpdateEmailModal();
            });
        }

        // 点击模态框外部关闭
        const resetPasswordModal = this.shadowRoot.querySelector('#resetPasswordModal');
        if (resetPasswordModal) {
            resetPasswordModal.addEventListener('click', (e) => {
                if (e.target === resetPasswordModal) {
                    this.hideResetPasswordModal();
                }
            });
        }

        const updateEmailModal = this.shadowRoot.querySelector('#updateEmailModal');
        if (updateEmailModal) {
            updateEmailModal.addEventListener('click', (e) => {
                if (e.target === updateEmailModal) {
                    this.hideUpdateEmailModal();
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
     * 显示修改邮箱模态框
     */
    showUpdateEmailModal() {
        const modal = this.shadowRoot.querySelector('#updateEmailModal');
        if (modal) {
            modal.classList.add('show');
            // 清除之前的错误信息
            this.clearUpdateEmailError();
            
            // 绑定确认按钮的点击事件
            const confirmBtn = modal.querySelector('#confirmUpdateEmailBtn');
            if (confirmBtn) {
                // 移除之前的事件监听器（如果有的话）
                if (this.handleUpdateEmailClick) {
                    confirmBtn.removeEventListener('click', this.handleUpdateEmailClick);
                }
                
                // 添加新的事件监听器
                this.handleUpdateEmailClick = (e) => {
                    e.preventDefault();
                    this.handleUpdateEmail();
                };
                confirmBtn.addEventListener('click', this.handleUpdateEmailClick);
            }
            
            // 聚焦到新邮箱输入框
            const newEmailInput = modal.querySelector('#newEmail');
            if (newEmailInput) {
                newEmailInput.focus();
            }
        }
    }

    /**
     * 隐藏修改邮箱模态框
     */
    hideUpdateEmailModal() {
        const modal = this.shadowRoot.querySelector('#updateEmailModal');
        if (modal) {
            modal.classList.remove('show');
            // 清空表单
            const form = modal.querySelector('#updateEmailForm');
            if (form) {
                form.reset();
            }
            // 清除错误信息
            this.clearUpdateEmailError();
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
     * 清除修改邮箱错误信息
     */
    clearUpdateEmailError() {
        const modal = this.shadowRoot.querySelector('#updateEmailModal');
        if (modal) {
            const errorDiv = modal.querySelector('.update-email-error');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }

    /**
     * 密码规则校验（与注册、邮件重置一致，使用共享 passwordRuleError）
     * @param {string} pwd
     * @returns {string|null} 错误信息或 null
     */
    _passwordRuleError(pwd) {
        return window.passwordRuleError(pwd);
    }

    /**
     * 处理重置密码
     */
    async handleResetPassword() {
        const newPassword = this.shadowRoot.querySelector('#newPassword').value;
        const confirmPassword = this.shadowRoot.querySelector('#confirmPassword').value;

        // 清除之前的错误信息
        this.clearResetPasswordError();

        // 验证密码（与注册、邮件重置规则一致：8–30 字符，大小写+数字，可打印 ASCII）
        const pwdErr = this._passwordRuleError(newPassword);
        if (pwdErr) {
            this.showResetPasswordError(pwdErr);
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showResetPasswordError('两次输入的密码不一致');
            return;
        }

        try {
            // 获取当前用户token
            const token = UserManager.getAccessToken();
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
     * 处理修改邮箱
     */
    async handleUpdateEmail() {
        const newEmail = this.shadowRoot.querySelector('#newEmail').value;

        // 清除之前的错误信息
        this.clearUpdateEmailError();

        // 验证邮箱
        if (!newEmail) {
            this.showUpdateEmailError('新邮箱不能为空');
            return;
        }

        // 简单的邮箱格式验证
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(newEmail)) {
            this.showUpdateEmailError('邮箱格式不正确');
            return;
        }

        // 检查是否与当前邮箱相同
        const currentEmail = this.userData.email || '';
        if (newEmail === currentEmail) {
            this.showUpdateEmailError('新邮箱与当前邮箱相同');
            return;
        }

        try {
            // 获取当前用户token
            const token = UserManager.getAccessToken();
            if (!token) {
                this.showUpdateEmailError('请先登录');
                return;
            }

            // 调用修改邮箱API
            const response = await fetch(`/api/users/${this.userData.id}/update-email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    new_email: newEmail
                })
            });

            if (response.ok) {
                this.showUpdateEmailSuccess('邮箱修改成功！');
                this.hideUpdateEmailModal();
                // 重新加载用户数据以显示新邮箱
                await this.loadUserData();
            } else {
                const errorData = await response.json();
                this.showUpdateEmailError(errorData.detail || '邮箱修改失败');
            }
        } catch (error) {
            console.error('修改邮箱失败:', error);
            this.showUpdateEmailError('网络错误，请稍后重试');
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

    /**
     * 显示修改邮箱错误信息
     */
    showUpdateEmailError(message) {
        // 在模态框中显示错误信息
        const modal = this.shadowRoot.querySelector('#updateEmailModal');
        if (modal) {
            let errorDiv = modal.querySelector('.update-email-error');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'update-email-error';
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
                const form = modal.querySelector('#updateEmailForm');
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
     * 显示修改邮箱成功信息
     */
    showUpdateEmailSuccess(message) {
        // 显示全局成功提示
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f59e0b;
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
            <style>${this.getCardStyles()}</style>
            <div class="card"><div class="error">${this.escapeHtml(message)}</div></div>
        `;
    }
}

customElements.define('user-profile-card', UserProfileCard);
