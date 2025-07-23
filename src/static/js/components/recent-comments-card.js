class RecentCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.comments = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        this.loadData();
    }

    async loadData() {
        try {
            const response = await fetch('/api/comments/recent?limit=5');
            if (!response.ok) {
                throw new Error('Failed to fetch recent comments');
            }
            this.comments = await response.json();
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
     * 验证并生成导航URL
     * @param {Object} comment - 评论对象
     * @returns {string|null} 有效的URL或null
     */
    getNavigationUrl(comment) {
        // 验证projectitemid是否存在且有效
        if (!comment.projectitemid || comment.projectitemid === undefined || comment.projectitemid === null) {
            return null;
        }
        
        // 确保projectitemid是数字
        const projectitemid = parseInt(comment.projectitemid);
        if (isNaN(projectitemid) || projectitemid <= 0) {
            return null;
        }
        
        // 使用一致的URL模式：/projectitem/{id}
        return `/projectitem/${projectitemid}`;
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

                .comment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-2);
                }

                .author {
                    font-weight: 500;
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
                            ${this.comments.map(comment => {
                                const isClickable = this.getNavigationUrl(comment) !== null;
                                const cssClass = isClickable ? 'comment-item clickable' : 'comment-item disabled';
                                const clickHandler = isClickable ? `onclick="this.getRootNode().host.handleCommentClick(${JSON.stringify(comment)})"` : '';
                                
                                return `
                                    <div class="${cssClass}" ${clickHandler}>
                                        <div class="comment-content">
                                            <div class="comment-header">
                                                <span class="author">${comment.author}</span>
                                                <span class="time">${comment.time}</span>
                                            </div>
                                            <div class="comment-text">${this.truncateText(comment.content, 20)}</div>
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