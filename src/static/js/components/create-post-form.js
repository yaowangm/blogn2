/**
 * 发表博客文章表单组件 (CreatePostForm)
 * 
 * 提供博客文章创建功能，包括：
 * - 文章标题、内容、分类的输入
 * - Markdown实时预览功能
 * - 单张和多张图片上传支持
 * - 表单验证和错误处理
 * - 临时文件管理和清理
 * 
 * 继承自BaseComponent，使用统一的工具方法。
 */
class CreatePostForm extends BaseComponent {
    constructor() {
        super();
        this.projectId = null;
        this.categories = [];
        this.loading = false;
        this.submitting = false; // 添加提交锁
        this.formData = {
            name: '',
            comment: '',
            itemtype: 1, // 默认为文章类型 (ArticleStatus.NORMAL)
            itemsize: 0, // 将在提交时计算
            folderid: null,
            status: 1, // 默认为正常状态
            allowpost: 1, // 默认为允许评论
            attachment: null, // 第一张图片附件
            attachments: [] // 多张图片附件
        };
        this.uploadedImage = null; // 上传的第一张图片信息
        this.uploadedImages = []; // 上传的多张图片信息
        this.previewMode = false; // 预览模式状态
        this._draftCacheKey = null;
        this._draftAutoSaver = null;
    }

    disconnectedCallback() {
        PostFormDraftMixin.disconnected(this);
    }

    initDraftCache() {
        const userId = UserManager.getCurrentUserId();
        PostFormDraftMixin.init(this, PostFormDraftCache.getCreateKey(userId, this.projectId));
    }

    getDraftFormData() {
        return PostFormDraftMixin.getDraftFormData(this);
    }

    restoreDraftIfAny() {
        return PostFormDraftMixin.restoreDraftIfAny(this);
    }

    applyDraft(draft) {
        PostFormDraftMixin.applyDraft(this, draft);
    }

    syncFormFieldsFromDraft(draft) {
        PostFormDraftMixin.syncFormFieldsFromDraft(this, draft);
    }

    clearDraftCache() {
        PostFormDraftMixin.clearDraftCache(this);
    }

    clearDraftOnSessionInvalid() {
        PostFormDraftMixin.clearDraftOnSessionInvalid(this);
    }

    startDraftAutoSave() {
        PostFormDraftMixin.startDraftAutoSave(this);
    }

    async connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        
        // 检查用户登录状态
        const isLoggedIn = UserManager.isLoggedIn();
        
        if (!isLoggedIn) {
            this.showLoginRequired();
            return;
        }

        this.initDraftCache();
        this.restoreDraftIfAny();
        
        this.render();
        await this.loadCategories();
        this.addEventListeners();
        this.startDraftAutoSave();
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
            return;
        }

        try {
            const response = await fetch(`/api/projects/${this.projectId}/categories`);
            if (response.ok) {
                const data = await response.json();
                // API直接返回分类数组，不需要.categories字段
                this.categories = data || [];
                this.updateCategories();
            } else {
                this.categories = [];
                this.updateCategories();
            }
        } catch (error) {
            this.categories = [];
            this.updateCategories();
        }
    }

    addEventListeners() {
        // 等待DOM渲染完成后再添加事件监听器
        setTimeout(() => {
            this.bindAllEvents();
        }, 100);
    }

    handleInputChange(field, value) {
        this.formData[field] = value;
        
        // 如果正在预览模式且内容发生变化，更新预览
        if (field === 'comment' && this.previewMode) {
            this.updatePreview();
        }
    }

    /**
     * 切换预览模式
     */
    togglePreview() {
        this.previewMode = !this.previewMode;
        
        const editor = this.shadowRoot.querySelector('.content-editor');
        const preview = this.shadowRoot.querySelector('.content-preview');
        const previewIcon = this.shadowRoot.querySelector('.preview-icon');
        const editIcon = this.shadowRoot.querySelector('.edit-icon');
        const toggleBtn = this.shadowRoot.querySelector('#previewToggleBtn');
        
        if (this.previewMode) {
            editor.style.display = 'none';
            preview.style.display = 'block';
            if (previewIcon) previewIcon.style.display = 'none';
            if (editIcon) editIcon.style.display = 'inline-flex';
            if (toggleBtn) {
                toggleBtn.title = '返回编辑';
                toggleBtn.setAttribute('aria-label', '返回编辑');
            }
            this.updatePreview();
        } else {
            editor.style.display = 'block';
            preview.style.display = 'none';
            if (previewIcon) previewIcon.style.display = 'inline-flex';
            if (editIcon) editIcon.style.display = 'none';
            if (toggleBtn) {
                toggleBtn.title = '预览';
                toggleBtn.setAttribute('aria-label', '预览');
            }
        }
    }

    /**
     * 更新预览内容
     */
    updatePreview() {
        const previewContent = this.shadowRoot.querySelector('.preview-content');
        const content = this.formData.comment || '';
        this.renderMarkdownPreview(previewContent, content);
    }



    async handleImageUpload(file) {
        if (!file) return;

        // 验证文件类型
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('只支持jpg、png、gif格式的图片');
            return;
        }

        // 验证文件大小（1MB = 1048576字节）
        if (file.size > 1048576) {
            this.showError('图片大小不能超过1MB');
            return;
        }

        // 检查是否已上传过多图片（最多10张）
        if (this.uploadedImages.length >= 10) {
            this.showError('最多只能上传10张图片');
            return;
        }

        try {
            // 创建FormData
            const formData = new FormData();
            formData.append('file', file);

            // 上传文件到临时目录
            const response = await fetch('/api/upload?temp=true', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                
                // 如果是第一张图片且没有主图，设置为主图片
                if (!this.uploadedImage) {
                    this.uploadedImage = {
                        ...result,
                        comment: '', // 用户可以添加图片描述
                        id: Date.now() + Math.random(), // 临时ID
                        is_temp: true // 标记为临时文件
                    };
                    this.formData.attachment = result.relative_path;
                } else {
                    // 添加到多张图片列表（不包括主图）
                    this.uploadedImages.push({
                        ...result,
                        comment: '', // 用户可以添加图片描述
                        id: Date.now() + Math.random(), // 临时ID
                        is_temp: true // 标记为临时文件
                    });
                }
                
                this.formData.attachments = this.uploadedImages;
                this.showSuccess(`图片已选择，将在保存时移动到正式目录 (${this.uploadedImages.length + (this.uploadedImage ? 1 : 0)}/10)`);
                this.updateImagePreview();
            } else {
                const errorData = await response.json();
                console.error('Upload failed:', errorData);
                this.showError(errorData.detail || '图片上传失败');
            }
        } catch (error) {
            console.error('图片上传失败:', error);
            this.showError(`网络错误: ${error.message}`);
        }
    }

    removeImage(imageId = null) {
        if (imageId) {
            // 删除指定的图片
            const imageIndex = this.uploadedImages.findIndex(img => img.id === imageId);
            if (imageIndex !== -1) {
                this.uploadedImages.splice(imageIndex, 1);
                
                // 如果删除的是主图片，设置第一张其他图片为主图片
                if (this.uploadedImage && this.uploadedImage.id === imageId) {
                    if (this.uploadedImages.length > 0) {
                        // 将第一张其他图片设为主图
                        this.uploadedImage = this.uploadedImages[0];
                        this.formData.attachment = this.uploadedImages[0].relative_path;
                        // 从其他图片列表中移除
                        this.uploadedImages.splice(0, 1);
                    } else {
                        this.uploadedImage = null;
                        this.formData.attachment = null;
                    }
                }
                
                this.formData.attachments = this.uploadedImages;
                this.updateImagePreview();
            }
        } else {
            // 删除所有图片
            this.uploadedImage = null;
            this.uploadedImages = [];
            this.formData.attachment = null;
            this.formData.attachments = [];
            this.updateImagePreview();
        }
    }


    bindAllEvents() {
        // 绑定表单提交事件
        const form = this.shadowRoot.querySelector('form');
        
        if (form) {
            // 先移除之前的事件监听器（如果有的话）
            form.removeEventListener('submit', this.handleFormSubmit);
            
            // 绑定新的事件监听器
            this.handleFormSubmit = this.createSubmitHandler(this.handleSubmit);
            form.addEventListener('submit', this.handleFormSubmit);
        } else {
            console.error('Form not found for event binding');
        }

        // 图片上传使用原生的onchange事件，无需复杂绑定
    }

    async handleSubmit() {
        // 立即检查提交锁，防止重复提交
        if (!this.canSubmit()) {
            return;
        }

        // 立即设置提交锁和loading状态，防止重复点击
        this.submitting = true;
        this.updateLoadingState(true);

        // 再次检查登录状态
        if (!UserManager.isLoggedIn()) {
            this.showError('请先登录后再发表文章');
            this.clearDraftOnSessionInvalid();
            this.resetSubmitState();
            return;
        }

        // 验证必填字段
        if (!this.formData.name.trim()) {
            this.showError('文章标题不能为空');
            this.resetSubmitState();
            return;
        }

        if (this.formData.name.length > 50) {
            this.showError('文章标题不能超过50个字符');
            this.resetSubmitState();
            return;
        }

        if (!this.formData.comment.trim()) {
            this.showError('文章内容不能为空');
            this.resetSubmitState();
            return;
        }

        // 检查文章内容大小（128KB = 131072字节）
        const contentSize = new Blob([this.formData.comment]).size;
        if (contentSize > 131072) {
            this.showError('文章内容不能超过128KB');
            this.resetSubmitState();
            return;
        }

        try {
            // 使用token-manager获取有效的访问令牌
            const tokenManager = window.tokenManager;
            if (!tokenManager) {
                this.showError('Token管理器未初始化，请刷新页面重试');
                this.resetSubmitState();
                return;
            }

            const token = await tokenManager.getValidAccessToken();
            if (!token) {
                this.showError('登录状态已过期，请重新登录');
                this.clearDraftOnSessionInvalid();
                this.resetSubmitState();
                return;
            }

            const headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            };

            // 准备提交数据
            const submitData = {
                name: this.formData.name,
                comment: this.formData.comment,
                itemtype: this.formData.itemtype,
                folderid: this.formData.folderid,
                status: this.formData.status,
                allowpost: this.formData.allowpost,
                attachment: this.formData.attachment,
                attachments: this.formData.attachments,
                projectid: this.projectId,
                userid: UserManager.getCurrentUserId(),
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
                this.clearDraftCache();
                this._draftAutoSaver?.stop();
                this.showSuccess(`文章发表成功！文章ID: ${result.id}`);
                setTimeout(() => {
                    window.location.href = `/blog/${this.projectId}`;
                }, 2000);
                // 成功后不重置状态，保持按钮禁用状态
                return; // 直接返回，不执行finally块
            } else {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { detail: '无法解析错误响应' };
                }
                
                let errorMessage = '发表文章失败';
                
                if (response.status === 401) {
                    errorMessage = '登录状态已过期，请重新登录';
                    this.clearDraftOnSessionInvalid();
                    // 清除本地存储的认证信息
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user_info');
                } else if (response.status === 403) {
                    errorMessage = '没有权限在此项目中创建文章';
                } else if (response.status === 400) {
                    errorMessage = `请求参数错误: ${errorData.detail || '未知错误'}`;
                } else if (response.status === 404) {
                    errorMessage = `项目不存在: ${errorData.detail || '项目ID无效'}`;
                } else if (response.status === 500) {
                    errorMessage = `服务器内部错误: ${errorData.detail || '请联系管理员'}`;
                } else {
                    errorMessage = `请求失败 (${response.status}): ${errorData.detail || '未知错误'}`;
                }
                
                this.showError(errorMessage);
                this.resetSubmitState();
            }
        } catch (error) {
            this.showError('网络错误，请稍后重试');
            this.resetSubmitState();
        }
    }

    resetSubmitState() {
        this.submitting = false;
        this.loading = false;
        this.updateButtonState();
    }

    async handleCancel() {
        // 删除所有上传的临时图片
        await this.cleanupTempImages();
        
        // 返回上一页
        window.history.back();
    }

    async cleanupTempImages() {
        // 删除主图的临时文件
        if (this.uploadedImage && this.uploadedImage.is_temp) {
            try {
                await fetch(`/api/temp-upload/${this.uploadedImage.filename}`, {
                    method: 'DELETE'
                });
            } catch (error) {
                // 忽略删除失败的错误
            }
        }

        // 删除其他图片的临时文件
        for (const image of this.uploadedImages) {
            if (image.is_temp) {
                try {
                    await fetch(`/api/temp-upload/${image.filename}`, {
                        method: 'DELETE'
                    });
                } catch (error) {
                    // 忽略删除失败的错误
                }
            }
        }

        // 清空图片数据
        this.uploadedImage = null;
        this.uploadedImages = [];
        this.formData.attachment = null;
        this.formData.attachments = [];
    }

    updateButtonState() {
        this.updateSubmitButtonState('发表中...', '发表文章');
    }

    updateLoadingState(loading) {
        this.loading = loading;
        this.updateButtonState();
    }

    updateImagePreview() {
        const imageContainer = this.shadowRoot.querySelector('.image-upload-container');
        if (imageContainer) {
            const existingPreview = imageContainer.querySelector('.uploaded-image-preview');
            if (existingPreview) {
                existingPreview.remove();
            }
            
            if (this.uploadedImages.length > 0 || this.uploadedImage) {
                const previewHtml = `
                    <div class="uploaded-image-preview">
                        ${this.uploadedImage ? `
                            <div class="main-image-preview">
                                <img src="${this.uploadedImage.url}" alt="主图片" class="preview-image">
                                <div class="image-info">
                                    <span class="image-name">${this.uploadedImage.original_name} (主图)</span>
                                    <span class="image-size">${(this.uploadedImage.size / 1024).toFixed(1)}KB</span>
                                </div>
                                <button type="button" class="btn-remove-image" onclick="this.getRootNode().host.removeImage('${this.uploadedImage.id}')" title="删除主图">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                </button>
                            </div>
                        ` : ''}
                        ${this.uploadedImages.length > 0 ? `
                            <div class="multiple-images-preview">
                                <h4>其他图片 (${this.uploadedImages.length}张)</h4>
                                <div class="images-list">
                                    ${this.uploadedImages.map(img => `
                                        <div class="image-item">
                                            <img src="${img.url}" alt="${img.original_name}" class="thumb-image">
                                            <div class="image-info">
                                                <span class="image-name">${img.original_name}</span>
                                                <span class="image-size">${(img.size / 1024).toFixed(1)}KB</span>
                                            </div>
                                            <button type="button" class="btn-remove-image" onclick="this.getRootNode().host.removeImage('${img.id}')" title="删除图片">×</button>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
                imageContainer.insertAdjacentHTML('beforeend', previewHtml);
            }
        }
    }

    updateCategories() {
        const categorySelect = this.shadowRoot.querySelector('#folderid');
        if (categorySelect) {
            // 保存当前选中的值
            const currentValue = categorySelect.value;
            
            // 更新选项
            const optionsHtml = `
                <option value="">未分类</option>
                ${this.categories.map(category => `
                    <option value="${category.id}" ${this.formData.folderid === category.id ? 'selected' : ''}>
                        ${category.name.trim()} (${category.count})
                    </option>
                `).join('')}
            `;
            categorySelect.innerHTML = optionsHtml;
            
            // 恢复选中的值
            if (currentValue) {
                categorySelect.value = currentValue;
            }
        }
    }


    showLoginRequired() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }

                @import url('/static/css/common-components.css');
                
                .card {
                    background: var(--white);
                    border-radius: var(--card-radius, var(--radius-lg));
                    box-shadow: var(--card-shadow, var(--shadow-sm));
                    border: 1px solid var(--card-border, var(--gray-200));
                    overflow: hidden;
                    text-align: center;
                    padding: var(--spacing-8);
                }
                
                .login-required-icon {
                    width: 64px;
                    height: 64px;
                    margin: 0 auto var(--spacing-4);
                    color: var(--gray-400);
                }
                
                .login-required-title {
                    font-size: var(--font-size-xl);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-3);
                }
                
                .login-required-message {
                    color: var(--gray-600);
                    margin-bottom: var(--spacing-6);
                    line-height: 1.6;
                }
            </style>

            <div class="card">
                <svg class="login-required-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
                <h2 class="login-required-title">需要登录</h2>
                <p class="login-required-message">
                    发表文章需要先登录您的账户。<br>
                    请点击下方按钮登录后重试。
                </p>
                <button class="btn btn-primary" onclick="this.showLoginModal()">
                    立即登录
                </button>
            </div>
        `;
    }

    showLoginModal() {
        // 直接调用header组件的showLoginModal方法
        const headerComponent = document.querySelector('header-component');
        if (headerComponent && headerComponent.showLoginModal) {
            headerComponent.showLoginModal(window.location.href);
        } else {
            // 如果header组件不可用，触发事件
            const loginEvent = new CustomEvent('showLoginModal', {
                bubbles: true,
                detail: { returnUrl: window.location.href }
            });
            document.dispatchEvent(loginEvent);
        }
    }


    showError(message) {
        // 显示错误消息
        const errorElement = this.shadowRoot.querySelector('.error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
            // 滚动到错误消息
            errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        // 隐藏成功消息
        const successElement = this.shadowRoot.querySelector('.success-message');
        if (successElement) {
            successElement.style.display = 'none';
        }
    }

    showSuccess(message) {
        // 显示成功消息
        const successElement = this.shadowRoot.querySelector('.success-message');
        if (successElement) {
            successElement.textContent = message;
            successElement.style.display = 'block';
            // 滚动到成功消息
            successElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        // 隐藏错误消息
        const errorElement = this.shadowRoot.querySelector('.error-message');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');
                @import url('/static/css/form-components.css');

                :host {
                    display: block;
                    font-family: var(--font-family);
                }
                
                .card {
                    background: var(--white);
                    border-radius: var(--card-radius, var(--radius-lg));
                    box-shadow: var(--card-shadow, var(--shadow-sm));
                    border: 1px solid var(--card-border, var(--gray-200));
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
                
                /* 表单样式 */
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
                    box-sizing: border-box;
                }
                
                .form-input:focus,
                .form-textarea:focus,
                .form-select:focus {
                    outline: none;
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 3px var(--primary-color-10);
                }
                
                .form-textarea {
                    min-height: 200px;
                    resize: vertical;
                    font-family: inherit;
                }
                
                .form-textarea.large {
                    min-height: 400px;
                }

                .form-input.post-title-input {
                    font-size: var(--font-size-xl);
                    font-weight: 700;
                    line-height: 1.3;
                    color: var(--gray-900);
                }

                .form-textarea.post-content-input,
                .content-editor.post-content-input {
                    font-family: var(--font-family);
                    font-size: var(--font-size-base);
                    line-height: 1.8;
                    color: var(--gray-800);
                }
                
                .form-help {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    margin-top: var(--spacing-1);
                }

                .draft-cache-hint {
                    margin-bottom: var(--spacing-3);
                    padding: var(--spacing-2) var(--spacing-3);
                    font-size: var(--font-size-xs);
                    color: var(--gray-600);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-sm);
                    line-height: 1.4;
                }

                .draft-cache-hint[hidden] {
                    display: none;
                }
                
                .error-message,
                .success-message {
                    padding: var(--spacing-3) var(--spacing-4);
                    border-radius: var(--radius-md);
                    margin-bottom: var(--spacing-4);
                    font-size: var(--font-size-sm);
                    display: none;
                }
                
                .error-message {
                    background-color: #fef2f2;
                    color: var(--error-color);
                    border: 1px solid #fecaca;
                }
                
                .success-message {
                    background-color: #f0fdf4;
                    color: var(--success-color);
                    border: 1px solid #bbf7d0;
                }
                
                .form-label-container {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-2);
                }
                
                .preview-toggle {
                    display: flex;
                    gap: var(--spacing-2);
                }
                
                .content-container {
                    position: relative;
                }
                
                .content-editor {
                    width: 100%;
                    min-height: 400px;
                    resize: vertical;
                }
                
                .content-preview {
                    width: 100%;
                    min-height: 400px;
                    padding: var(--spacing-4);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    background: var(--white);
                    overflow-y: auto;
                }
                
                .markdown-content {
                    font-family: var(--font-family);
                    line-height: 1.8;
                    color: var(--gray-800);
                }
                
                .markdown-content h1,
                .markdown-content h2,
                .markdown-content h3,
                .markdown-content h4,
                .markdown-content h5,
                .markdown-content h6 {
                    margin-top: var(--spacing-6);
                    margin-bottom: var(--spacing-3);
                    font-weight: 600;
                    color: var(--gray-900);
                }
                
                .markdown-content h1 { font-size: var(--font-size-xl); }
                .markdown-content h2 { font-size: var(--font-size-lg); }
                .markdown-content h3 { font-size: var(--font-size-base); }
                
                .markdown-content p {
                    margin-bottom: var(--spacing-4);
                }
                
                .markdown-content code {
                    background: var(--gray-100);
                    padding: var(--spacing-1) var(--spacing-2);
                    border-radius: var(--radius-sm);
                    font-family: var(--font-family-mono);
                    font-size: var(--font-size-xs);
                }
                
                .markdown-content pre {
                    background: var(--gray-100);
                    padding: var(--spacing-4);
                    border-radius: var(--radius-md);
                    overflow-x: auto;
                    margin-bottom: var(--spacing-4);
                }
                
                .markdown-content pre code {
                    background: none;
                    padding: 0;
                }
                
                .markdown-content ul,
                .markdown-content ol {
                    margin-bottom: var(--spacing-4);
                    padding-left: var(--spacing-6);
                }
                
                .markdown-content li {
                    margin-bottom: var(--spacing-1);
                }
                
                .markdown-content blockquote {
                    border-left: 4px solid var(--primary-color);
                    padding-left: var(--spacing-4);
                    margin: var(--spacing-4) 0;
                    color: var(--gray-600);
                    font-style: italic;
                }
                
                .markdown-content table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: var(--spacing-4);
                }
                
                .markdown-content th,
                .markdown-content td {
                    padding: var(--spacing-2) var(--spacing-3);
                    border: 1px solid var(--gray-300);
                    text-align: left;
                }
                
                .markdown-content th {
                    background: var(--gray-50);
                    font-weight: 600;
                }
                
                .image-upload-container {
                    border: 2px dashed var(--gray-300);
                    border-radius: var(--radius-md);
                    padding: var(--spacing-6);
                    text-align: center;
                    transition: var(--transition-fast);
                    cursor: pointer;
                }
                
                .image-upload-container:hover {
                    border-color: var(--primary-color);
                    background: var(--gray-50);
                }
                
                .image-upload-container.dragover {
                    border-color: var(--primary-color);
                    background: var(--primary-color-10);
                }
                
                .image-upload-icon {
                    width: 48px;
                    height: 48px;
                    margin: 0 auto var(--spacing-3);
                    color: var(--gray-400);
                }
                
                .image-upload-text {
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                    margin-bottom: var(--spacing-2);
                }
                
                .image-upload-hint {
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                }
                
                .image-preview {
                    margin-top: var(--spacing-4);
                    text-align: center;
                }
                
                .image-preview img {
                    max-width: 100%;
                    max-height: 200px;
                    border-radius: var(--radius-md);
                    box-shadow: var(--shadow-sm);
                }
                
                .image-remove {
                    margin-top: var(--spacing-2);
                    padding: var(--spacing-2) var(--spacing-4);
                    background: var(--error-color);
                    color: var(--white);
                    border: none;
                    border-radius: var(--radius-sm);
                    cursor: pointer;
                    font-size: var(--font-size-xs);
                }
                
                .image-remove:hover {
                    background: #dc2626;
                }
                
                .form-actions {
                    display: flex;
                    gap: var(--spacing-3);
                    justify-content: flex-end;
                    margin-top: var(--spacing-6);
                    padding-top: var(--spacing-4);
                    border-top: 1px solid var(--gray-200);
                }
                
                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
                
                .loading-spinner {
                    width: 32px;
                    height: 32px;
                    border: 3px solid var(--gray-200);
                    border-top: 3px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto var(--spacing-4);
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
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
                    <div class="draft-cache-hint" hidden>草稿已经保存到本地缓存</div>
                    <div class="error-message"></div>
                    <div class="success-message"></div>
                    
                    <form>
                        <div class="form-group">
                            <label class="form-label required" for="name">文章标题</label>
                            <input 
                                type="text" 
                                id="name" 
                                class="form-input post-title-input" 
                                placeholder="请输入文章标题"
                                value="${this.formData.name}"
                                oninput="this.getRootNode().host.handleInputChange('name', this.value)"
                                onchange="this.getRootNode().host.handleInputChange('name', this.value)"
                                required
                            >
                            <div class="form-help">文章标题将显示在博客列表中，建议简洁明了（最多50个字符）</div>
                        </div>

                        <div class="form-group">
                            <div class="form-label-container">
                                <label class="form-label required" for="comment">文章内容</label>
                                <div class="preview-toggle">
                                    <button type="button" class="btn-preview btn-icon-only" id="previewToggleBtn" title="预览" aria-label="预览" onclick="this.getRootNode().host.togglePreview()">
                                        <span class="preview-icon">${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.preview) : '预览'}</span>
                                        <span class="edit-icon" style="display: none;">${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.edit) : '编辑'}</span>
                                    </button>
                                </div>
                            </div>
                            <div class="content-container">
                                <textarea 
                                    id="comment" 
                                    class="form-textarea large content-editor post-content-input" 
                                    placeholder="请输入文章内容..."
                                    oninput="this.getRootNode().host.handleInputChange('comment', this.value)"
                                    required
                                >${this.formData.comment}</textarea>
                                <div class="content-preview" style="display: none;">
                                    <div class="preview-content markdown-content"></div>
                                </div>
                            </div>
                            <div class="form-help">支持Markdown格式，包括标题、列表、代码块、表格、链接等（最多128KB）</div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="image-upload">上传图片</label>
                            <div class="image-upload-container">
                                <input 
                                    type="file" 
                                    id="image-upload" 
                                    name="UserFile"
                                    class="form-input"
                                    accept="image/jpeg,image/jpg,image/png,image/gif"
                                    onchange="this.getRootNode().host.handleImageUpload(this.files[0])"
                                >
                            </div>
                            <div class="form-help">支持jpg、png、gif格式，大小不超过1MB，最多上传10张图片。第一张图片将作为文章主图。</div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="folderid">文章分类</label>
                            <select 
                                id="folderid" 
                                class="form-select"
                                onchange="this.getRootNode().host.handleInputChange('folderid', this.value ? parseInt(this.value) : null)"
                            >
                                <option value="">未分类</option>
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
                            <button type="button" class="btn btn-secondary btn-icon-only" title="取消" aria-label="取消" onclick="this.getRootNode().host.handleCancel()">
                                ${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.close) : '取消'}
                            </button>
                            <button type="submit" class="btn btn-primary" ${!this.canSubmit() ? 'disabled' : ''}>
                                ${!this.canSubmit() ? `
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

        if (typeof MarkdownUtils !== 'undefined') {
            MarkdownUtils.ensureKatexStyles(this.shadowRoot);
        }
        
        // 立即绑定事件监听器（因为innerHTML会清除之前的事件）
        // 使用setTimeout确保DOM更新完成后再绑定事件
        setTimeout(() => {
            this.bindAllEvents();
        }, 0);
    }
}

customElements.define('create-post-form', CreatePostForm);
