class RecentMessagesCard extends BaseComponent {
    constructor() {
        super();
        this.messages = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        this.loadContent();
    }

    async loadContent() {
        try {
            const response = await fetch('/api/blogs/messages/recent');
            if (!response.ok) {
                throw new Error('Failed to fetch recent messages');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading recent messages', error);
            this.showError();
        }
    }

    updateContent(messages) {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            if (messages.length === 0) {
                cardBody.innerHTML = `
                    <div class="message-list">
                        <div class="message-item">
                            <div class="message-subject">暂无留言</div>
                        </div>
                    </div>
                `;
                return;
            }
            
            const messagesHtml = messages.map(message => {
                // 安全处理所有文本字段，防止HTML注入和XSS攻击
                const safeAuthor = this.escapeHtml(message.author);
                const safeSubject = this.escapeHtml(message.subject);
                const safeReplyInfo = message.reply_info ? this.escapeHtml(message.reply_info) : '';
                const safeTime = this.escapeHtml(message.time);
                
                // 检查是否有有效的留言ID
                const messageId = message.id;
                const hasValidId = messageId && messageId !== null && messageId !== undefined;
                
                if (hasValidId) {
                    // 可点击的留言项
                    return `
                        <div class="message-item clickable" data-message-id="${messageId}" title="点击查看留言详情">
                            <div class="message-header">
                                <div class="message-author-info">
                                    ${message.avatar ? `<img src="${message.avatar}" alt="${safeAuthor}" class="message-avatar">` : `<div class="message-avatar-placeholder">${safeAuthor.charAt(0).toUpperCase()}</div>`}
                                    <span class="message-author">${safeAuthor}</span>
                                </div>
                                <span class="message-time">${safeTime}</span>
                            </div>
                            <div class="message-subject">${safeSubject}</div>
                            ${safeReplyInfo ? `<div class="message-reply-info">${safeReplyInfo}</div>` : ''}
                        </div>
                    `;
                } else {
                    // 不可点击的留言项
                    return `
                        <div class="message-item disabled">
                            <div class="message-header">
                                <div class="message-author-info">
                                    ${message.avatar ? `<img src="${message.avatar}" alt="${safeAuthor}" class="message-avatar">` : `<div class="message-avatar-placeholder">${safeAuthor.charAt(0).toUpperCase()}</div>`}
                                    <span class="message-author">${safeAuthor}</span>
                                </div>
                                <span class="message-time">${safeTime}</span>
                            </div>
                            <div class="message-subject">${safeSubject}</div>
                            ${safeReplyInfo ? `<div class="message-reply-info">${safeReplyInfo}</div>` : ''}
                        </div>
                    `;
                }
            }).join('');
            
            cardBody.innerHTML = `
                <div class="message-list">
                    ${messagesHtml}
                </div>
            `;
            
            // 添加点击事件监听器
            this.attachClickListeners();
        }
    }

    showError() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML('加载失败，请稍后重试');
        }
    }

    /**
     * 添加点击事件监听器
     */
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

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');
                .view-all-link {
                    font-size: var(--font-size-sm);
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                    transition: var(--transition-fast);
                }

                .view-all-link:hover {
                    color: var(--primary-color-dark);
                    text-decoration: underline;
                }
                .message-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-3);
                }

                .message-item {
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                }

                .message-item.clickable {
                    cursor: pointer;
                    transition: var(--transition-normal);
                }

                .message-item.clickable:hover {
                    background: var(--gray-100);
                    border-color: var(--gray-300);
                    box-shadow: var(--shadow-sm);
                }

                .message-item.disabled {
                    cursor: default;
                    opacity: 0.7;
                }

                .message-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-1);
                    flex-wrap: wrap;
                    gap: var(--spacing-2);
                }

                .message-author-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    flex-shrink: 0;
                }

                .message-avatar {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 1px solid var(--gray-200);
                    flex-shrink: 0;
                }

                .message-avatar-placeholder {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    background: var(--primary-color);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    border: 1px solid var(--gray-200);
                    flex-shrink: 0;
                }

                .message-author {
                    font-weight: 500;
                    color: var(--gray-900);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 120px;
                }

                .message-time {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                    white-space: nowrap;
                    flex-shrink: 0;
                }

                .message-subject {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.5;
                    font-weight: 500;
                    margin-bottom: var(--spacing-1);
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }

                .message-reply-info {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    line-height: 1.4;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }

                /* 确保在小屏幕上不会重叠 */
                @media (max-width: 480px) {
                    .message-header {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: var(--spacing-1);
                    }
                    
                    .message-author-info {
                        max-width: 100%;
                    }
                    
                    .message-author {
                        max-width: 100px;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近留言</h3>
                    <a href="/messages" class="view-all-link" target="_blank">查看全部</a>
                </div>
                <div class="card-body">
                    <div class="message-list">
                        <div class="message-item">
                            <div class="message-subject">正在加载留言...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('recent-messages-card', RecentMessagesCard); 