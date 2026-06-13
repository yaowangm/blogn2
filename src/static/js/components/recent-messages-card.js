class RecentMessagesCard extends BaseComponent {
    constructor() {
        super();
        this.messages = [];
        this.loading = true;
    }

    connectedCallback() {
        this.render();
        BaseComponent.observeWhenVisible(this, () => this.loadContent());
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
                    <div class="post-list">
                        <div class="post-item post-item-block">
                            <div class="post-content">
                                <p class="post-excerpt">暂无留言</p>
                            </div>
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
                
                const avatarHtml = message.avatar
                    ? `<span class="author-avatar"><img src="${message.avatar}" alt=""></span>`
                    : `<span class="author-avatar"><span class="author-avatar-fallback">${safeAuthor.charAt(0).toUpperCase()}</span></span>`;

                const contentHtml = `
                    <div class="article-meta">
                        <div class="meta-items-left">
                            <div class="meta-item meta-item-author">
                                ${avatarHtml}
                                <span class="author-name">${safeAuthor}</span>
                            </div>
                        </div>
                        <div class="meta-item">
                            <span>${safeTime}</span>
                        </div>
                    </div>
                    <p class="post-title">${safeSubject}</p>
                    ${safeReplyInfo ? `<p class="post-excerpt">${safeReplyInfo}</p>` : ''}
                `;
                
                if (hasValidId) {
                    return `
                        <div class="post-item clickable" data-message-id="${messageId}" title="点击查看留言详情">
                            <div class="post-content">
                                ${contentHtml}
                            </div>
                        </div>
                    `;
                }

                return `
                    <div class="post-item post-item-block disabled">
                        <div class="post-content">
                            ${contentHtml}
                        </div>
                    </div>
                `;
            }).join('');
            
            cardBody.innerHTML = `
                <div class="post-list">
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
        const messageItems = this.shadowRoot.querySelectorAll('.post-item[data-message-id]');
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

                .post-item.clickable {
                    cursor: pointer;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近留言</h3>
                    <a href="/messages" class="view-all-link" target="_blank">查看全部</a>
                </div>
                <div class="card-body">
                    <div class="post-list">
                        <div class="post-item post-item-block">
                            <div class="post-content">
                                <p class="post-excerpt">正在加载留言...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('recent-messages-card', RecentMessagesCard); 