/**
 * 登录模态框组件
 */

class LoginModal extends BaseComponent {
    constructor() {
        super();
        this.isVisible = false;
        this.isLoading = false;
        this.returnUrl = null;
    }

    connectedCallback() {
        this.render();
        this.addEventListeners();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 1000;
                    align-items: center;
                    justify-content: center;
                }

                :host([visible]) {
                    display: flex;
                }

                .modal-container {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-xl);
                    width: 90%;
                    max-width: 400px;
                    max-height: 90vh;
                    overflow-y: auto;
                    position: relative;
                }

                .modal-header {
                    padding: var(--spacing-6);
                    border-bottom: 1px solid var(--gray-200);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }

                .modal-title {
                    font-size: var(--font-size-xl);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                }

                .close-button {
                    background: none;
                    border: none;
                    font-size: var(--font-size-xl);
                    color: var(--gray-500);
                    cursor: pointer;
                    padding: var(--spacing-1);
                    border-radius: var(--radius-md);
                    transition: var(--transition-fast);
                }

                .close-button:hover {
                    background: var(--gray-100);
                    color: var(--gray-700);
                }

                .modal-body {
                    padding: var(--spacing-6);
                }

                .form-group {
                    margin-bottom: var(--spacing-4);
                }

                .form-label {
                    display: block;
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-2);
                }

                .form-input {
                    width: 100%;
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    transition: var(--transition-fast);
                    box-sizing: border-box;
                }

                .form-input:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px var(--primary-color-alpha);
                }

                .form-input.error {
                    border-color: var(--red-500);
                }

                .error-message {
                    color: var(--red-500);
                    font-size: var(--font-size-sm);
                    margin-top: var(--spacing-1);
                    display: none;
                }

                .error-message.show {
                    display: block;
                }

                .login-button {
                    width: 100%;
                    background: var(--primary-color);
                    color: var(--white);
                    border: none;
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    cursor: pointer;
                    transition: var(--transition-fast);
                    margin-top: var(--spacing-4);
                }

                .login-button:hover:not(:disabled) {
                    background: var(--primary-hover);
                }

                .login-button:disabled {
                    background: var(--gray-400);
                    cursor: not-allowed;
                }

                .loading-spinner {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid var(--white);
                    border-top: 2px solid transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: var(--spacing-2);
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .modal-footer {
                    padding: var(--spacing-4) var(--spacing-6);
                    border-top: 1px solid var(--gray-200);
                    text-align: center;
                }

                .footer-text {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                }

                .footer-link {
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                }

                .footer-link:hover {
                    text-decoration: underline;
                }
            </style>

            <div class="modal-container">
                <div class="modal-header">
                    <h2 class="modal-title">用户登录</h2>
                    <button class="close-button" aria-label="关闭">×</button>
                </div>

                <div class="modal-body">
                    <form id="loginForm">
                        <div class="form-group">
                            <label class="form-label" for="username">用户名或邮箱</label>
                            <input 
                                type="text" 
                                id="username" 
                                name="username" 
                                class="form-input" 
                                placeholder="请输入用户名或邮箱"
                                required
                            >
                            <div class="error-message" id="usernameError"></div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="password">密码</label>
                            <input 
                                type="password" 
                                id="password" 
                                name="password" 
                                class="form-input" 
                                placeholder="请输入密码"
                                required
                            >
                            <div class="error-message" id="passwordError"></div>
                        </div>

                        <button type="submit" class="login-button" id="loginButton">
                            <span class="loading-spinner" id="loadingSpinner" style="display: none;"></span>
                            <span id="buttonText">登录</span>
                        </button>
                    </form>
                </div>

                <div class="modal-footer">
                    <p class="footer-text">
                        还没有账号？ 
                        <a href="#" class="footer-link" id="registerLink">立即注册</a>
                    </p>
                </div>
            </div>
        `;
    }

    addEventListeners() {
        const closeButton = this.shadowRoot.querySelector('.close-button');
        closeButton.addEventListener('click', () => this.hide());

        this.addEventListener('click', (e) => {
            if (e.target === this) {
                this.hide();
            }
        });

        const form = this.shadowRoot.querySelector('#loginForm');
        form.addEventListener('submit', (e) => this.handleLogin(e));

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });
    }

    show(returnUrl = null) {
        this.isVisible = true;
        this.returnUrl = returnUrl;
        this.setAttribute('visible', '');
        this.resetForm();
        
        setTimeout(() => {
            const usernameInput = this.shadowRoot.querySelector('#username');
            usernameInput.focus();
        }, 100);
    }

    hide() {
        this.isVisible = false;
        this.removeAttribute('visible');
        this.returnUrl = null;
    }

    resetForm() {
        const form = this.shadowRoot.querySelector('#loginForm');
        form.reset();
        this.clearErrors();
        this.setLoading(false);
    }

    clearErrors() {
        const errorElements = this.shadowRoot.querySelectorAll('.error-message');
        errorElements.forEach(el => {
            el.textContent = '';
            el.classList.remove('show');
        });
        
        const inputs = this.shadowRoot.querySelectorAll('.form-input');
        inputs.forEach(input => input.classList.remove('error'));
    }

    showError(field, message) {
        const input = this.shadowRoot.querySelector(`#${field}`);
        const errorElement = this.shadowRoot.querySelector(`#${field}Error`);
        
        if (input && errorElement) {
            input.classList.add('error');
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        const button = this.shadowRoot.querySelector('#loginButton');
        const spinner = this.shadowRoot.querySelector('#loadingSpinner');
        const buttonText = this.shadowRoot.querySelector('#buttonText');
        
        if (loading) {
            button.disabled = true;
            spinner.style.display = 'inline-block';
            buttonText.textContent = '登录中...';
        } else {
            button.disabled = false;
            spinner.style.display = 'none';
            buttonText.textContent = '登录';
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        if (this.isLoading) return;
        
        this.clearErrors();
        
        const username = this.shadowRoot.querySelector('#username').value.trim();
        const password = this.shadowRoot.querySelector('#password').value;
        
        if (!username) {
            this.showError('username', '请输入用户名或邮箱');
            return;
        }
        
        if (!password) {
            this.showError('password', '请输入密码');
            return;
        }
        
        this.setLoading(true);
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username_or_email: username,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleLoginSuccess(data);
            } else {
                this.handleLoginError(data.detail || '登录失败，请检查用户名和密码');
            }
            
        } catch (error) {
            console.error('Login error:', error);
            this.handleLoginError('网络错误，请稍后重试');
        } finally {
            this.setLoading(false);
        }
    }

    handleLoginSuccess(data) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_info', JSON.stringify(data.user));
        
        const event = new CustomEvent('userLoginSuccess', {
            detail: data.user,
            bubbles: true
        });
        document.dispatchEvent(event);
        
        this.hide();
        this.showSuccessMessage('登录成功！');
        this.handleRedirect();
    }

    handleLoginError(message) {
        this.showError('username', message);
        const passwordInput = this.shadowRoot.querySelector('#password');
        passwordInput.focus();
    }

    handleRedirect() {
        if (this.returnUrl) {
            window.location.href = this.returnUrl;
        } else {
            window.location.reload();
        }
    }

    showSuccessMessage(message) {
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
        `;
        successDiv.textContent = message;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
    }
}

customElements.define('login-modal', LoginModal);
