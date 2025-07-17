class HeaderComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.metadata = null;
    }

    async connectedCallback() {
        await this.loadMetadata();
        this.render();
    }

    async loadMetadata() {
        try {
            const response = await fetch('/api/metadata');
            if (response.ok) {
                this.metadata = await response.json();
            } else {
                console.error('Failed to load metadata:', response.status);
                this.metadata = {
                    site_name: 'BlogN',
                    logo_url: '/static/images/logo.svg'
                };
            }
        } catch (error) {
            console.error('Error loading metadata:', error);
            this.metadata = {
                site_name: 'BlogN',
                logo_url: '/static/images/logo.svg'
            };
        }
    }

    render() {
        // 模拟用户登录状态（实际应用中应该从后端获取）
        const isLoggedIn = false;
        const userName = '张三';
        
        const siteName = this.metadata?.site_name || 'BlogN';
        const logoUrl = this.metadata?.logo_url || '/static/images/logo.svg';

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
                    width: 32px;
                    height: 32px;
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
                        <img src="${logoUrl}" alt="${siteName} Logo">
                    </div>
                    <span class="logo-text">${siteName}</span>
                </a>

                <div class="header-actions">
                    ${isLoggedIn ? `
                        <div class="user-menu">
                            <div class="user-avatar">${userName.charAt(0)}</div>
                            <span>${userName}</span>
                        </div>
                        <a href="/user" class="btn btn-ghost">我的首页</a>
                        <button class="search-button" title="搜索">
                            🔍
                        </button>
                        <a href="/logout" class="btn btn-ghost">退出</a>
                    ` : `
                        <button class="search-button" title="搜索">
                            🔍
                        </button>
                        <a href="/login" class="btn btn-primary">登录</a>
                    `}
                </div>
            </div>
        `;

        // 添加事件监听器
        this.addEventListeners();
    }

    addEventListeners() {
        const searchButton = this.shadowRoot.querySelector('.search-button');
        if (searchButton) {
            searchButton.addEventListener('click', () => {
                // 这里可以添加搜索功能
                console.log('搜索按钮被点击');
            });
        }
    }
}

customElements.define('header-component', HeaderComponent); 