class MessagesListCard extends BaseComponent {
    constructor() {
        super();
        this.messages = [];
        this.loading = true;
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPages = 0;
        this.total = 0;
    }


    connectedCallback() {
        this.currentPage = this.getCurrentPageFromUrl();
        this.render();
        this.loadMessages();
        this.setupPaginationListener();
    }

    setupPaginationListener() {
        // 分页事件通过setPagination回调函数处理，无需额外监听
        // 移除了重复的document.addEventListener('page-change', ...)
    }

    async loadMessages() {
        this.loading = true;
        this.updateLoadingState();
        
        try {
            const response = await fetch(`/api/messages?page=${this.currentPage}&limit=${this.pageSize}`);
            if (!response.ok) {
                throw new Error('Failed to fetch messages');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading messages', error);
            this.showError();
        }
    }

    // 公共方法：刷新到第一页
    refreshToFirstPage() {
        this.currentPage = 1;
        this.loadMessages();
    }

    updateContent(data) {
        this.messages = data.messages || [];
        this.total = data.total || 0;
        this.totalPages = data.total_pages || 0;
        this.currentPage = data.current_page || 1;
        
        this.renderMessagesList();
        this.updatePagination();
    }

    renderMessagesList() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            if (this.messages.length === 0) {
                cardBody.innerHTML = `
                    <div class="messages-list">
                        <div class="message-item">
                            <div class="message-subject">暂无留言</div>
                        </div>
                    </div>
                `;
                return;
            }
            
            // 检查用户是否为管理员
            const isAdmin = UserManager.isAdmin();
            
            const messagesHtml = this.messages.map(message => {
                // 安全处理所有文本字段，防止HTML注入和XSS攻击
                const safeAuthor = this.escapeHtml(message.author);
                const safeSubject = this.escapeHtml(message.subject);
                const safeLastReplyAuthor = message.last_reply_author ? this.escapeHtml(message.last_reply_author) : '';
                const safePostTime = this.escapeHtml(message.post_time);
                const safeLastReplyTime = message.last_reply_time ? this.escapeHtml(message.last_reply_time) : '';
                
                // 格式化字节数
                const size = message.size || 0;
                const sizeText = size > 1024 ? `${(size / 1024).toFixed(1)}KB` : `${size}B`;
                
                // 格式化阅读数和回复数
                const hits = message.hits || 0;
                const replyCount = message.reply_count || 0;
                const readReplyText = `${hits}/${replyCount}`;
                
                // 生成删除按钮（仅管理员可见）
                const deleteButton = isAdmin ? `
                    <button class="delete-button" data-message-id="${message.id}" data-is-main="true">
                        <svg class="delete-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3,6 5,6 21,6"></polyline>
                            <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                        删除
                    </button>
                ` : '';
                
                return `
                    <div class="message-item" data-message-id="${message.id}" style="cursor: pointer;">
                        <div class="message-header">
                            <div class="message-title">${safeSubject}</div>
                            <div class="message-meta">
                                <span class="message-author">${safeAuthor}</span>
                                <span class="message-time">${safePostTime}</span>
                                ${deleteButton}
                            </div>
                        </div>
                        <div class="message-stats">
                            <div class="stat-item">
                                <span class="stat-label">字节:</span>
                                <span class="stat-value">${sizeText}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">阅读/回复:</span>
                                <span class="stat-value">${readReplyText}</span>
                            </div>
                            ${safeLastReplyAuthor ? `
                                <div class="stat-item">
                                    <span class="stat-label">最后回复:</span>
                                    <span class="stat-value">${safeLastReplyAuthor} ${safeLastReplyTime}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
            cardBody.innerHTML = `
                <div class="messages-list">
                    ${messagesHtml}
                </div>
            `;
            
            // 添加点击事件监听器
            this.attachClickListeners();
            
            // 添加删除按钮事件监听器
            if (isAdmin) {
                this.attachDeleteListeners();
            }
        }
    }

    attachClickListeners() {
        const messageItems = this.shadowRoot.querySelectorAll('.message-item[data-message-id]');
        messageItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // 如果点击的是删除按钮，不触发跳转
                if (e.target.closest('.delete-button')) {
                    return;
                }
                const messageId = item.getAttribute('data-message-id');
                if (messageId) {
                    window.open(`/thread/${messageId}`, '_blank');
                }
            });
        });
    }

    /**
     * 添加删除按钮事件监听器
     */
    attachDeleteListeners() {
        const deleteButtons = this.shadowRoot.querySelectorAll('.delete-button');
        deleteButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation(); // 防止事件冒泡
                const messageId = button.getAttribute('data-message-id');
                const isMainPost = button.getAttribute('data-is-main') === 'true';
                await this.showDeleteConfirmation(messageId, isMainPost);
            });
        });
    }

    /**
     * 显示删除确认对话框
     */
    async showDeleteConfirmation(messageId, isMainPost) {
        const confirmMessage = isMainPost
            ? `确定要删除这个主贴吗？\n\n删除主贴将同时删除所有相关的跟贴，此操作不可撤销！`
            : `确定要删除这条跟贴吗？\n\n此操作不可撤销！`;

        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: isMainPost ? '删除主贴' : '删除跟贴',
            message: confirmMessage,
            danger: true,
        })) {
            return;
        }
        this.deleteMessage(messageId);
    }

    /**
     * 删除留言
     */
    async deleteMessage(messageId) {
        try {
            const token = UserManager.getAccessToken();
            if (!token) {
                alert('请先登录');
                return;
            }

            const response = await fetch(`/api/messages/${messageId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // 删除成功
                alert(result.message);
                
                // 刷新留言列表
                this.loadMessages();
            } else {
                // 删除失败
                alert(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除留言失败:', error);
            alert('删除失败，请稍后重试');
        }
    }

    updatePagination() {
        const paginationCard = document.querySelector('navigation-card[mode="pagination"]');
        if (paginationCard) {
            const pagination = {
                current_page: this.currentPage,
                total_pages: this.totalPages,
                total: this.total,
                total_count: this.total,
                has_prev: this.currentPage > 1,
                has_next: this.currentPage < this.totalPages,
                item_type: '条留言'
            };
            
            paginationCard.setPagination(pagination, (page) => {
                this.currentPage = page;
                this.loadMessages();
            });
        }
    }

    updateLoadingState() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = `
                <div class="messages-list">
                    <div class="message-item">
                        <div class="message-subject">正在加载留言...</div>
                    </div>
                </div>
            `;
        }
    }

    showError() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML('加载失败，请稍后重试');
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
                }

                .card-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                }

                .card-body {
                    padding: var(--spacing-5);
                }

                .messages-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }

                .message-item {
                    padding: var(--spacing-4);
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    transition: var(--transition-fast);
                }

                .message-item:hover {
                    background: var(--gray-100);
                    border-color: var(--gray-300);
                }

                .message-header {
                    margin-bottom: var(--spacing-3);
                }

                .message-title {
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-2);
                    line-height: 1.4;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }

                .message-meta {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    flex-wrap: wrap;
                }

                .message-author {
                    font-weight: 500;
                    color: var(--primary-color);
                    font-size: var(--font-size-sm);
                }

                .message-time {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                .delete-button {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    padding: var(--spacing-1) var(--spacing-2);
                    background: var(--red-50);
                    color: var(--red-600);
                    border: 1px solid var(--red-200);
                    border-radius: var(--radius-sm);
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    cursor: pointer;
                    transition: var(--transition-fast);
                    margin-left: auto;
                }

                .delete-button:hover {
                    background: var(--red-100);
                    border-color: var(--red-300);
                    color: var(--red-700);
                }

                .delete-button:active {
                    background: var(--red-200);
                    transform: translateY(1px);
                }

                .delete-icon {
                    width: 14px;
                    height: 14px;
                }

                .message-stats {
                    display: flex;
                    flex-wrap: wrap;
                    gap: var(--spacing-4);
                    padding-top: var(--spacing-2);
                    border-top: 1px solid var(--gray-200);
                }

                .stat-item {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    font-size: var(--font-size-sm);
                }

                .stat-label {
                    color: var(--gray-600);
                    font-weight: 500;
                }

                .stat-value {
                    color: var(--gray-900);
                    font-weight: 600;
                }

                /* 响应式设计 */
                @media (max-width: 768px) {
                    .message-meta {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: var(--spacing-1);
                    }
                    
                    .message-stats {
                        flex-direction: column;
                        gap: var(--spacing-2);
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">留言本</h3>
                </div>
                <div class="card-body">
                    <div class="messages-list">
                        <div class="message-item">
                            <div class="message-subject">正在加载留言...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('messages-list-card', MessagesListCard);
