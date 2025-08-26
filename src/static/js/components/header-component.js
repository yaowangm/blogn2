class HeaderComponent extends BaseComponent {
    constructor() {
        super();
        this.siteName = '';
        this.logoUrl = '';
        this.isLoggedIn = false;
        this.userName = '';
        this.userInfo = null;
        this.loginModal = null;
    }

    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async connectedCallback() {
        await this.loadMetadata();
        this.checkAuthStatus();
        this.render();
        this.setupLoginModal();
        this.addGlobalEventListeners();
    }

    render() {
        const siteName = this.metadata?.site_name || 'BlogN';
        const logoUrl = this.getLogoUrl();
        
        // 检查图标库是否可用
        const hasIcons = typeof Icons !== 'undefined';
        const searchIcon = hasIcons ? Icons.search : this.getDefaultSearchIcon();
        const homeIcon = hasIcons ? Icons.home : this.getDefaultHomeIcon();
        const logoutIcon = hasIcons ? Icons.logout : this.getDefaultLogoutIcon();

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    background: var(--white);
                    border-bottom: 1px solid var(--gray-200);
                    box-shadow: var(--shadow-sm);
                    position: sticky;
                    top: 0;
                    z-index: 100;
                }

                .header-container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 var(--spacing-4);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    height: 64px;
                }

                .header-logo {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    text-decoration: none;
                    color: var(--gray-900);
                }

                .logo-icon {
                    width: 40px;
                    height: 40px;
                    border-radius: var(--radius-md);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .logo-icon img {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }

                .logo-text {
                    font-size: var(--font-size-xl);
                    font-weight: 700;
                    color: var(--gray-900);
                }

                .header-actions {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }

                .user-menu {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    position: relative;
                    cursor: pointer;
                    padding: var(--spacing-2);
                    border-radius: var(--radius-md);
                    transition: var(--transition-fast);
                }

                .user-menu:hover {
                    background: var(--gray-100);
                }

                .user-name {
                    font-weight: 500;
                    color: var(--gray-700);
                }

                .dropdown-arrow {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    transition: var(--transition-fast);
                }

                .user-menu.active .dropdown-arrow {
                    transform: rotate(180deg);
                }

                .dropdown-menu {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    background: var(--white);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    box-shadow: var(--shadow-lg);
                    min-width: 180px;
                    z-index: 1000;
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(-10px);
                    transition: var(--transition-fast);
                    margin-top: var(--spacing-1);
                }

                .user-menu.active .dropdown-menu {
                    opacity: 1;
                    visibility: visible;
                    transform: translateY(0);
                }

                .dropdown-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    padding: var(--spacing-3);
                    color: var(--gray-700);
                    text-decoration: none;
                    transition: var(--transition-fast);
                    border-radius: var(--radius-sm);
                    margin: var(--spacing-1);
                }

                .dropdown-item:hover {
                    background: var(--gray-100);
                    color: var(--gray-900);
                }

                .dropdown-icon {
                    width: 16px;
                    height: 16px;
                    flex-shrink: 0;
                    color: var(--gray-600);
                    transition: var(--transition-fast);
                }

                .dropdown-item:hover .dropdown-icon {
                    color: var(--gray-900);
                }

                .dropdown-divider {
                    height: 1px;
                    background: var(--gray-200);
                    margin: var(--spacing-2) var(--spacing-1);
                }

                .user-avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: var(--primary-color);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--white);
                    font-weight: 600;
                    font-size: var(--font-size-sm);
                    overflow: hidden;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 50%;
                }

                .avatar-placeholder {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--white);
                    font-weight: 600;
                    font-size: var(--font-size-sm);
                    border-radius: 50%;
                }

                .search-button {
                    background: transparent;
                    border: none;
                    color: var(--gray-600);
                    padding: var(--spacing-2);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: var(--transition-fast);
                }

                .search-button:hover {
                    background: var(--gray-100);
                    color: var(--gray-800);
                }

                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-2) var(--spacing-4);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    border-radius: var(--radius-md);
                    border: 1px solid transparent;
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                    line-height: 1;
                }

                .btn-primary {
                    background-color: var(--primary-color);
                    color: var(--white);
                    border-color: var(--primary-color);
                }

                .btn-primary:hover {
                    background-color: var(--primary-hover);
                    border-color: var(--primary-hover);
                }

                .btn-ghost {
                    background-color: transparent;
                    color: var(--gray-600);
                    border-color: transparent;
                }

                .btn-ghost:hover {
                    background-color: var(--gray-100);
                    color: var(--gray-800);
                }

                @media (max-width: 768px) {
                    .header-container {
                        padding: 0 var(--spacing-3);
                    }
                    
                    .header-actions {
                        gap: var(--spacing-2);
                    }
                }

                @media (max-width: 480px) {
                    .header-container {
                        padding: 0 var(--spacing-2);
                    }
                    
                    .logo-text {
                        font-size: var(--font-size-lg);
                    }
                    
                    .header-actions {
                        gap: var(--spacing-2);
                    }
                }
            </style>

            <div class="header-container">
                <a href="/" class="header-logo">
                    <div class="logo-icon">
                        <img src="${this.escapeHtml(logoUrl)}" alt="${this.escapeHtml(siteName)} Logo">
                    </div>
                    <span class="logo-text">${this.escapeHtml(siteName)}</span>
                </a>

                <div class="header-actions">
                    ${this.isLoggedIn ? `
                        <div class="user-menu" id="userMenu">
                            <div class="user-avatar">
                                ${(() => {
                                    if (this.userInfo && this.userInfo.avatar_url) {
                                        return `<img src="${this.escapeHtml(this.userInfo.avatar_url)}" alt="Avatar">`;
                                    } else {
                                        return `<div class="avatar-placeholder">${this.escapeHtml(this.userName.charAt(0))}</div>`;
                                    }
                                })()}
                            </div>
                            <span class="user-name">${this.escapeHtml(this.userName)}</span>
                            <div class="dropdown-arrow">▼</div>
                            
                            <!-- 下拉菜单 -->
                            <div class="dropdown-menu" id="dropdownMenu">
                                <a href="#" class="dropdown-item" id="searchMenuItem">
                                    ${searchIcon}
                                    搜索
                                </a>
                                <a href="/user" class="dropdown-item">
                                    ${homeIcon}
                                    我的首页
                                </a>
                                <div class="dropdown-divider"></div>
                                <a href="#" class="dropdown-item" id="logoutMenuItem">
                                    ${logoutIcon}
                                    退出
                                </a>
                            </div>
                        </div>
                    ` : `
                        <button class="btn btn-primary" id="loginButton">登录</button>
                    `}
                </div>
            </div>
        `;

        // 添加事件监听器
        this.addEventListeners();
    }

    addEventListeners() {
        // 用户菜单下拉功能
        const userMenu = this.shadowRoot.querySelector('#userMenu');
        if (userMenu) {
            userMenu.addEventListener('click', (e) => {
                e.stopPropagation();
                userMenu.classList.toggle('active');
            });
        }

        // 点击其他地方关闭下拉菜单
        document.addEventListener('click', (e) => {
            if (userMenu && !userMenu.contains(e.target)) {
                userMenu.classList.remove('active');
            }
        });

        // 搜索菜单项
        const searchMenuItem = this.shadowRoot.querySelector('#searchMenuItem');
        if (searchMenuItem) {
            searchMenuItem.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                // TODO: 实现搜索功能
                userMenu.classList.remove('active');
            });
        }

        // 退出菜单项
        const logoutMenuItem = this.shadowRoot.querySelector('#logoutMenuItem');
        if (logoutMenuItem) {
            logoutMenuItem.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.handleLogout();
                userMenu.classList.remove('active');
            });
        }

        // 登录按钮事件
        const loginButton = this.shadowRoot.querySelector('#loginButton');
        if (loginButton) {
            loginButton.addEventListener('click', () => this.showLoginModal());
        }
    }

    setupLoginModal() {
        // 检查 login-modal 组件是否已定义
        if (!customElements.get('login-modal')) {
            // 如果组件未定义，动态加载脚本
            const script = document.createElement('script');
            script.src = '/static/js/components/login-modal.js';
            script.onload = () => {
                // 脚本加载完成后创建模态框
                this.createLoginModal();
            };
            script.onerror = () => {
                console.error('Failed to load login-modal.js');
            };
            document.head.appendChild(script);
        } else {
            // 如果组件已定义，直接创建模态框
            this.createLoginModal();
        }
    }

    createLoginModal() {
        // 创建登录模态框
        this.loginModal = document.createElement('login-modal');
        document.body.appendChild(this.loginModal);
    }

    addGlobalEventListeners() {
        // 监听登录成功事件
        document.addEventListener('userLoginSuccess', (e) => {
            this.handleLoginSuccess(e.detail);
        });
    }

    checkAuthStatus() {
        // 检查本地存储的认证状态
        const token = localStorage.getItem('access_token');
        const userInfo = localStorage.getItem('user_info');
        
        if (token && userInfo) {
            try {
                this.userInfo = JSON.parse(userInfo);
                this.isLoggedIn = true;
                this.userName = this.userInfo.name;
            } catch (error) {
                console.error('Failed to parse user info:', error);
                this.clearAuthData();
            }
        } else {
            this.clearAuthData();
        }
    }

    clearAuthData() {
        this.isLoggedIn = false;
        this.userName = '';
        this.userInfo = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
    }

    showLoginModal() {
        if (!this.loginModal) {
            // 如果模态框未初始化，先初始化
            this.setupLoginModal();
            // 等待一小段时间让脚本加载完成
            setTimeout(() => {
                if (this.loginModal) {
                    const returnUrl = window.location.pathname + window.location.search;
                    this.loginModal.show(returnUrl);
                }
            }, 100);
        } else {
            // 传递当前页面URL作为返回地址
            const returnUrl = window.location.pathname + window.location.search;
            this.loginModal.show(returnUrl);
        }
    }

    async handleLoginSuccess(userData) {
        this.userInfo = userData;
        this.isLoggedIn = true;
        this.userName = userData.name;
        
        // 重新渲染组件
        this.render();
        this.addEventListeners();
    }

    async handleLogout() {
        try {
            // 调用登出API
            const token = localStorage.getItem('access_token');
            if (token) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // 清除本地数据
            this.clearAuthData();
            
            // 重新渲染组件
            this.render();
            this.addEventListeners();
            
            // 跳转到首页
            window.location.href = '/';
        }
    }

    // 默认图标方法，当图标库不可用时使用
    getDefaultSearchIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
        </svg>`;
    }

    getDefaultHomeIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9,22 9,12 15,12 15,22"></polyline>
        </svg>`;
    }

    getDefaultLogoutIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16,17 21,12 16,7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>`;
    }
}

customElements.define('header-component', HeaderComponent); 