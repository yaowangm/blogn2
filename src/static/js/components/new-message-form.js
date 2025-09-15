class NewMessageForm extends BaseComponent {
    constructor() {
        super();
        this.submitting = false;
    }

    connectedCallback() {
        this.render();
        this.setupEventListeners();
    }

    setupEventListeners() {
        const form = this.shadowRoot.querySelector('#message-form');
        if (form) {
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
        const subject = formData.get('subject').trim();
        const content = formData.get('content').trim();

        // 验证输入
        if (!subject) {
            this.showError('请输入留言标题');
            return;
        }

        if (!content) {
            this.showError('请输入留言内容');
            return;
        }

        if (subject.length > 200) {
            this.showError('标题不能超过200个字符');
            return;
        }

        this.submitting = true;
        this.updateSubmitButton(true);

        try {
            // 准备请求头
            const headers = {
                'Content-Type': 'application/json',
            };
            
            // 添加认证头（如果用户已登录）
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch('/api/messages', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    subject: subject,
                    content: content,
                    user_id: this.getCurrentUserId()  // 获取当前用户ID
                })
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
            this.showSuccess('留言发表成功！');
            
            // 通知消息列表刷新到第一页
            this.refreshMessagesList();

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

    getCurrentUserId() {
        // 从localStorage获取用户信息
        const userInfo = localStorage.getItem('user_info');
        if (userInfo) {
            try {
                const user = JSON.parse(userInfo);
                return user.id;
            } catch (e) {
                console.error('Failed to parse user info:', e);
            }
        }
        return 0; // 匿名用户返回0
    }

    updateSubmitButton(submitting) {
        const button = this.shadowRoot.querySelector('#submit-btn');
        if (button) {
            button.disabled = submitting;
            button.textContent = submitting ? '发表中...' : '发表留言';
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
                }

                .btn-primary {
                    background: var(--primary-color);
                    color: var(--white);
                }

                .btn-primary:hover:not(:disabled) {
                    background: var(--primary-color-dark);
                }

                .btn-primary:disabled {
                    background: var(--gray-400);
                    cursor: not-allowed;
                }

                .btn-secondary {
                    background: var(--gray-100);
                    color: var(--gray-700);
                    border: 1px solid var(--gray-300);
                }

                .btn-secondary:hover {
                    background: var(--gray-200);
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
                    <h3 class="card-title">发表新留言</h3>
                </div>
                <div class="card-body">
                    <form id="message-form">
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
                                发表留言
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