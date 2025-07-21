class RecentMessagesCard extends BaseComponent {
    constructor() {
        super();
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
            
            const messagesHtml = messages.map(message => `
                <div class="message-item">
                    <div class="message-header">
                        <div class="message-author-info">
                            ${message.avatar ? `<img src="${message.avatar}" alt="${message.author}" class="message-avatar">` : `<div class="message-avatar-placeholder">${message.author.charAt(0).toUpperCase()}</div>`}
                            <span class="message-author">${message.author}</span>
                        </div>
                        <span class="message-time">${message.time}</span>
                    </div>
                    <div class="message-subject">${message.subject}</div>
                    ${message.reply_info ? `<div class="message-reply-info">${message.reply_info}</div>` : ''}
                </div>
            `).join('');
            
            cardBody.innerHTML = `
                <div class="message-list">
                    ${messagesHtml}
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

                .message-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-2);
                }

                .message-author-info {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .message-avatar {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 1px solid var(--gray-200);
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
                }

                .message-author {
                    font-weight: 500;
                    color: var(--gray-900);
                }

                .message-time {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                .message-subject {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.5;
                    font-weight: 500;
                    margin-bottom: var(--spacing-1);
                }

                .message-reply-info {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    line-height: 1.4;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近留言</h3>
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