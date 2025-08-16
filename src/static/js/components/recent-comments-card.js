class RecentCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.comments = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        this.loadData();
        this.setupEventListeners();
    }

    async loadData() {
        try {
            // 检测是否在博客页面
            const isBlogPage = this.isBlogPage();
            let apiUrl;
            
            if (isBlogPage) {
                // 在博客页面：获取当前博客的评论
                const projectId = this.getProjectIdFromUrl();
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
            this.comments = await response.json();
            
            // 格式化时间（如果是ISO格式）
            this.comments = this.comments.map(comment => ({
                ...comment,
                time: this.formatTime(comment.time)
            }));
        } catch (error) {
            this.logError('Error loading recent comments', error);
            // 使用默认数据作为后备
            this.comments = [
                { 
                    author: '张三', 
                    content: '这篇文章写得很好，对我很有帮助！', 
                    time: '2小时前'
                },
                { 
                    author: '李四', 
                    content: '感谢分享，学到了很多新知识。', 
                    time: '4小时前'
                },
                { 
                    author: '王五', 
                    content: '这个观点很独特，值得深入思考。', 
                    time: '6小时前'
                },
                { 
                    author: '赵六', 
                    content: '期待更多相关内容！', 
                    time: '1天前'
                }
            ];
        } finally {
            this.loading = false;
            this.render();
        }
    }

    /**
     * 检测是否在博客页面
     * @returns {boolean} 是否在博客页面
     */
    isBlogPage() {
        const path = window.location.pathname;
        return path.startsWith('/blog/');
    }

    /**
     * 从URL获取项目ID
     * @returns {number|null} 项目ID
     */
    getProjectIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/blog\/(\d+)/);
        return match ? parseInt(match[1]) : null;
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
     * 截断文本
     * @param {string} text - 原始文本
     * @param {number} maxLength - 最大长度
     * @returns {string} 截断后的文本
     */
    truncateText(text, maxLength) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
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
        
        // 使用新的URL模式：blogn/{projectid}#post{postid}
        return `/blogn/${projectitemid}#post${commentId}`;
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 使用事件委托来处理评论点击
        this.shadowRoot.addEventListener('click', (event) => {
            const commentItem = event.target.closest('.comment-item.clickable');
            if (commentItem) {
                const commentIndex = commentItem.getAttribute('data-comment-index');
                if (commentIndex !== null) {
                    const index = parseInt(commentIndex);
                    if (!isNaN(index) && index >= 0 && index < this.comments.length) {
                        this.handleCommentClick(this.comments[index]);
                    }
                }
            }
        });
    }

    /**
     * HTML转义方法
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 处理评论点击事件
     * @param {Object} comment - 评论对象
     */
    handleCommentClick(comment) {
        const url = this.getNavigationUrl(comment);
        if (url) {
            window.location.href = url;
        } else {
            // 如果URL无效，可以显示错误信息或记录日志
            console.warn('Invalid projectitemid for comment:', comment);
            // 可以选择显示一个提示或禁用点击
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    transition: var(--transition-normal);
                }

                .card:hover {
                    box-shadow: var(--shadow-md);
                    transform: translateY(-2px);
                }

                .card-header {
                    padding: var(--spacing-4) var(--spacing-5);
                    border-bottom: 1px solid var(--gray-200);
                    background: var(--gray-50);
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }

                .card-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                }

                .icon {
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .icon svg {
                    width: 20px;
                    height: 20px;
                    stroke: var(--primary-color);
                    stroke-width: 2;
                    fill: none;
                    stroke-linecap: round;
                    stroke-linejoin: round;
                }

                .card-body {
                    padding: var(--spacing-5);
                }

                .comment-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-3);
                }

                .comment-item {
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    transition: var(--transition-normal);
                    display: flex;
                    align-items: flex-start;
                    gap: var(--spacing-3);
                }

                .comment-item:hover {
                    background: var(--gray-100);
                    border-color: var(--gray-300);
                }

                .comment-item.clickable {
                    cursor: pointer;
                }

                .comment-item.disabled {
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
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 2px solid var(--gray-200);
                    overflow: hidden;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .comment-content {
                    flex: 1;
                    min-width: 0;
                }

                .comment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-2);
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
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .loading-spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--gray-200);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: var(--spacing-2);
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <div class="icon">
                        <svg viewBox="0 0 24 24">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                            <path d="M8 9h8"/>
                            <path d="M8 13h6"/>
                        </svg>
                    </div>
                    <h3 class="card-title">最近评论</h3>
                </div>
                <div class="card-body">
                    ${this.loading ? this.createLoadingHTML() : `
                        <div class="comment-list">
                            ${this.comments.map((comment, index) => {
                                const isClickable = this.getNavigationUrl(comment) !== null;
                                const cssClass = isClickable ? 'comment-item clickable' : 'comment-item disabled';
                                const dataAttributes = isClickable ? `data-comment-index="${index}"` : '';
                                
                                return `
                                    <div class="${cssClass}" ${dataAttributes}>
                                        <div class="user-avatar">
                                            ${comment.avatar && comment.avatar !== 'null' && comment.avatar !== null ? 
                                                `<img src="${comment.avatar}" alt="${this.escapeHtml(comment.author)}" />` : 
                                                `<span>${this.escapeHtml(comment.author.charAt(0))}</span>`
                                            }
                                        </div>
                                        <div class="comment-content">
                                            <div class="comment-header">
                                                <span class="author">${this.escapeHtml(comment.author)}</span>
                                                <span class="time">${this.escapeHtml(comment.time)}</span>
                                            </div>
                                            <div class="comment-text">${this.escapeHtml(this.truncateText(comment.content, 20))}</div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    `}
                </div>
            </div>
        `;
    }
}

customElements.define('recent-comments-card', RecentCommentsCard); 