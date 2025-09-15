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

    connectedCallback() {
        this.render();
        this.loadMessages();
        this.setupPaginationListener();
    }

    setupPaginationListener() {
        // 监听分页导航组件的页面变化事件
        document.addEventListener('page-change', (event) => {
            if (event.detail && event.detail.page) {
                this.currentPage = event.detail.page;
                this.loadMessages();
            }
        });
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
                
                return `
                    <div class="message-item" data-message-id="${message.id}" style="cursor: pointer;">
                        <div class="message-header">
                            <div class="message-title">${safeSubject}</div>
                            <div class="message-meta">
                                <span class="message-author">${safeAuthor}</span>
                                <span class="message-time">${safePostTime}</span>
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
        }
    }

    attachClickListeners() {
        const messageItems = this.shadowRoot.querySelectorAll('.message-item[data-message-id]');
        messageItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const messageId = item.getAttribute('data-message-id');
                if (messageId) {
                    window.open(`/thread/${messageId}`, '_blank');
                }
            });
        });
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
