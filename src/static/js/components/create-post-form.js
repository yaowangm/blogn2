/**
 * 发表博客文章表单组件
 * 根据projectitem表定义生成表单
 */
class CreatePostForm extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.categories = [];
        this.loading = false;
        this.formData = {
            name: '',
            comment: '',
            itemtype: 1, // 默认为文章类型
            itemsize: 0,
            folderid: null,
            status: 1, // 默认为正常状态
            allowpost: 1 // 默认为允许评论
        };
    }

    async connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        this.render();
        await this.loadCategories();
        this.addEventListeners();
    }

    getProjectIdFromUrl() {
        // 从URL路径中提取项目ID
        const pathParts = window.location.pathname.split('/');
        const blogIndex = pathParts.indexOf('blog');
        if (blogIndex !== -1 && pathParts[blogIndex + 1]) {
            return parseInt(pathParts[blogIndex + 1]);
        }
        return null;
    }

    async loadCategories() {
        if (!this.projectId) {
            console.warn('没有项目ID，无法加载分类');
            return;
        }

        try {
            console.log(`正在加载项目 ${this.projectId} 的分类...`);
            const response = await fetch(`/api/projects/${this.projectId}/categories`);
            if (response.ok) {
                const data = await response.json();
                // API直接返回分类数组，不需要.categories字段
                this.categories = data || [];
                console.log('分类数据加载成功:', this.categories);
                this.render();
            } else {
                console.warn('获取分类失败，使用空分类列表:', response.status);
                this.categories = [];
                this.render();
            }
        } catch (error) {
            console.error('加载分类失败:', error);
            this.categories = [];
            this.render();
        }
    }

    addEventListeners() {
        // 表单提交事件
        this.addEventListener('submit', (event) => {
            event.preventDefault();
            this.handleSubmit();
        });
    }

    handleInputChange(field, value) {
        this.formData[field] = value;
    }

    async handleSubmit() {
        if (this.loading) {
            return;
        }

        // 验证必填字段
        if (!this.formData.name.trim()) {
            this.showError('文章标题不能为空');
            return;
        }

        if (!this.formData.comment.trim()) {
            this.showError('文章内容不能为空');
            return;
        }

        this.loading = true;
        this.render();

        try {
            const token = localStorage.getItem('access_token');
            const headers = {
                'Content-Type': 'application/json'
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            // 准备提交数据
            const submitData = {
                ...this.formData,
                projectid: this.projectId,
                userid: this.getCurrentUserId(),
                createtime: new Date().toISOString(),
                updatetime: new Date().toISOString(),
                lastmodifytime: new Date().toISOString(),
                accesscount: 0,
                commentcount: 0
            };

            const response = await fetch('/api/projects/create-post', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(submitData)
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess('文章发表成功！');
                // 延迟跳转回博客页面
                setTimeout(() => {
                    window.location.href = `/blog/${this.projectId}`;
                }, 2000);
            } else {
                const errorData = await response.json();
                this.showError(errorData.detail || '发表文章失败');
            }
        } catch (error) {
            console.error('发表文章失败:', error);
            this.showError('网络错误，请稍后重试');
        } finally {
            this.loading = false;
            this.render();
        }
    }

    getCurrentUserId() {
        const userInfo = localStorage.getItem('user_info');
        if (userInfo) {
            const currentUser = JSON.parse(userInfo);
            return currentUser.id;
        }
        return null;
    }

    showError(message) {
        // 显示错误消息
        const errorElement = this.shadowRoot.querySelector('.error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    showSuccess(message) {
        // 显示成功消息
        const successElement = this.shadowRoot.querySelector('.success-message');
        if (successElement) {
            successElement.textContent = message;
            successElement.style.display = 'block';
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }
                
                @import url('/static/css/common-components.css');
                
                .card {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                }
                
                .card-header {
                    padding: var(--spacing-5);
                    border-bottom: 1px solid var(--gray-200);
                    background: var(--gray-50);
                }
                
                .card-title {
                    font-size: var(--font-size-xl);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }
                
                .card-body {
                    padding: var(--spacing-6);
                }
                
                .form-group {
                    margin-bottom: var(--spacing-5);
                }
                
                .form-label {
                    display: block;
                    font-weight: 500;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-2);
                    font-size: var(--font-size-sm);
                }
                
                .form-label.required::after {
                    content: ' *';
                    color: var(--error-color);
                }
                
                .form-input,
                .form-textarea,
                .form-select {
                    width: 100%;
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    font-size: var(--font-size-sm);
                    transition: var(--transition-fast);
                    background: var(--white);
                }
                
                .form-input:focus,
                .form-textarea:focus,
                .form-select:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                }
                
                .form-textarea {
                    min-height: 200px;
                    resize: vertical;
                    font-family: inherit;
                }
                
                .form-textarea.large {
                    min-height: 400px;
                }
                
                .form-actions {
                    display: flex;
                    gap: var(--spacing-3);
                    justify-content: flex-end;
                    margin-top: var(--spacing-6);
                    padding-top: var(--spacing-5);
                    border-top: 1px solid var(--gray-200);
                }
                
                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: var(--spacing-3) var(--spacing-6);
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    border-radius: var(--radius-md);
                    border: 1px solid transparent;
                    cursor: pointer;
                    transition: var(--transition-fast);
                    text-decoration: none;
                    line-height: 1;
                }
                
                .btn-primary {
                    background-color: var(--primary-color);
                    color: var(--white);
                    border-color: var(--primary-color);
                }
                
                .btn-primary:hover:not(:disabled) {
                    background-color: var(--primary-hover);
                    border-color: var(--primary-hover);
                }
                
                .btn-secondary {
                    background-color: var(--white);
                    color: var(--gray-700);
                    border-color: var(--gray-300);
                }
                
                .btn-secondary:hover:not(:disabled) {
                    background-color: var(--gray-50);
                    border-color: var(--gray-400);
                }
                
                .btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                
                .error-message,
                .success-message {
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    margin-bottom: var(--spacing-4);
                    font-size: var(--font-size-sm);
                    display: none;
                }
                
                .error-message {
                    background-color: #fef2f2;
                    color: #dc2626;
                    border: 1px solid #fecaca;
                }
                
                .success-message {
                    background-color: #f0fdf4;
                    color: #16a34a;
                    border: 1px solid #bbf7d0;
                }
                
                .loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: var(--spacing-2);
                    color: var(--gray-600);
                }
                
                .loading-spinner {
                    width: 16px;
                    height: 16px;
                    border: 2px solid var(--gray-300);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .form-help {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    margin-top: var(--spacing-1);
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                        </svg>
                        发表博客文章
                    </h2>
                </div>
                <div class="card-body">
                    <div class="error-message"></div>
                    <div class="success-message"></div>
                    
                    <form>
                        <div class="form-group">
                            <label class="form-label required" for="name">文章标题</label>
                            <input 
                                type="text" 
                                id="name" 
                                class="form-input" 
                                placeholder="请输入文章标题"
                                value="${this.formData.name}"
                                onchange="this.getRootNode().host.handleInputChange('name', this.value)"
                                required
                            >
                            <div class="form-help">文章标题将显示在博客列表中，建议简洁明了</div>
                        </div>

                        <div class="form-group">
                            <label class="form-label required" for="comment">文章内容</label>
                            <textarea 
                                id="comment" 
                                class="form-textarea large" 
                                placeholder="请输入文章内容..."
                                onchange="this.getRootNode().host.handleInputChange('comment', this.value)"
                                required
                            >${this.formData.comment}</textarea>
                            <div class="form-help">支持Markdown格式，可以包含图片、链接等</div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="folderid">文章分类</label>
                            <select 
                                id="folderid" 
                                class="form-select"
                                onchange="this.getRootNode().host.handleInputChange('folderid', this.value ? parseInt(this.value) : null)"
                            >
                                <option value="">选择分类（可选）</option>
                                ${this.categories.map(category => `
                                    <option value="${category.id}" ${this.formData.folderid === category.id ? 'selected' : ''}>
                                        ${category.name.trim()} (${category.count})
                                    </option>
                                `).join('')}
                            </select>
                            <div class="form-help">选择文章所属分类，便于读者浏览</div>
                        </div>


                        <div class="form-group">
                            <label class="form-label" for="allowpost">评论设置</label>
                            <select 
                                id="allowpost" 
                                class="form-select"
                                onchange="this.getRootNode().host.handleInputChange('allowpost', parseInt(this.value))"
                            >
                                <option value="1" ${this.formData.allowpost === 1 ? 'selected' : ''}>允许匿名评论</option>
                                <option value="2" ${this.formData.allowpost === 2 ? 'selected' : ''}>只允许登录用户评论</option>
                                <option value="3" ${this.formData.allowpost === 3 ? 'selected' : ''}>不允许任何评论</option>
                            </select>
                            <div class="form-help">选择文章的评论权限设置</div>
                        </div>

                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="window.history.back()">
                                取消
                            </button>
                            <button type="submit" class="btn btn-primary" ${this.loading ? 'disabled' : ''}>
                                ${this.loading ? `
                                    <div class="loading">
                                        <div class="loading-spinner"></div>
                                        发表中...
                                    </div>
                                ` : '发表文章'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }
}

customElements.define('create-post-form', CreatePostForm);
