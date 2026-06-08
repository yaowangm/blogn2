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
            
            // 检查用户是否为管理员
            const isAdmin = UserManager.isAdmin();
            
            const messagesHtml = this.messages.map((message, index) => {
                // 安全处理所有文本字段，防止HTML注入和XSS攻击
                const safeAuthor = this.escapeHtml(message.author);
                const safeSubject = this.escapeHtml(message.subject);
                const safeContent = this.escapeHtml(message.content);
                const safePostTime = this.escapeHtml(message.post_time);
                
                // 判断是否为主贴
                const isMainPost = message.is_main_post;
                const messageClass = isMainPost ? 'message-item main-post' : 'message-item reply-post';
                
                // 生成删除按钮（仅管理员可见）
                const deleteButton = isAdmin ? `
                    <button class="delete-button" data-message-id="${message.id}" data-is-main="${isMainPost}">
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
                    <div class="${messageClass}" data-message-id="${message.id}">
                        <div class="message-header">
                            ${isMainPost ? `<div class="message-title">${safeSubject}</div>` : ''}
                            <div class="message-meta">
                                <span class="message-author">${safeAuthor}</span>
                                <span class="message-time">${safePostTime}</span>
                                ${deleteButton}
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
            
            // 添加删除按钮事件监听器
            if (isAdmin) {
                this.attachDeleteListeners();
            }
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
                
                // 如果是主贴被删除，跳转到留言本首页
                if (result.is_main_post) {
                    window.location.href = '/messages';
                } else {
                    // 如果是跟贴被删除，刷新当前页面
                    this.loadThread();
                }
            } else {
                // 删除失败
                alert(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除留言失败:', error);
            alert('删除失败，请稍后重试');
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
                @import url('/static/css/common-components.css');
                :host {
                    display: block;
                }
                .thread-messages {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }

                .message-item {
                    padding: var(--spacing-3) var(--spacing-4);
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
