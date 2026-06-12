class HeaderComponent extends BaseComponent {
    constructor() {
        super();
        this.siteName = '';
        this.logoUrl = '';
        this.isLoggedIn = false;
        this.userName = '';
        this.userInfo = null;
        this.loginModal = null;
        this.registrationLogin = false; // 注册登录标识
    }


    async connectedCallback() {
        await this.loadMetadata();
        await this.checkAuthStatus();
        this.render();
        this.setupLoginModal();
        this.addGlobalEventListeners();
        
        // 监听令牌相关事件
        this.setupTokenEventListeners();
        
        // 动态加载token-manager服务
        this.loadTokenManager();
    }

    render() {
        const siteName = this.metadata?.site_name || 'BlogN';
        const logoUrl = this.getLogoUrl();
        
        // 检查图标库是否可用
        const hasIcons = typeof Icons !== 'undefined';
        const searchIcon = hasIcons ? Icons.search : this.getDefaultSearchIcon();
        const userHomeIcon = hasIcons ? Icons.userHome : this.getDefaultUserHomeIcon();
        const blogIcon = hasIcons ? Icons.userHome : this.getDefaultHomeIcon();
        const settingsIcon = hasIcons && Icons.settings ? Icons.settings : this.getDefaultSettingsIcon();
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

                /* 规范下拉菜单项中的任意SVG图标尺寸，避免外部图标过大 */
                .dropdown-item svg {
                    width: 16px;
                    height: 16px;
                    flex-shrink: 0;
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
                    gap: var(--spacing-2);
                    padding: var(--spacing-2) var(--spacing-3);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    border-radius: var(--radius-md);
                    border: 1px solid var(--gray-300);
                    background-color: var(--white);
                    color: var(--gray-700);
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                    line-height: 1.25;
                }

                .btn:hover {
                    background-color: var(--gray-50);
                    border-color: var(--gray-400);
                    color: var(--gray-900);
                }

                .btn:focus { outline: none; }
                .btn:focus-visible {
                    outline: 2px solid var(--primary-color);
                    outline-offset: 2px;
                }

                .btn-primary {
                    background-color: var(--primary-color);
                    color: var(--white);
                    border-color: var(--primary-color);
                }

                .btn-primary:hover {
                    background-color: var(--primary-hover);
                    border-color: var(--primary-hover);
                    color: var(--white);
                }

                .btn-ghost {
                    background-color: transparent;
                    color: var(--gray-600);
                    border-color: transparent;
                }

                .btn-ghost:hover {
                    background-color: var(--gray-100);
                    color: var(--gray-800);
                    border-color: transparent;
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
                    <!-- 注册链接始终显示 -->
                    <a href="/user_register" class="btn btn-ghost">注册</a>
                    
                    ${this.isLoggedIn ? `
                        <div class="user-menu" id="userMenu">
                            <div class="user-avatar">
                                ${(() => {
                                    // 按照最新评论卡片的方式：同时渲染头像和用户名首字母
                                    const hasAvatar = this.userInfo && this.userInfo.avatar_url && this.userInfo.avatar_url !== 'null' && this.userInfo.avatar_url !== '';
                                    const firstChar = this.userName && this.userName.length > 0 ? this.userName.charAt(0).toUpperCase() : 'U';
                                    
                                    if (hasAvatar) {
                                        // 有头像URL，显示头像，失败时显示用户名首字母
                                        return `<img src="${this.escapeHtml(this.userInfo.avatar_url)}" alt="Avatar" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                        <div class="avatar-placeholder" style="display: none;">${this.escapeHtml(firstChar)}</div>`;
                                    } else {
                                        // 没有头像URL，直接显示用户名首字母
                                        return `<div class="avatar-placeholder">${this.escapeHtml(firstChar)}</div>`;
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
                                ${this.userInfo && this.userInfo.projectid ? `
                                <a href="/blog/${this.userInfo.projectid}" target="_blank" rel="noopener" class="dropdown-item" id="blogMenuItem">
                                    ${blogIcon}
                                    博客
                                </a>
                                ` : ''}
                                <a href="${this.userInfo && this.userInfo.id ? `/profile/${this.userInfo.id}` : '/profile'}" class="dropdown-item" id="profileMenuItem">
                                    ${userHomeIcon}
                                    个人资料
                                </a>
                                ${this.userInfo && this.userInfo.projectid ? `
                                <a href="/manage-friend-links?project_id=${this.userInfo.projectid}" target="_blank" rel="noopener" class="dropdown-item" id="manageFriendLinksMenuItem">
                                    ${settingsIcon}
                                    管理友情链接
                                </a>
                                ${this.userInfo && this.userInfo.state === 10 ? `
                                <a href="/manage-friend-links" target="_blank" rel="noopener" class="dropdown-item" id="manageGlobalFriendLinksMenuItem">
                                    ${settingsIcon}
                                    管理全站友情链接
                                </a>
                                ` : ''}
                                ` : ''}
                                ${this.isLoggedIn && this.userInfo && this.userInfo.state === 10 ? `
                                <a href="/users" class="dropdown-item" id="usersListMenuItem">
                                    ${hasIcons ? Icons.usersList : this.getDefaultUsersListIcon()}
                                    用户列表
                                </a>
                                ` : ''}
                                ${this.isLoggedIn ? `
                                <a href="/regkey" class="dropdown-item" id="registrationCodeMenuItem">
                                    ${hasIcons ? Icons.registrationCode : this.getDefaultRegistrationCodeIcon()}
                                    注册码管理
                                </a>
                                ` : ''}
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
                userMenu.classList.remove('active');
                // 打开搜索页面
                window.open('/search', '_blank');
            });
        }

        // 个人资料菜单项
        const profileMenuItem = this.shadowRoot.querySelector('#profileMenuItem');
        if (profileMenuItem) {
            profileMenuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                // 链接已经直接指向正确的URL，只需要关闭菜单
                userMenu.classList.remove('active');
            });
        }

        // 管理友情链接菜单项
        const manageFriendLinksMenuItem = this.shadowRoot.querySelector('#manageFriendLinksMenuItem');
        if (manageFriendLinksMenuItem) {
            manageFriendLinksMenuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                // 新窗口打开，关闭菜单
                userMenu.classList.remove('active');
            });
        }

        // 管理全站友情链接菜单项（仅管理员可见）
        const manageGlobalFriendLinksMenuItem = this.shadowRoot.querySelector('#manageGlobalFriendLinksMenuItem');
        if (manageGlobalFriendLinksMenuItem) {
            manageGlobalFriendLinksMenuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                // 新窗口打开，关闭菜单
                userMenu.classList.remove('active');
            });
        }

        // 博客菜单项
        const blogMenuItem = this.shadowRoot.querySelector('#blogMenuItem');
        if (blogMenuItem) {
            blogMenuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                // 新窗口打开，关闭菜单
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
            script.src = (window.BlognStatic && window.BlognStatic.url('/static/js/components/login-modal.js'))
                || '/static/js/components/login-modal.js';
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
        
        // 监听显示登录模态框事件
        document.addEventListener('showLoginModal', (e) => {
            const options = e.detail || {};
            this.showLoginModal(null, options);
        });
    }
    
    setupTokenEventListeners() {
        // 监听令牌刷新事件
        window.addEventListener('tokenRefreshed', (event) => {
            // 可以在这里更新UI状态
        });
        
        // 监听令牌清除事件
        window.addEventListener('tokensCleared', () => {
            this.clearAuthData();
            this.render();
        });
    }

    async checkAuthStatus() {
        // 使用令牌管理服务验证令牌有效性
        if (window.tokenManager) {
            const isValid = await window.tokenManager.validateToken();
            if (!isValid) {
                this.clearAuthData();
                return;
            }
        }
        
        // 检查本地存储的认证状态
        if (UserManager.isLoggedIn()) {
            try {
                this.userInfo = UserManager.getCurrentUser();
                this.isLoggedIn = true;
                // 清理用户名中的多余空格
                this.userName = (this.userInfo.name || 'User').trim();

                // 补充获取完整用户信息（包括是否开通博客的projectid）
                if (this.userInfo && this.userInfo.id) {
                    try {
                        const headers = UserManager.createHeaders();
                        const resp = await fetch(`/api/users/${this.userInfo.id}`, { headers });
                        if (resp && resp.ok) {
                            const fullUser = await resp.json();
                            // 合并关键字段（避免覆盖已有字段）
                            if (typeof fullUser.projectid !== 'undefined') {
                                this.userInfo.projectid = fullUser.projectid;
                            }
                            if (typeof fullUser.avatar_url !== 'undefined' && !this.userInfo.avatar_url) {
                                this.userInfo.avatar_url = fullUser.avatar_url;
                            }
                        } else {
                            console.warn('Failed to load full user info:', resp && resp.status);
                        }
                    } catch (e) {
                        console.warn('Error fetching full user info:', e);
                    }
                }
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
        this.registrationLogin = false; // 重置注册登录标识
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
    }

    showLoginModal(returnUrl = null, options = {}) {
        // 设置注册登录标识
        if (options.fromRegistration) {
            this.registrationLogin = true;
        }
        
        if (!this.loginModal) {
            // 如果模态框未初始化，先初始化
            this.setupLoginModal();
            // 等待一小段时间让脚本加载完成
            setTimeout(() => {
                if (this.loginModal) {
                    const finalReturnUrl = returnUrl || window.location.pathname + window.location.search;
                    this.loginModal.show(finalReturnUrl);
                }
            }, 100);
        } else {
            // 传递指定的返回地址或当前页面URL
            const finalReturnUrl = returnUrl || window.location.pathname + window.location.search;
            this.loginModal.show(finalReturnUrl);
        }
    }

    async handleLoginSuccess(userData) {
        this.userInfo = userData;
        this.isLoggedIn = true;
        // 清理用户名中的多余空格
        this.userName = (userData.name || 'User').trim();
        
        // 重新渲染组件
        this.render();
        this.addEventListeners();
        
        // 根据登录来源决定跳转行为
        if (this.registrationLogin) {
            // 注册后的登录，跳转到首页
            this.registrationLogin = false; // 重置标识
            window.location.href = '/';
        } else if (this.returnUrl) {
            // 普通登录，回到原页面
            const returnUrl = this.returnUrl;
            this.returnUrl = null; // 清除returnUrl
            window.location.href = returnUrl;
        }
        // 如果没有特殊标识，保持在当前页面
    }

    async handleLogout() {
        try {
            // 调用登出API
            const token = UserManager.getAccessToken();
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

    getDefaultUserHomeIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
            <circle cx="12" cy="7" r="4"/>
        </svg>`;
    }

    getDefaultLogoutIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16,17 21,12 16,7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>`;
    }

    getDefaultRegistrationCodeIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 0 1 21.75 8.25z"></path>
        </svg>`;
    }

    /**
     * 获取默认用户列表图标
     * @returns {string} SVG图标HTML
     */
    getDefaultUsersListIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        </svg>`;
    }

    getDefaultSettingsIcon() {
        return `<svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>`;
    }

    /**
     * 动态加载token-manager服务
     */
    loadTokenManager() {
        // 检查token-manager是否已经加载
        if (window.tokenManager) {
            return;
        }

        // 检查是否已经有token-manager脚本
        const existingScript = document.querySelector('script[src*="token-manager.js"]');
        if (existingScript) {
            return;
        }

        // 动态加载token-manager脚本
        const script = document.createElement('script');
        const tokenManagerJs = '/static/js/services/token-manager.js';
        script.src = (window.BlognStatic && window.BlognStatic.url(tokenManagerJs)) || tokenManagerJs;
        script.onerror = () => {
            console.error('Failed to load token-manager.js');
        };
        document.head.appendChild(script);
    }
}

customElements.define('header-component', HeaderComponent); 