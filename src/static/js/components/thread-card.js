class ThreadCard extends BaseComponent {
    constructor() {
        super();
        this.threadId = null;
        this.messages = [];
        this.loading = true;
    }

    static get observedAttributes() {
        return ['thread-id'];
    }

    connectedCallback() {
        this.threadId = this.getAttribute('thread-id');
        this.render();
        this.loadThread();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'thread-id' && newValue) {
            this.threadId = newValue;
            this.loadThread();
        }
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

    async loadThread() {
        if (!this.threadId) {
            this.showError('无效的主题ID');
            return;
        }

        this.loading = true;
        this.updateLoadingState();
        
        try {
            const response = await fetch(`/api/thread/${this.threadId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch thread');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading thread', error);
            this.showError('加载主题失败，请稍后重试');
        }
    }

    updateContent(data) {
        this.messages = data.messages || [];
        this.renderMessagesList();
        
        // 更新页面标题
        this.updatePageTitle();
    }

    renderMessagesList() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            if (this.messages.length === 0) {
                cardBody.innerHTML = `
                    <div class="thread-messages">
                        <div class="message-item">
                            <div class="message-subject">暂无留言</div>
                        </div>
                    </div>
                `;
                return;
            }
            
            const messagesHtml = this.messages.map((message, index) => {
                // 安全处理所有文本字段，防止HTML注入和XSS攻击
                const safeAuthor = this.escapeHtml(message.author);
                const safeSubject = this.escapeHtml(message.subject);
                const safeContent = this.escapeHtml(message.content);
                const safePostTime = this.escapeHtml(message.post_time);
                
                // 判断是否为主贴
                const isMainPost = message.is_main_post;
                const messageClass = isMainPost ? 'message-item main-post' : 'message-item reply-post';
                
                return `
                    <div class="${messageClass}">
                        <div class="message-header">
                            ${isMainPost ? `<div class="message-title">${safeSubject}</div>` : ''}
                            <div class="message-meta">
                                <span class="message-author">${safeAuthor}</span>
                                <span class="message-time">${safePostTime}</span>
                            </div>
                        </div>
                        <div class="message-content">${safeContent}</div>
                        ${isMainPost ? '<div class="main-post-indicator">主题</div>' : ''}
                    </div>
                `;
            }).join('');
            
            cardBody.innerHTML = `
                <div class="thread-messages">
                    ${messagesHtml}
                </div>
            `;
        }
    }

    updateLoadingState() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = `
                <div class="thread-messages">
                    <div class="message-item">
                        <div class="message-subject">正在加载主题...</div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * 刷新主题消息列表
     * 供外部组件调用，用于在发表跟贴后刷新显示
     */
    refreshMessages() {
        if (this.threadId) {
            this.loadThread();
        }
    }

    showError(message) {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML(message);
        }
    }

    updatePageTitle() {
        // 获取主贴的标题
        const mainPost = this.messages.find(msg => msg.is_main_post);
        if (mainPost && mainPost.subject) {
            // 限制标题为前20个字符
            const title = mainPost.subject.length > 20 
                ? mainPost.subject.substring(0, 20) + '...' 
                : mainPost.subject;
            
            // 更新页面标题
            document.title = `${title} - 留言本`;
        } else {
            // 如果没有找到主贴或标题，使用默认标题
            document.title = '留言本主题 - BlogN2';
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

                .thread-messages {
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
                    position: relative;
                }

                .message-item:hover {
                    background: var(--gray-100);
                    border-color: var(--gray-300);
                }

                .main-post {
                    background: var(--primary-color-light);
                    border-color: var(--primary-color);
                }

                .reply-post {
                    margin-left: var(--spacing-6);
                    border-left: 3px solid var(--gray-300);
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

                .message-content {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.6;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    white-space: pre-wrap;
                }

                .main-post-indicator {
                    position: absolute;
                    top: var(--spacing-2);
                    right: var(--spacing-2);
                    background: var(--primary-color);
                    color: var(--white);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-sm);
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                }

                /* 响应式设计 */
                @media (max-width: 768px) {
                    .message-meta {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: var(--spacing-1);
                    }
                    
                    .reply-post {
                        margin-left: var(--spacing-3);
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">主题讨论</h3>
                </div>
                <div class="card-body">
                    <div class="thread-messages">
                        <div class="message-item">
                            <div class="message-subject">正在加载主题...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('thread-card', ThreadCard);
