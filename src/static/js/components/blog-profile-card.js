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
        
        // 如果在个人资料页面，等待targetUserIdReady事件
        if (window.location.pathname.startsWith('/profile')) {
            if (window.targetUserId) {
                // 如果已经有targetUserId，直接加载数据
                this.loadData();
            } else {
                // 等待targetUserIdReady事件
                window.addEventListener('targetUserIdReady', (event) => {
                    this.loadData();
                }, { once: true });
            }
        } else {
            // 不在个人资料页面，直接加载数据
            this.loadData();
        }
    }

    getProjectIdFromUrl() {
        // 使用基类的统一方法
        return this.getProjectId();
    }



    async loadData() {
        if (!this.projectId) {
            // 如果在个人资料页面，尝试获取目标用户的博客信息
            if (window.location.pathname.startsWith('/profile')) {
                try {
                    // 优先使用全局目标用户ID
                    let userId = window.targetUserId;
                    
                    if (!userId) {
                        // 如果没有目标用户ID，使用当前登录用户
                        if (UserManager.isLoggedIn()) {
                            const currentUser = UserManager.getCurrentUser();
                            userId = currentUser.id;
                        }
                    }
                    
                    if (userId) {
                        // 获取用户的博客信息
                        const headers = UserManager.createHeaders();
                        
                        // 获取用户信息
                        const userResponse = await fetch(`/api/users/${userId}`, { headers });
                        if (userResponse.ok) {
                            this.userData = await userResponse.json();
                            
                            // 检查用户是否有博客项目
                            if (this.userData.projectid) {
                                const projectData = await BaseComponent.getProject(this.userData.projectid);
                                if (projectData) {
                                    this.projectData = projectData;
                                    this.projectId = projectData.id;
                                }
                            } else {
                                // 用户没有博客
                                this.projectData = null;
                            }
                            this.loading = false;
                            this.render();
                            return;
                        } else {
                            this.showError(`获取用户信息失败: ${userResponse.status}`);
                            return;
                        }
                    } else {
                        this.showError('无法获取用户ID');
                        return;
                    }
                } catch (error) {
                    console.error('Error loading user blog data:', error);
                    this.showError('加载用户博客数据失败');
                    return;
                }
            }
            
            // 如果在文章页面，尝试从文章ID获取项目ID
            if (this.isArticlePage()) {
                const articleId = this.getArticleId();
                if (articleId) {
                    try {
                        const articleData = await BaseComponent.getArticle(articleId);
                        if (articleData?.project?.id) {
                            this.projectId = articleData.project.id;
                        } else {
                            this.showError('无法获取博客ID');
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
            const projectData = await BaseComponent.getProject(this.projectId);
            if (projectData === null) {
                window.location.href = '/static/error.html';
                return;
            }
            this.projectData = projectData;
            if (projectData.userid) {
                const userResponse = await fetch(`/api/users/${projectData.userid}`);
                if (userResponse.ok) {
                    this.userData = await userResponse.json();
                }
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


    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');

                :host {
                    display: block;
                }

                .blog-profile-link {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }

                .blog-profile-link:focus {
                    outline: none;
                }

                .profile-main {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3) var(--spacing-4);
                }

                .user-avatar {
                    width: 56px;
                    height: 56px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .profile-text {
                    min-width: 0;
                    flex: 1;
                }

                .blog-name {
                    margin: 0;
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-900);
                    line-height: 1.3;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .user-name {
                    margin: var(--spacing-1) 0 0;
                    font-size: var(--font-size-sm);
                    font-weight: 400;
                    color: var(--gray-500);
                    line-height: 1.3;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .profile-stats {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-4);
                    padding: var(--spacing-2) var(--spacing-4) var(--spacing-3);
                    border-top: 1px solid var(--gray-100);
                    font-size: var(--font-size-xs);
                    color: var(--gray-600);
                }

                .profile-stat strong {
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-right: var(--spacing-1);
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-4);
                    color: var(--gray-500);
                    font-size: var(--font-size-sm);
                }

                .error {
                    text-align: center;
                    padding: var(--spacing-4);
                    color: var(--error-color);
                    font-size: var(--font-size-sm);
                }
            </style>

            <div class="card">
                ${this.loading ? this.renderLoading() : 
                  (this.projectData || this.userData) ? this.renderContent() : 
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
        // 安全处理所有文本字段，防止HTML注入和XSS攻击；允许仅有 projectData 无 userData 时仍显示
        const safeAvatarText = (this.userData && this.userData.name) ? this.escapeHtml(this.userData.name.charAt(0).toUpperCase()) : '?';
        const safeBlogName = this.projectData ? this.escapeHtml(this.projectData.name || '未命名博客') : '暂无博客';
        const safeUserName = (this.userData && this.userData.name) ? this.escapeHtml(this.userData.name) : '未知用户';

        // 构建头像路径 - 用户资料卡片使用大头像格式
        let avatarPath = null;
        if (this.userData && this.userData.id) {
            const prefix = Math.floor(this.userData.id / 10000) + 1;
            // 用户资料卡片使用大头像：/avatar/prefix/userid.jpg
            avatarPath = `/avatar/${prefix}/${this.userData.id}.jpg`;
        }

        const blogLink = this.projectId ? `/blog/${this.projectId}` : '#';
        const postCount = this.projectData ? (this.projectData.recordcount || 0) : 0;
        const commentCount = this.projectData ? (this.projectData.commentcount || 0) : 0;
        
        return `
            <a href="${blogLink}" class="blog-profile-link" title="查看博客主页" target="_blank" rel="noopener noreferrer">
                <div class="profile-main">
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
                    <div class="profile-text">
                        <h2 class="blog-name">${safeBlogName}</h2>
                        <p class="user-name">${safeUserName}</p>
                    </div>
                </div>
                <div class="profile-stats">
                    <span class="profile-stat"><strong>${postCount}</strong>文章</span>
                    <span class="profile-stat"><strong>${commentCount}</strong>评论</span>
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
