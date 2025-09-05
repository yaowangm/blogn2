/**
 * 评论表单卡片组件
 * 提供评论输入和提交功能
 */
class CommentFormCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
        this.isSubmitting = false;
        this.isLoggedIn = false;
    }

    async connectedCallback() {
        this.articleId = this.getArticleIdFromUrl();
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        // 加载文章数据并检查评论设置
        await this.loadArticleData();
        
        // 检查是否可以发表评论
        if (!this.canComment()) {
            this.hide();
            return;
        }

        this.render();
        this.bindEvents();
    }

    getArticleIdFromUrl() {
        // 使用基类的统一方法
        return this.getArticleId();
    }

    /**
     * 加载文章数据
     */
    async loadArticleData() {
        try {
            const response = await fetch(`/api/articles/${this.articleId}`);
            if (response.ok) {
                this.articleData = await response.json();
            }
        } catch (error) {
            // 静默处理错误
        }
    }

    /**
     * 检查登录状态
     */
    checkLoginStatus() {
        const token = localStorage.getItem('access_token');
        const userInfo = localStorage.getItem('user_info');
        return !!(token && userInfo);
    }

    /**
     * 检查是否可以发表评论
     */
    canComment() {
        if (!this.articleData) return false;
        
        const allowpost = this.articleData.allowpost || 1;
        this.isLoggedIn = this.checkLoginStatus();
        
        switch (allowpost) {
            case 1: // 允许匿名评论
                return true;
            case 2: // 只允许登录用户评论
                return this.isLoggedIn;
            case 3: // 不允许任何评论
                return false;
            default:
                return false;
        }
    }

    /**
     * 隐藏组件
     */
    hide() {
        this.style.display = 'none';
    }

    render() {
        this.shadowRoot.innerHTML = `
            <div class="card comment-form-card">
                <div class="card-header">
                    <h3>发表评论</h3>
                </div>
                <div class="card-body">
                    <form class="comment-form" id="commentForm">
                        <div class="form-group">
                            <label for="commentContent" class="form-label">评论内容</label>
                            <textarea 
                                id="commentContent" 
                                name="content" 
                                class="form-textarea" 
                                placeholder="请输入您的评论..."
                                rows="4"
                                required
                            ></textarea>
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary" id="submitBtn">
                                <span class="btn-text">发表评论</span>
                                <span class="btn-loading" style="display: none;">提交中...</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        this.addStyles();
    }

    bindEvents() {
        const form = this.shadowRoot.getElementById('commentForm');
        form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();
        if (this.isSubmitting) return;
        
        const contentTextarea = this.shadowRoot.getElementById('commentContent');
        const content = contentTextarea.value.trim();
        
        if (!content) {
            this.showError('请输入评论内容');
            return;
        }

        this.setSubmitting(true);
        
        try {
            const response = await fetch(`/api/articles/${this.articleId}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: content,
                    user_id: this.getCurrentUserId()
                })
            });

            if (response.ok) {
                this.showSuccess('评论发表成功！');
                this.resetForm();
                this.dispatchEvent(new CustomEvent('commentAdded', {
                    detail: { articleId: this.articleId },
                    bubbles: true
                }));
            } else {
                const error = await response.json();
                throw new Error(error.detail || '提交失败');
            }
        } catch (error) {
            this.logError('Failed to submit comment', error);
            this.showError(`评论提交失败: ${error.message}`);
        } finally {
            this.setSubmitting(false);
        }
    }

    setSubmitting(submitting) {
        this.isSubmitting = submitting;
        const submitBtn = this.shadowRoot.getElementById('submitBtn');
        const btnText = this.shadowRoot.querySelector('.btn-text');
        const btnLoading = this.shadowRoot.querySelector('.btn-loading');
        
        if (submitting) {
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline';
        } else {
            submitBtn.disabled = false;
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    }

    resetForm() {
        const form = this.shadowRoot.getElementById('commentForm');
        form.reset();
    }

    getCurrentUserId() {
        return 1; // 临时返回1，实际应该从用户会话获取
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        const existingMessage = this.shadowRoot.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;

        const cardBody = this.shadowRoot.querySelector('.card-body');
        cardBody.appendChild(messageDiv);

        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 3000);
    }

    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                .comment-form-card {
                    margin-bottom: var(--spacing-6);
                }
                .card-header {
                    padding: var(--spacing-4) var(--spacing-6);
                    border-bottom: 1px solid var(--gray-200);
                    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
                    background-color: var(--gray-50);
                }
                .card-header h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-800);
                    margin: 0;
                }
                .comment-form {
                    padding: var(--spacing-4) var(--spacing-6);
                }
                .form-group {
                    margin-bottom: var(--spacing-4);
                }
                .form-label {
                    display: block;
                    font-weight: 500;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-2);
                }
                .form-textarea {
                    width: 100%;
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-family: inherit;
                    font-size: var(--font-size-base);
                    line-height: 1.5;
                    resize: vertical;
                    transition: border-color var(--transition-fast);
                }
                .form-textarea:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgb(37 99 235 / 0.1);
                }
                .form-actions {
                    display: flex;
                    justify-content: flex-end;
                }
                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-3) var(--spacing-6);
                    border: none;
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-base);
                    font-weight: 500;
                    text-decoration: none;
                    cursor: pointer;
                    transition: all var(--transition-fast);
                    min-width: 100px;
                }
                .btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                .btn-primary {
                    background-color: var(--primary-color);
                    color: var(--white);
                }
                .btn-primary:hover:not(:disabled) {
                    background-color: var(--primary-hover);
                }
                .message {
                    padding: var(--spacing-3) var(--spacing-4);
                    border-radius: var(--radius-md);
                    margin: var(--spacing-4) var(--spacing-6) 0;
                    font-size: var(--font-size-sm);
                }
                .message-success {
                    background-color: rgb(16 185 129 / 0.1);
                    color: var(--success-color);
                    border: 1px solid rgb(16 185 129 / 0.2);
                }
                .message-error {
                    background-color: rgb(239 68 68 / 0.1);
                    color: var(--error-color);
                    border: 1px solid rgb(239 68 68 / 0.2);
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

customElements.define('comment-form-card', CommentFormCard);
