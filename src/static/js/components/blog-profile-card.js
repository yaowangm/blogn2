/**
 * 博客用户资料卡片组件
 * 显示博客用户的头像、名称和基本信息
 */
class BlogProfileCard extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.userData = null;
        this.projectData = null;
        this.loading = true;
    }

    connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        this.loadData();
    }

    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    async loadData() {
        if (!this.projectId) {
            this.showError('无法获取博客ID');
            return;
        }

        try {
            // 获取项目信息
            const projectResponse = await fetch(`/api/projects/${this.projectId}`);
            if (projectResponse.ok) {
                this.projectData = await projectResponse.json();
                
                // 获取用户信息
                if (this.projectData.userid) {
                    const userResponse = await fetch(`/api/users/${this.projectData.userid}`);
                    if (userResponse.ok) {
                        this.userData = await userResponse.json();
                    }
                }
            }
        } catch (error) {
            console.error('Error loading blog profile data:', error);
            this.showError('加载博客信息失败');
        } finally {
            this.loading = false;
            this.render();
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-xl);
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    margin-bottom: var(--spacing-6);
                }

                .card-header {
                    padding: var(--spacing-6);
                    background: var(--gray-50);
                    color: var(--gray-800);
                    text-align: center;
                    border-bottom: 1px solid var(--gray-200);
                }

                .user-avatar {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    margin: 0 auto var(--spacing-4);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-3xl);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 3px solid var(--gray-200);
                    box-shadow: var(--shadow-lg);
                    overflow: hidden;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .blog-name {
                    margin: 0;
                    font-size: var(--font-size-xl);
                    font-weight: 600;
                    color: var(--gray-800);
                }



                .card-body {
                    padding: var(--spacing-6);
                }

                .user-info {
                    text-align: center;
                    margin-bottom: var(--spacing-4);
                }

                .user-name {
                    font-size: var(--font-size-lg);
                    font-weight: 500;
                    color: var(--gray-800);
                    margin: 0 0 var(--spacing-2) 0;
                }

                .user-email {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                    margin: 0;
                }

                .blog-stats {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: var(--spacing-4);
                    margin-top: var(--spacing-4);
                }

                .stat-item {
                    text-align: center;
                    padding: var(--spacing-3);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }

                .stat-number {
                    font-size: var(--font-size-xl);
                    font-weight: 600;
                    color: var(--primary-color);
                    margin: 0;
                }

                .stat-label {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    margin: var(--spacing-1) 0 0 0;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .error {
                    text-align: center;
                    padding: var(--spacing-6);
                    color: var(--error-color);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }
            </style>

            <div class="card">
                ${this.loading ? this.renderLoading() : 
                  this.userData && this.projectData ? this.renderContent() : 
                  this.renderError()}
            </div>
        `;
    }

    renderLoading() {
        return `
            <div class="loading">
                <div>加载中...</div>
            </div>
        `;
    }

    renderContent() {
        const avatarText = this.userData.name ? this.userData.name.charAt(0).toUpperCase() : '?';
        const blogName = this.projectData.name || '未命名博客';
        const userName = this.userData.name || '未知用户';
        const userEmail = this.userData.email || '';
        
        // 构建头像路径
        let avatarPath = null;
        if (this.userData.id) {
            const prefix = Math.floor(this.userData.id / 10000) + 1;
            avatarPath = `/avatars/${prefix}/s_${this.userData.id}.jpg`;
        }

        return `
            <div class="card-header">
                <div class="user-avatar">
                    ${avatarPath ? 
                        `<img src="${avatarPath}" alt="${userName}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">` : 
                        ''
                    }
                    <span style="display: ${avatarPath ? 'none' : 'flex'}">${avatarText}</span>
                </div>
                <h2 class="blog-name">${blogName}</h2>
            </div>
            <div class="card-body">
                <div class="user-info">
                    <h3 class="user-name">${userName}</h3>
                    <p class="user-email">${userEmail}</p>
                </div>
                <div class="blog-stats">
                    <div class="stat-item">
                        <div class="stat-number">${this.projectData.recordcount || 0}</div>
                        <div class="stat-label">文章</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${this.projectData.commentcount || 0}</div>
                        <div class="stat-label">评论</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderError() {
        return `
            <div class="error">
                <div>加载失败</div>
            </div>
        `;
    }

    showError(message) {
        console.error(message);
        this.loading = false;
        this.render();
    }
}

customElements.define('blog-profile-card', BlogProfileCard);
