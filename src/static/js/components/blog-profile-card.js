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
        // 使用基类的统一方法
        return this.getProjectId();
    }



    async loadData() {
        if (!this.projectId) {
            // 如果在个人资料页面，尝试获取当前用户的博客信息
            if (window.location.pathname === '/profile') {
                try {
                    const userInfo = localStorage.getItem('user_info');
                    if (userInfo) {
                        const currentUser = JSON.parse(userInfo);
                        const userId = currentUser.id;
                        
                        // 获取用户的博客信息
                        const projectResponse = await fetch(`/api/projects/user/${userId}`);
                        if (projectResponse.ok) {
                            this.projectData = await projectResponse.json();
                            this.projectId = this.projectData.id;
                            
                            // 获取用户信息
                            const userResponse = await fetch(`/api/users/${userId}`);
                            if (userResponse.ok) {
                                this.userData = await userResponse.json();
                            }
                            
                            this.loading = false;
                            this.render();
                            return;
                        }
                    }
                } catch (error) {
                    console.error('Error loading user blog data:', error);
                }
            }
            
            // 如果在文章页面，尝试从文章ID获取项目ID
            if (this.isArticlePage()) {
                const articleId = this.getArticleId();
                if (articleId) {
                    try {
                        const articleResponse = await fetch(`/api/articles/${articleId}`);
                        if (articleResponse.ok) {
                            const articleData = await articleResponse.json();
                            if (articleData.project?.id) {
                                this.projectId = articleData.project.id;
                            } else {
                                this.showError('无法获取博客ID');
                                return;
                            }
                        } else {
                            this.showError('无法获取文章信息');
                            return;
                        }
                    } catch (error) {
                        console.error('Error loading article data:', error);
                        this.showError('加载文章信息失败');
                        return;
                    }
                } else {
                    this.showError('无法获取文章ID');
                    return;
                }
            } else {
                this.showError('无法获取博客ID');
                return;
            }
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
            } else if (projectResponse.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            }
        } catch (error) {
            console.error('Error loading blog profile data:', error);
            // 加载失败，跳转到错误页面
            window.location.href = '/static/error.html';
            return;
        } finally {
            this.loading = false;
            this.render();
        }
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
                    transition: all 0.2s ease;
                }

                .card:hover {
                    transform: translateY(-2px);
                    box-shadow: var(--shadow-lg);
                    border-color: var(--primary-color);
                }

                .card-header {
                    padding: var(--spacing-6);
                    background: var(--gray-50);
                    color: var(--gray-800);
                    text-align: center;
                    border-bottom: 1px solid var(--gray-200);
                }

                .user-avatar {
                    width: 100px;
                    height: 100px;
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



                .blog-profile-link {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                    cursor: pointer;
                }

                .blog-profile-link:hover {
                    text-decoration: none;
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
        // 安全处理所有文本字段，防止HTML注入和XSS攻击
        const safeAvatarText = this.userData.name ? this.escapeHtml(this.userData.name.charAt(0).toUpperCase()) : '?';
        const safeBlogName = this.escapeHtml(this.projectData.name || '未命名博客');
        const safeUserName = this.escapeHtml(this.userData.name || '未知用户');
        
        // 构建头像路径 - 用户资料卡片使用大头像格式
        let avatarPath = null;
        if (this.userData.id) {
            const prefix = Math.floor(this.userData.id / 10000) + 1;
            // 用户资料卡片使用大头像：/avatar/prefix/userid.jpg
            avatarPath = `/avatar/${prefix}/${this.userData.id}.jpg`;
        }

        const blogLink = this.projectId ? `/blog/${this.projectId}` : '#';
        
        return `
            <a href="${blogLink}" class="blog-profile-link" title="查看博客主页" target="_blank" rel="noopener noreferrer">
                <div class="card-header">
                    <div class="user-avatar">
                        ${avatarPath ? 
                            `<img src="${avatarPath}" alt="${safeUserName}" 
                                  onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                                  onload="this.style.display='block'; this.nextElementSibling.style.display='none';"
                                  style="display: block;">` : 
                            ''
                        }
                        <span style="display: ${avatarPath ? 'none' : 'flex'}; color: var(--gray-600);">${safeAvatarText}</span>
                    </div>
                    <h2 class="blog-name">${safeBlogName}</h2>
                </div>
                <div class="card-body">
                    <div class="user-info">
                        <h3 class="user-name">${safeUserName}</h3>
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
            </a>
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