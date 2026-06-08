class RecentCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.comments = [];
        this.loading = true;
        this.error = false;
        this.errorMessage = '';
    }

    connectedCallback() {
        this.render();
        this.loadData();
    }

    async loadData() {
        try {
            // 检测当前页面类型
            const isBlogRelatedPage = this.isBlogRelatedPage();
            
            let apiUrl;
            
            if (isBlogRelatedPage) {
                // 在博客页面或博客文章页面：获取当前博客的评论
                const projectId = await this.getProjectIdFromCurrentPage();
                
                if (projectId) {
                    apiUrl = `/api/projects/${projectId}/comments/recent?limit=5`;
                } else {
                    // 如果无法获取projectId，回退到全站评论
                    apiUrl = '/api/comments/recent?limit=5';
                }
            } else {
                // 在首页：获取全站评论
                apiUrl = '/api/comments/recent?limit=5';
            }
            
            const response = await fetch(apiUrl);
            if (response.ok) {
                this.comments = await response.json();
            } else if (response.status === 404) {
                // 如果博客不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                throw new Error('Failed to fetch recent comments');
            }
            
            // 格式化时间（如果是ISO格式）
            this.comments = this.comments.map(comment => ({
                ...comment,
                time: this.formatTime(comment.time)
            }));
        } catch (error) {
            this.logError('Error loading recent comments', error);
            // 设置错误状态，不显示假数据
            this.error = true;
            this.errorMessage = '加载评论失败，请稍后重试';
        } finally {
            this.loading = false;
            this.render();
        }
    }

    /**
     * 检测是否在博客相关页面（博客页面或博客文章页面）
     * @returns {boolean} 是否在博客相关页面
     */
    isBlogRelatedPage() {
        const path = window.location.pathname;
        return path.startsWith('/blog/') || path.startsWith('/article/');
    }

    /**
     * 从当前页面获取项目ID
     * @returns {Promise<number|null>} 项目ID
     */
    async getProjectIdFromCurrentPage() {
        const path = window.location.pathname;
        
        if (path.startsWith('/blog/')) {
            // 博客页面：直接从URL获取项目ID
            return this.getProjectId();
        } else if (path.startsWith('/article/')) {
            // 博客文章页面：需要从文章数据获取项目ID
            return await this.getProjectIdFromArticlePage();
        }
        
        return null;
    }

    /**
     * 从博客文章页面获取项目ID
     * @returns {Promise<number|null>} 项目ID
     */
    async getProjectIdFromArticlePage() {
        // 从基类方法获取文章ID
        const articleId = this.getArticleId();
        
        if (!articleId) return null;
        
        try {
            const articleData = await BaseComponent.getArticle(articleId);
            if (articleData) return articleData.project?.id;
        } catch (error) {
            console.warn('Failed to fetch article data for project ID:', error);
        }
        
        // 如果API调用失败，尝试从页面组件获取（可能不可靠，但作为后备方案）
        const articleHeaderCard = document.querySelector('article-header-card');
        if (articleHeaderCard && articleHeaderCard.articleData) {
            return articleHeaderCard.articleData.projectid;
        }
        
        const articleContentCard = document.querySelector('article-content-card');
        if (articleContentCard && articleContentCard.articleData) {
            return articleContentCard.articleData.projectid;
        }
        
        return null;
    }

    /**
     * 格式化时间
     * @param {string|Date} time - 时间
     * @returns {string} 格式化后的时间
     */
    formatTime(time) {
        if (!time) {
            return '未知时间';
        }
        
        // 如果已经是相对时间格式，直接返回
        if (typeof time === 'string' && (time.includes('前') || time.includes('小时') || time.includes('分钟'))) {
            return time;
        }
        
        try {
            const dateObj = new Date(time);
            const now = new Date();
            const diff = now - dateObj;
            
            // 转换为秒
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            if (seconds < 60) {
                return '刚刚';
            } else if (minutes < 60) {
                return `${minutes}分钟前`;
            } else if (hours < 24) {
                return `${hours}小时前`;
            } else if (days < 7) {
                return `${days}天前`;
            } else {
                return dateObj.toLocaleDateString('zh-CN');
            }
        } catch (error) {
            return '未知时间';
        }
    }

    /**
     * 创建加载状态HTML
     * @returns {string} 加载状态HTML
     */
    createLoadingHTML() {
        return `
            <div class="loading">
                <div class="loading-spinner"></div>
                <div>加载中...</div>
            </div>
        `;
    }

    /**
     * 验证并生成导航URL
     * @param {Object} comment - 评论对象
     * @returns {string|null} 有效的URL或null
     * 
     * 生成的URL格式：/article/{articleId}#post{commentId}
     * 这样可以直接跳转到文章页面并定位到对应评论
     */
    getNavigationUrl(comment) {
        // 验证projectitemid和comment id是否存在且有效
        if (!comment.projectitemid || comment.projectitemid === undefined || comment.projectitemid === null) {
            return null;
        }
        
        if (!comment.id || comment.id === undefined || comment.id === null) {
            return null;
        }
        
        // 确保projectitemid和comment id是数字
        const projectitemid = parseInt(comment.projectitemid);
        const commentId = parseInt(comment.id);
        if (isNaN(projectitemid) || projectitemid <= 0 || isNaN(commentId) || commentId <= 0) {
            return null;
        }
        
        // 使用正确的URL模式：article/{articleid}#post{commentid}
        return `/article/${projectitemid}#post${commentId}`;
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');

                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .comment-list {
                    list-style: none;
                    margin: 0;
                    padding: 0;
                }

                .comment-item {
                    border-bottom: 1px solid var(--gray-100);
                }

                .comment-item:last-child {
                    border-bottom: none;
                }

                .comment-link {
                    text-decoration: none;
                    color: inherit;
                    display: flex;
                    align-items: flex-start;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3) var(--spacing-4);
                    transition: var(--transition-fast);
                }

                .comment-item:hover {
                    background: var(--gray-50);
                }

                .comment-link:hover {
                    text-decoration: none;
                }

                .comment-item.disabled {
                    display: flex;
                    align-items: flex-start;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3) var(--spacing-4);
                    cursor: default;
                    opacity: 0.7;
                }

                .user-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 2px solid var(--gray-200);
                    overflow: hidden;
                    position: relative;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    position: absolute;
                    top: 0;
                    left: 0;
                }

                .user-avatar span {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--primary-color);
                    color: white;
                    font-weight: 600;
                    text-transform: uppercase;
                }

                .comment-content {
                    flex: 1;
                    min-width: 0;
                }

                .comment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-1);
                }

                .author {
                    font-weight: 700;
                    color: var(--gray-900);
                    font-size: var(--font-size-sm);
                }

                .time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }

                .comment-text {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.5;
                    margin: 0;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .error {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-3) var(--spacing-4);
                    color: var(--error-color);
                    background: var(--gray-50);
                    border-radius: var(--radius-lg);
                }

                .error-icon {
                    margin-right: var(--spacing-2);
                    font-size: 1.2em;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${Icons.comments}
                        最近评论
                    </h3>
                </div>
                ${this.loading ? `<div class="loading">${this.createLoadingHTML()}</div>` :
                  this.error ? this.createErrorHTML() : `
                    <ul class="comment-list">
                        ${this.comments.map((comment) => {
                            const commentUrl = this.getNavigationUrl(comment);
                            const avatarHtml = `
                                <div class="user-avatar">
                                    ${comment.avatar && comment.avatar !== 'null' && comment.avatar !== null && comment.avatar !== '' ?
                                        `<img src="${comment.avatar}" alt="${this.escapeHtml(comment.author)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />` :
                                        ''
                                    }
                                    <span style="${comment.avatar && comment.avatar !== 'null' && comment.avatar !== null && comment.avatar !== '' ? 'display: none;' : 'display: flex;'}">${this.escapeHtml(comment.author.charAt(0))}</span>
                                </div>
                            `;
                            const contentHtml = `
                                <div class="comment-content">
                                    <div class="comment-header">
                                        <span class="author">${this.escapeHtml(comment.author)}</span>
                                        <span class="time">${this.escapeHtml(comment.time)}</span>
                                    </div>
                                    <div class="comment-text">${this.escapeHtml(this.truncateText(comment.content, 20))}</div>
                                </div>
                            `;

                            if (commentUrl) {
                                return `
                                    <li class="comment-item">
                                        <a href="${commentUrl}" class="comment-link" target="_blank" title="查看评论">
                                            ${avatarHtml}
                                            ${contentHtml}
                                        </a>
                                    </li>
                                `;
                            }

                            return `
                                <li class="comment-item disabled">
                                    ${avatarHtml}
                                    ${contentHtml}
                                </li>
                            `;
                        }).join('')}
                    </ul>
                `}
            </div>
        `;
    }

    createErrorHTML() {
        return `
            <div class="error">
                ${Icons.warning}
                <span>${this.errorMessage}</span>
            </div>
        `;
    }
}

customElements.define('recent-comments-card', RecentCommentsCard); 