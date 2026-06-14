class RecentMessagesCard extends BaseComponent {
    constructor() {
        super();
        this.messages = [];
        this.loading = true;
        this.error = false;
    }

    connectedCallback() {
        this.render();
        BaseComponent.observeWhenVisible(this, () => this.loadContent());
    }

    async loadContent() {
        try {
            this.loading = true;
            this.error = false;
            this.render();

            const response = await fetch('/api/blogs/messages/recent');
            if (!response.ok) {
                throw new Error('Failed to fetch recent messages');
            }
            this.messages = await response.json();
        } catch (error) {
            this.logError('Error loading recent messages', error);
            this.messages = [];
            this.error = true;
        } finally {
            this.loading = false;
            this.render();
        }
    }

    renderMessages() {
        return MessageListRenderer.renderMessageList(this, this.messages);
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
                    flex-shrink: 0;
                }

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

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                ${MessageListRenderer.getRowStyles()}
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <span class="title-icon">${typeof Icons !== 'undefined' ? Icons.message : ''}</span>
                        最近留言
                    </h3>
                    <a href="/messages" class="view-all-link" target="_blank" rel="noopener noreferrer">查看全部</a>
                </div>
                <div class="card-body">
                    ${this.loading ? `<div class="loading">${this.createLoadingHTML()}</div>` :
                      this.error ? this.createErrorHTML('加载失败，请稍后重试') :
                      this.renderMessages()}
                </div>
            </div>
        `;
    }
}

customElements.define('recent-messages-card', RecentMessagesCard);
