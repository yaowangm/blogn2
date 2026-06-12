class NewMessageForm extends BaseComponent {
    static get observedAttributes() {
        return ['thread-id'];
    }

    constructor() {
        super();
        this.submitting = false;
        this.threadId = null;
    }

    connectedCallback() {
        // 获取thread-id属性
        const threadIdAttr = this.getAttribute('thread-id');
        this.threadId = threadIdAttr ? parseInt(threadIdAttr) : null;
        this.render();
        this.setupEventListeners();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'thread-id') {
            this.threadId = newValue ? parseInt(newValue) : null;
            this.render(); // 重新渲染以更新UI
            this.setupEventListeners(); // 重新绑定事件监听器
        }
    }

    setupEventListeners() {
        const form = this.shadowRoot.querySelector('#message-form');
        if (form) {
            // 移除旧的事件监听器（如果有的话）
            form.removeEventListener('submit', this.handleSubmit);
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        const clearBtn = this.shadowRoot.querySelector('#clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearForm());
        }
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.submitting) {
            return;
        }

        const formData = new FormData(event.target);
        const subject = formData.get('subject') ? formData.get('subject').trim() : '';
        const content = formData.get('content') ? formData.get('content').trim() : '';

        // 验证输入
        if (this.threadId === null && !subject) {
            this.showError('请输入留言标题');
            return;
        }

        if (!content) {
            this.showError('请输入留言内容');
            return;
        }

        if (subject && subject.length > 200) {
            this.showError('标题不能超过200个字符');
            return;
        }

        this.submitting = true;
        this.updateSubmitButton(true);

        try {
            const requestData = {
                subject: this.threadId !== null ? '' : subject,  // 跟贴时标题为空
                content: content,
                user_id: UserManager.getCurrentUserId(),  // 使用公用的用户管理方法
                thread_id: this.threadId  // 如果有threadId，则作为跟贴
            };
            
            const response = await fetch('/api/messages', {
                method: 'POST',
                headers: UserManager.createHeaders({
                    'Content-Type': 'application/json',
                }),
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '提交失败');
            }

            // 提交成功，清空表单
            const form = this.shadowRoot.querySelector('#message-form');
            if (form) {
                form.reset();
            }
            this.showSuccess(this.threadId !== null ? '跟贴发表成功！' : '留言发表成功！');
            
            // 根据是否有threadId决定刷新策略
            if (this.threadId !== null) {
                // 跟贴成功，通知主题卡片刷新
                this.refreshThreadCard();
            } else {
                // 主贴成功，通知消息列表刷新到第一页
                this.refreshMessagesList();
            }

        } catch (error) {
            this.logError('Error submitting message', error);
            this.showError(error.message || '提交失败，请稍后重试');
        } finally {
            this.submitting = false;
            this.updateSubmitButton(false);
        }
    }

    refreshMessagesList() {
        // 查找消息列表组件并刷新到第一页
        const messagesListCard = document.querySelector('messages-list-card');
        if (messagesListCard && typeof messagesListCard.refreshToFirstPage === 'function') {
            messagesListCard.refreshToFirstPage();
        }
    }

    refreshThreadCard() {
        // 查找主题卡片组件并刷新
        const threadCard = document.querySelector('thread-card');
        if (threadCard && typeof threadCard.refreshMessages === 'function') {
            threadCard.refreshMessages();
        }
    }

    clearForm() {
        const form = this.shadowRoot.querySelector('#message-form');
        if (form) {
            form.reset();
        }
        
        // 隐藏错误和成功消息
        const errorDiv = this.shadowRoot.querySelector('.error-message');
        const successDiv = this.shadowRoot.querySelector('.success-message');
        if (errorDiv) errorDiv.style.display = 'none';
        if (successDiv) successDiv.style.display = 'none';
    }


    updateSubmitButton(submitting) {
        const button = this.shadowRoot.querySelector('#submit-btn');
        if (button) {
            button.disabled = submitting;
            const buttonText = this.threadId !== null ? '发表跟贴' : '发表留言';
            button.textContent = submitting ? '发表中...' : buttonText;
        }
    }

    showError(message) {
        const errorDiv = this.shadowRoot.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }

    showSuccess(message) {
        const successDiv = this.shadowRoot.querySelector('.success-message');
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            
            // 3秒后隐藏成功消息
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 3000);
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

                .form-group {
                    margin-bottom: var(--spacing-4);
                }

                .form-label {
                    display: block;
                    font-weight: 500;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-2);
                    font-size: var(--font-size-sm);
                }

                .form-input {
                    width: 100%;
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    transition: var(--transition-fast);
                    box-sizing: border-box;
                }

                .form-input:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px var(--primary-color-light);
                }

                .form-textarea {
                    min-height: 120px;
                    resize: vertical;
                    font-family: inherit;
                }

                .form-actions {
                    display: flex;
                    justify-content: flex-end;
                    gap: var(--spacing-3);
                }

                .btn {
                    padding: var(--spacing-3) var(--spacing-5);
                    border: none;
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    z-index: 1;
                }

                .btn-primary {
                    background: var(--primary-color);
                    color: #ffffff;
                }

                .btn-primary:hover:not(:disabled) {
                    background: var(--primary-hover);
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }

                .btn-primary:disabled {
                    background: #94a3b8;
                    cursor: not-allowed;
                }

                .btn-secondary {
                    background: #f1f5f9;
                    color: #374151;
                    border: 1px solid #d1d5db;
                }

                .btn-secondary:hover {
                    background: #e2e8f0;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }

                .error-message {
                    display: none;
                    color: var(--error-color);
                    font-size: var(--font-size-sm);
                    margin-top: var(--spacing-2);
                    padding: var(--spacing-2);
                    background: var(--error-color-light);
                    border-radius: var(--radius-md);
                    border: 1px solid var(--error-color);
                }

                .success-message {
                    display: none;
                    color: var(--success-color);
                    font-size: var(--font-size-sm);
                    margin-top: var(--spacing-2);
                    padding: var(--spacing-2);
                    background: var(--success-color-light);
                    border-radius: var(--radius-md);
                    border: 1px solid var(--success-color);
                }

                /* 响应式设计 */
                @media (max-width: 768px) {
                    .form-actions {
                        flex-direction: column;
                    }
                    
                    .btn {
                        width: 100%;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">${this.threadId !== null ? '发表跟贴' : '发表新留言'}</h3>
                </div>
                <div class="card-body">
                    <form id="message-form">
                        ${this.threadId === null ? `
                        <div class="form-group">
                            <label for="subject" class="form-label">标题</label>
                            <input 
                                type="text" 
                                id="subject" 
                                name="subject" 
                                class="form-input" 
                                placeholder="请输入留言标题"
                                maxlength="200"
                                required
                            >
                        </div>
                        ` : ''}
                        
                        <div class="form-group">
                            <label for="content" class="form-label">内容</label>
                            <textarea 
                                id="content" 
                                name="content" 
                                class="form-input form-textarea" 
                                placeholder="请输入留言内容"
                                required
                            ></textarea>
                        </div>
                        
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" id="clear-btn">
                                清空
                            </button>
                            <button type="submit" id="submit-btn" class="btn btn-primary">
                                ${this.threadId !== null ? '发表跟贴' : '发表留言'}
                            </button>
                        </div>
                        
                        <div class="error-message"></div>
                        <div class="success-message"></div>
                    </form>
                </div>
            </div>
        `;
    }
}

customElements.define('new-message-form', NewMessageForm);