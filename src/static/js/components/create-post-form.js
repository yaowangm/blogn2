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
        this.submitting = false; // 添加提交锁
        this.formData = {
            name: '',
            comment: '',
            itemtype: 1, // 默认为文章类型
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
    }

    async connectedCallback() {
        this.projectId = this.getProjectIdFromUrl();
        
        // 检查用户登录状态
        const isLoggedIn = this.checkLoginStatus();
        
        if (!isLoggedIn) {
            this.showLoginRequired();
            return;
        }
        
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
        const previewText = this.shadowRoot.querySelector('.preview-text');
        const editText = this.shadowRoot.querySelector('.edit-text');
        
        if (this.previewMode) {
            // 切换到预览模式
            editor.style.display = 'none';
            preview.style.display = 'block';
            previewText.style.display = 'none';
            editText.style.display = 'inline';
            this.updatePreview();
        } else {
            // 切换到编辑模式
            editor.style.display = 'block';
            preview.style.display = 'none';
            previewText.style.display = 'inline';
            editText.style.display = 'none';
        }
    }

    /**
     * 更新预览内容
     */
    updatePreview() {
        const previewContent = this.shadowRoot.querySelector('.preview-content');
        const content = this.formData.comment || '';
        
        if (!previewContent) {
            console.error('preview-content element not found!');
            return;
        }
        
        if (!content.trim()) {
            previewContent.innerHTML = '<p class="no-content">暂无内容</p>';
            return;
        }
        
        // 检查marked.js是否可用
        if (typeof marked === 'undefined' && typeof window.marked === 'undefined') {
            console.error('marked.js is not available');
            previewContent.innerHTML = '<p style="color: red;">错误：Markdown解析库未加载，请刷新页面重试</p>';
            return;
        }
        
        try {
            // 使用marked.js解析Markdown，优先使用全局的marked对象
            const markedParser = typeof marked !== 'undefined' ? marked : window.marked;
            
            // 配置marked.js选项
            const options = {
                breaks: true,  // 支持换行符
                gfm: true,     // 启用GitHub风格的Markdown
                pedantic: false
            };
            
            const html = markedParser.parse(content, options);
            
            // 对解析后的HTML进行安全过滤
            const safeHtml = this.sanitizeHtml(html);
            
            previewContent.innerHTML = safeHtml;
        } catch (error) {
            console.error('Markdown parsing failed in preview', error);
            this.logError('Markdown parsing failed in preview', error);
            // 如果Markdown解析失败，显示原始文本
            previewContent.innerHTML = `<pre>${this.escapeHtml(content)}</pre>`;
        }
    }


    /**
     * 验证URL是否安全
     */
    isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            
            // 只允许http和https协议
            if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
                return false;
            }
            
            // 检查域名是否包含危险字符
            const hostname = urlObj.hostname;
            if (!hostname || /[<>\"'&]/.test(hostname)) {
                return false;
            }
            
            // 检查端口号是否在安全范围内
            if (urlObj.port) {
                const port = parseInt(urlObj.port);
                if (port < 1 || port > 65535) {
                    return false;
                }
            }
            
            // 检查URL长度是否合理
            if (url.length > 2048) {
                return false;
            }
            
            // 检查是否包含可疑的JavaScript代码
            if (/javascript:|data:|vbscript:|file:/i.test(url)) {
                return false;
            }
            
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * 验证图片src是否安全
     */
    isValidImageSrc(src) {
        if (!src || typeof src !== 'string') {
            return false;
        }

        // 允许相对路径和绝对路径
        if (src.startsWith('/') || src.startsWith('./') || src.startsWith('../')) {
            return true;
        }

        // 允许http/https链接
        if (src.startsWith('http://') || src.startsWith('https://')) {
            try {
                const url = new URL(src);
                return url.protocol === 'http:' || url.protocol === 'https:';
            } catch {
                return false;
            }
        }

        // 允许data URL（base64图片）
        if (src.startsWith('data:image/')) {
            return true;
        }

        return false;
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
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
            this.handleFormSubmit = (event) => {
                event.preventDefault();
                
                // 防止重复提交：检查提交锁和loading状态
                if (this.submitting || this.loading) {
                    return;
                }
                
                this.handleSubmit();
            };
            form.addEventListener('submit', this.handleFormSubmit);
        } else {
            console.error('Form not found for event binding');
        }

        // 图片上传使用原生的onchange事件，无需复杂绑定
    }

    async handleSubmit() {
        // 立即检查提交锁，防止重复提交
        if (this.submitting || this.loading) {
            return;
        }

        // 立即设置提交锁和loading状态，防止重复点击
        this.submitting = true;
        this.updateLoadingState(true);

        // 再次检查登录状态
        if (!this.checkLoginStatus()) {
            this.showError('请先登录后再发表文章');
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
                return;
            }

            const token = await tokenManager.getValidAccessToken();
            if (!token) {
                this.showError('登录状态已过期，请重新登录');
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
        const submitBtn = this.shadowRoot.querySelector('button[type="submit"]');
        
        if (submitBtn) {
            if (this.loading || this.submitting) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <div class="loading">
                        <div class="loading-spinner"></div>
                        发表中...
                    </div>
                `;
            } else {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '发表文章';
            }
        }
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

    checkLoginStatus() {
        const token = localStorage.getItem('access_token');
        const userInfo = localStorage.getItem('user_info');
        
        return !!(token && userInfo);
    }

    showLoginRequired() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: var(--font-family);
                }
                
                @import url('/static/css/common-components.css');
                @import url('/static/css/components.css');
                
                .card {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--gray-200);
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
                
                .btn-primary:hover {
                    background-color: var(--primary-hover);
                    border-color: var(--primary-hover);
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
                :host {
                    display: block;
                    font-family: var(--font-family);
                }
                
                @import url('/static/css/common-components.css');
                @import url('/static/css/components.css');
                
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

                /* 预览功能样式 */
                .form-label-container {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-2);
                }

                .preview-toggle {
                    display: flex;
                    align-items: center;
                }

                .btn-preview {
                    display: inline-flex;
                    align-items: center;
                    padding: var(--spacing-2) var(--spacing-3);
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    color: var(--primary-color);
                    background-color: var(--white);
                    border: 1px solid var(--primary-color);
                    border-radius: var(--radius-sm);
                    cursor: pointer;
                    transition: var(--transition-fast);
                }

                .btn-preview:hover {
                    background-color: var(--primary-color);
                    color: var(--white);
                }

                .content-container {
                    position: relative;
                }

                .content-preview {
                    min-height: 400px;
                    padding: var(--spacing-4);
                    border: 1px solid var(--gray-300);
                    border-radius: var(--radius-md);
                    background-color: var(--white);
                    font-family: inherit;
                    line-height: 1.8;
                    color: var(--gray-800);
                }

                .preview-content {
                    min-height: 350px;
                }

                /* 确保预览内容使用Markdown样式 */
                .preview-content.markdown-content {
                    line-height: 1.6;
                    color: var(--gray-800);
                }

                .preview-content.markdown-content h1,
                .preview-content.markdown-content h2,
                .preview-content.markdown-content h3,
                .preview-content.markdown-content h4,
                .preview-content.markdown-content h5,
                .preview-content.markdown-content h6 {
                    margin: var(--spacing-6) 0 var(--spacing-4) 0;
                    font-weight: 600;
                    line-height: 1.3;
                    color: var(--gray-900);
                }

                .preview-content.markdown-content h1 {
                    font-size: 1.875rem;
                    border-bottom: 2px solid var(--gray-200);
                    padding-bottom: var(--spacing-2);
                }

                .preview-content.markdown-content h2 {
                    font-size: 1.5rem;
                    border-bottom: 1px solid var(--gray-200);
                    padding-bottom: var(--spacing-1);
                }

                .preview-content.markdown-content h3 {
                    font-size: 1.25rem;
                }

                .preview-content.markdown-content h4 {
                    font-size: 1.125rem;
                }

                .preview-content.markdown-content h5 {
                    font-size: 1rem;
                }

                .preview-content.markdown-content h6 {
                    font-size: 0.875rem;
                    color: var(--gray-600);
                }

                .preview-content.markdown-content p {
                    margin: var(--spacing-4) 0;
                }

                .preview-content.markdown-content ul,
                .preview-content.markdown-content ol {
                    margin: var(--spacing-4) 0;
                    padding-left: var(--spacing-6);
                }

                .preview-content.markdown-content li {
                    margin: var(--spacing-2) 0;
                }

                .preview-content.markdown-content blockquote {
                    margin: var(--spacing-4) 0;
                    padding: var(--spacing-4);
                    border-left: 4px solid var(--gray-300);
                    background-color: var(--gray-50);
                    color: var(--gray-700);
                    font-style: italic;
                }

                .preview-content.markdown-content blockquote p {
                    margin-bottom: 0;
                }

                .preview-content.markdown-content code {
                    background-color: var(--gray-100);
                    color: var(--gray-800);
                    padding: 2px 4px;
                    border-radius: var(--radius-sm);
                    font-family: 'Consolas', 'Monaco', 'Menlo', 'Ubuntu Mono', 'Courier New', monospace;
                    font-size: 0.9em;
                }

                .preview-content.markdown-content pre {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    padding: var(--spacing-4);
                    border-radius: var(--radius-md);
                    overflow-x: auto;
                    margin: var(--spacing-4) 0;
                    font-family: 'Consolas', 'Monaco', 'Menlo', 'Ubuntu Mono', 'Courier New', monospace;
                    font-size: 0.9em;
                    line-height: 1.5;
                }

                .preview-content.markdown-content pre code {
                    background-color: transparent;
                    color: inherit;
                    padding: 0;
                    border-radius: 0;
                    font-family: inherit;
                }

                .preview-content.markdown-content table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: var(--spacing-4) 0;
                }

                .preview-content.markdown-content th,
                .preview-content.markdown-content td {
                    border: 1px solid var(--gray-300);
                    padding: var(--spacing-3);
                    text-align: left;
                }

                .preview-content.markdown-content th {
                    background-color: var(--gray-100);
                    font-weight: 600;
                }

                .preview-content.markdown-content a {
                    color: var(--primary-600);
                    text-decoration: none;
                }

                .preview-content.markdown-content a:hover {
                    color: var(--primary-700);
                    text-decoration: underline;
                }

                .preview-content.markdown-content img {
                    max-width: 100%;
                    height: auto;
                    border-radius: var(--radius-md);
                    margin: var(--spacing-4) 0;
                }

                .preview-content.markdown-content hr {
                    border: none;
                    height: 1px;
                    background-color: var(--gray-300);
                    margin: var(--spacing-6) 0;
                }


                .preview-content .no-content {
                    color: var(--gray-500);
                    font-style: italic;
                    text-align: center;
                    padding: var(--spacing-8);
                }
                
                .image-upload-container {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-3);
                }
                
                .uploaded-image-preview {
                    position: relative;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                }
                
                .preview-image {
                    width: 60px;
                    height: 60px;
                    object-fit: cover;
                    border-radius: var(--radius-sm);
                    border: 1px solid var(--gray-200);
                }
                
                .image-info {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-1);
                }
                
                .image-name {
                    font-size: var(--font-size-sm);
                    font-weight: 500;
                    color: var(--gray-700);
                    word-break: break-all;
                }
                
                .image-size {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }
                
                .btn-remove-image {
                    position: absolute !important;
                    top: 8px !important;
                    right: 8px !important;
                    width: 24px !important;
                    height: 24px !important;
                    border: none !important;
                    background: #dc2626 !important;
                    color: white !important;
                    border-radius: 50% !important;
                    cursor: pointer !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    transition: all 0.2s ease !important;
                    z-index: 10 !important;
                    font-size: 12px !important;
                    font-weight: bold !important;
                }
                
                .btn-remove-image:hover {
                    background: #b91c1c !important;
                    transform: scale(1.1) !important;
                }
                
                .main-image-preview {
                    position: relative;
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    padding: var(--spacing-3);
                    border: 2px solid var(--primary-color);
                    border-radius: var(--radius-md);
                    background: var(--primary-50);
                    margin-bottom: var(--spacing-3);
                }
                
                .multiple-images-preview {
                    margin-top: var(--spacing-3);
                }
                
                .multiple-images-preview h4 {
                    font-size: var(--font-size-sm);
                    font-weight: 600;
                    color: var(--gray-700);
                    margin: 0 0 var(--spacing-2) 0;
                }
                
                .images-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                    gap: var(--spacing-2);
                }
                
                .image-item {
                    position: relative;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: var(--spacing-2);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    background: var(--white);
                    transition: var(--transition-fast);
                }
                
                .image-item:hover {
                    border-color: var(--gray-300);
                    box-shadow: var(--shadow-sm);
                }
                
                .thumb-image {
                    width: 60px;
                    height: 60px;
                    object-fit: cover;
                    border-radius: var(--radius-sm);
                    border: 1px solid var(--gray-200);
                    margin-bottom: var(--spacing-1);
                }
                
                .image-item .image-info {
                    text-align: center;
                    width: 100%;
                }
                
                .image-item .image-name {
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    color: var(--gray-700);
                    word-break: break-all;
                    display: block;
                    margin-bottom: var(--spacing-1);
                }
                
                .image-item .image-size {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    display: block;
                }
                
                .image-item .btn-remove-image {
                    position: absolute !important;
                    top: 4px !important;
                    right: 4px !important;
                    width: 20px !important;
                    height: 20px !important;
                    font-size: 12px !important;
                    padding: 0 !important;
                    z-index: 10 !important;
                    background: #dc2626 !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 50% !important;
                    cursor: pointer !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    font-weight: bold !important;
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
                            <div class="form-help">文章标题将显示在博客列表中，建议简洁明了（最多50个字符）</div>
                        </div>

                        <div class="form-group">
                            <div class="form-label-container">
                                <label class="form-label required" for="comment">文章内容</label>
                                <div class="preview-toggle">
                                    <button type="button" class="btn-preview" onclick="this.getRootNode().host.togglePreview()">
                                        <span class="preview-text">预览</span>
                                        <span class="edit-text" style="display: none;">编辑</span>
                                    </button>
                                </div>
                            </div>
                            <div class="content-container">
                                <textarea 
                                    id="comment" 
                                    class="form-textarea large content-editor" 
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
                            <button type="button" class="btn btn-secondary" onclick="this.getRootNode().host.handleCancel()">
                                取消
                            </button>
                            <button type="submit" class="btn btn-primary" ${(this.loading || this.submitting) ? 'disabled' : ''}>
                                ${(this.loading || this.submitting) ? `
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
        
        // 立即绑定事件监听器（因为innerHTML会清除之前的事件）
        // 使用setTimeout确保DOM更新完成后再绑定事件
        setTimeout(() => {
            this.bindAllEvents();
        }, 0);
    }
}

customElements.define('create-post-form', CreatePostForm);
