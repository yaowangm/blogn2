/**
 * 文章评论卡片组件
 * 显示文章的评论列表
 */
class ArticleCommentsCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
        this.userMap = {};
        this.currentPage = 1;
        this.perPage = 10;
        this.pagination = null;
    }

    async connectedCallback() {
        // 从URL获取文章ID
        this.articleId = this.getArticleIdFromUrl();
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        // 加载文章数据
        await this.loadArticleData();
        
        // 渲染组件
        this.render();
        
        // 检查URL锚点，如果需要定位到特定评论
        this.checkAndScrollToComment();
    }

    /**
     * 从URL获取文章ID
     */
    getArticleIdFromUrl() {
        // 使用基类的统一方法
        return this.getArticleId();
    }

    /**
     * 加载文章数据
     */
    async loadArticleData() {
        try {
            // 获取认证token
            const token = localStorage.getItem('access_token');
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(`/api/articles/${this.articleId}?page=${this.currentPage}&per_page=${this.perPage}`, {
                headers: headers
            });
            if (response.ok) {
                this.articleData = await response.json();
                
                // 保存分页信息
                if (this.articleData.comments_pagination) {
                    this.pagination = this.articleData.comments_pagination;
                }
                
                // 如果有评论，获取每个评论的用户信息
                if (this.articleData.comments && this.articleData.comments.length > 0) {
                    await this.loadCommentUsers();
                }
            } else if (response.status === 404) {
                // 文章不存在，跳转到错误页面
                window.location.href = '/static/error.html';
                return;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.logError('Failed to load article data', error);
            // 加载失败，跳转到错误页面
            window.location.href = '/static/error.html';
        }
    }

    /**
     * 加载评论用户信息
     */
    async loadCommentUsers() {
        if (!this.articleData.comments) return;
        
        try {
            // 获取所有不重复的用户ID
            const userIds = [...new Set(this.articleData.comments
                .map(comment => comment.user_id)
                .filter(id => id))];
            
            // 批量获取用户信息
            const userPromises = userIds.map(async (userId) => {
                try {
                    const userResponse = await fetch(`/api/users/${userId}`);
                    if (userResponse.ok) {
                        return await userResponse.json();
                    }
                } catch (error) {
                    console.warn(`Failed to load user ${userId}:`, error);
                }
                return null;
            });
            
            const users = await Promise.all(userPromises);
            
            // 创建用户ID到用户信息的映射
            this.userMap = {};
            users.forEach(user => {
                if (user) {
                    this.userMap[user.id] = user;
                }
            });
        } catch (error) {
            console.warn('Failed to load comment users:', error);
            this.userMap = {};
        }
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.shadowRoot.innerHTML = `
                <div class="card article-comments-card">
                    <div class="card-body">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            `;
            return;
        }

        const { comments, comment_count } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-comments-card">
                <div class="card-header">
                    <h3>评论 (${comment_count || 0})</h3>
                </div>
                <div class="card-body">
                    ${this.renderComments(comments)}
                </div>
                ${this.renderPagination()}
            </div>
        `;

        this.addStyles();
        this.addEventListeners();
        this.setupPaginationCallback();
    }

    /**
     * 添加事件监听器
     */
    addEventListeners() {
        // 移除之前的事件监听器（如果存在）
        if (this.clickHandler) {
            this.shadowRoot.removeEventListener('click', this.clickHandler);
        }
        
        // 创建新的事件处理器
        this.clickHandler = (e) => {
            if (e.target.closest('.delete-comment-btn')) {
                const button = e.target.closest('.delete-comment-btn');
                const commentId = parseInt(button.dataset.commentId);
                if (commentId) {
                    this.deleteComment(commentId);
                }
            }
        };
        
        // 添加新的事件监听器
        this.shadowRoot.addEventListener('click', this.clickHandler);
    }

    /**
     * 检查当前用户是否有删除评论的权限
     */
    canDeleteComment(comment) {
        // 检查是否已登录
        const userInfo = localStorage.getItem('user_info');
        if (!userInfo) {
            return false;
        }
        
        try {
            const currentUser = JSON.parse(userInfo);
            const currentUserId = currentUser.id;
            const isAdmin = currentUser.state === 10;
            
            // 管理员可以删除任何评论
            if (isAdmin) {
                return true;
            }
            
            // 文章作者可以删除评论（需要检查文章作者）
            // 这里我们假设文章数据中包含了作者信息
            if (this.articleData && this.articleData.author) {
                const articleAuthorId = this.articleData.author.id;
                return articleAuthorId === currentUserId;
            }
            
            return false;
        } catch (error) {
            console.error('Error checking delete permission:', error);
            return false;
        }
    }

    /**
     * 删除评论
     */
    async deleteComment(commentId) {
        // 查找要删除的评论
        const comment = this.articleData.comments?.find(c => c.id === commentId);
        if (!comment) {
            this.showError('找不到要删除的评论');
            return;
        }
        
        // 获取评论内容的前10个字符
        const contentPreview = comment.content ? 
            (comment.content.length > 10 ? comment.content.substring(0, 10) + '...' : comment.content) : 
            '无内容';
        
        if (!confirm(`确定要删除这条评论吗？\n\n评论内容预览：${contentPreview}\n\n此操作不可撤销。`)) {
            return;
        }
        
        try {
            // 获取认证token
            const token = localStorage.getItem('access_token');
            const headers = { 'Content-Type': 'application/json' };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(`/api/articles/${this.articleId}/comments/${commentId}`, {
                method: 'DELETE',
                headers: headers
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess('评论删除成功！');
                
                // 刷新评论列表
                await this.refreshComments();
            } else {
                const error = await response.json();
                throw new Error(error.detail || '删除失败');
            }
        } catch (error) {
            console.error('Failed to delete comment:', error);
            this.showError(`删除评论失败: ${error.message}`);
        }
    }

    /**
     * 刷新评论列表
     */
    async refreshComments() {
        try {
            // 重新加载文章数据（包含评论）
            await this.loadArticleData();
            
            // 重新渲染组件
            this.render();
            
            // 重新加载用户信息
            await this.loadCommentUsers();
            
            // 重新渲染以显示用户信息
            this.render();
        } catch (error) {
            console.error('Failed to refresh comments:', error);
            this.showError('刷新评论失败');
        }
    }

    /**
     * 检查URL锚点并滚动到对应评论
     */
    checkAndScrollToComment() {
        // 获取URL中的锚点
        const hash = window.location.hash;
        if (!hash) return;
        
        // 检查锚点格式是否为 #post{commentId}
        const match = hash.match(/^#post(\d+)$/);
        if (!match) return;
        
        const commentId = match[1];
        
        // 等待DOM渲染完成后再滚动
        setTimeout(() => {
            // 查找对应的评论元素
            const commentElement = this.shadowRoot.querySelector(`#post${commentId}`);
            if (commentElement) {
                // 滚动到评论位置
                commentElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                // 添加高亮效果
                commentElement.style.backgroundColor = 'var(--primary-color)';
                commentElement.style.color = 'var(--white)';
                
                // 3秒后恢复原样式
                setTimeout(() => {
                    commentElement.style.backgroundColor = '';
                    commentElement.style.color = '';
                }, 3000);
            }
        }, 500); // 增加延迟，确保评论完全渲染
    }

    /**
     * 渲染评论列表
     */
    renderComments(comments) {
        if (!comments || comments.length === 0) {
            return `
                <div class="no-comments">
                    <p>暂无评论，成为第一个评论者吧！</p>
                </div>
            `;
        }

        return `
            <div class="comments-list">
                ${comments.map(comment => this.renderComment(comment)).join('')}
            </div>
        `;
    }

    /**
     * 渲染单个评论
     */
    renderComment(comment) {
        const { id, content, user_id, post_time, reply_count } = comment;
        
        // 获取用户名和博客ID，如果没有则显示用户ID或匿名
        let userName = '匿名';
        let blogId = null;
        let userAvatar = null;
        
        // 检查当前用户是否有删除权限
        const canDelete = this.canDeleteComment(comment);
        
        if (user_id) {
            if (this.userMap && this.userMap[user_id]) {
                const user = this.userMap[user_id];
                userName = user.name || `用户${user_id}`;
                blogId = user.projectid || null;
                
                // 构建头像路径
                if (user.id) {
                    const prefix = Math.floor(user.id / 10000) + 1;
                    userAvatar = `/avatar/${prefix}/${user.id}.jpg`;
                }
            } else {
                userName = `用户${user_id}`;
            }
        }
        
        return `
            <div class="comment-item" id="post${id}" data-comment-id="${id}">
                <div class="comment-avatar">
                    ${blogId ? `
                        <a href="/blog/${blogId}" class="avatar-link" title="查看博客" target="_blank" rel="noopener noreferrer">
                            <div class="user-avatar">
                                ${userAvatar ? 
                                    `<img src="${userAvatar}" alt="${this.escapeHtml(userName)}" 
                                          onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                                          onload="this.style.display='block'; this.nextElementSibling.style.display='none';"
                                          style="display: block;">` : 
                                    ''
                                }
                                <span style="display: ${userAvatar ? 'none' : 'flex'}; color: var(--gray-600);">${userName.charAt(0).toUpperCase()}</span>
                            </div>
                        </a>
                    ` : `
                        <div class="user-avatar">
                            <span style="color: var(--gray-600);">?</span>
                        </div>
                    `}
                </div>
                
                <div class="comment-content-wrapper">
                    <div class="comment-header">
                        <div class="comment-user">
                            ${blogId ? `
                                <a href="/blog/${blogId}" class="user-link" title="查看博客" target="_blank" rel="noopener noreferrer">
                                    <span class="user-name">${this.escapeHtml(userName)}</span>
                                </a>
                            ` : `
                                <span class="user-name">${this.escapeHtml(userName)}</span>
                            `}
                        </div>
                        <div class="comment-actions">
                            <div class="comment-time">
                                ${this.formatDate(post_time)}
                            </div>
                            ${canDelete ? `
                                <button class="delete-comment-btn" 
                                        data-comment-id="${id}" 
                                        title="删除评论">
                                    <i class="fas fa-trash"></i>
                                    删除
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="comment-content">
                        ${this.processTextWithLinks(content || '')}
                    </div>
                    
                    ${reply_count > 0 ? `
                        <div class="comment-replies">
                            <span class="reply-count">${reply_count} 条回复</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * HTML转义并处理换行
     */
    escapeHtml(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        
        // 先转义HTML特殊字符
        const escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
        
        // 将换行符转换为HTML换行标签
        return escaped.replace(/\r?\n/g, '<br>');
    }

    /**
     * 验证URL是否安全有效
     * @param {string} url - 要验证的URL
     * @returns {boolean} - 是否安全有效
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
     * 处理文本中的链接，安全地转换为可点击的链接
     */
    processTextWithLinks(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }

        // 更严格的URL正则表达式，只匹配基本的http/https链接
        const urlRegex = /(https?:\/\/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+)/gi;
        
        return text.replace(urlRegex, (url) => {
            // 使用严格的URL验证
            if (this.isValidUrl(url)) {
                const safeUrl = this.escapeHtml(url);
                const displayUrl = this.escapeHtml(url);
                return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="auto-link">${displayUrl}</a>`;
            }
            // 如果URL不安全，只转义显示
            return this.escapeHtml(url);
        });
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="card article-comments-card">
                <div class="card-body">
                    <div class="error-message">${message}</div>
                </div>
            </div>
        `;
        this.addStyles();
    }

    showSuccess(message) {
        // 创建临时成功提示
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #10b981;
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease-out;
        `;
        successDiv.textContent = message;
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(successDiv);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
            if (style.parentNode) {
                style.parentNode.removeChild(style);
            }
        }, 3000);
    }

    /**
     * 渲染分页导航
     */
    renderPagination() {
        if (!this.pagination || this.pagination.total_pages <= 1) {
            return '';
        }

        return `
            <div class="pagination-container">
                <navigation-card mode="pagination" pagination='${JSON.stringify(this.pagination)}'></navigation-card>
            </div>
        `;
    }

    /**
     * 切换到指定页面
     */
    async goToPage(page) {
        if (page < 1 || page > this.pagination.total_pages) {
            return;
        }
        
        this.currentPage = page;
        await this.loadArticleData();
        this.render();
        this.checkAndScrollToComment();
    }

    /**
     * 设置分页导航回调
     */
    setupPaginationCallback() {
        const navigationCard = this.shadowRoot.querySelector('navigation-card');
        if (navigationCard && this.pagination) {
            // 为评论分页添加item_type
            const paginationData = {
                ...this.pagination,
                item_type: '条评论'
            };
            navigationCard.setPagination(paginationData, (page) => {
                this.goToPage(page);
            });
        }
    }

    /**
     * 添加样式
     */
    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                @import url('/static/css/common-components.css');
                
                .card-header {
                    padding: var(--spacing-4) var(--spacing-6);
                    border-bottom: 1px solid var(--gray-200);
                    background-color: var(--gray-50);
                }
                
                .card-header h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-800);
                    margin: 0;
                }
                
                .comments-list {
                    max-height: 600px;
                    overflow-y: auto;
                    scroll-behavior: smooth;
                }
                
                .comment-item {
                    display: flex;
                    gap: var(--spacing-4);
                    padding: var(--spacing-4);
                    border-bottom: 1px solid var(--gray-100);
                    transition: background-color var(--transition-fast);
                }
                
                .comment-item:last-child {
                    border-bottom: none;
                }
                
                .comment-item:hover {
                    background-color: var(--gray-50);
                }

                .comment-avatar {
                    flex-shrink: 0;
                }

                .avatar-link {
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }

                .user-avatar {
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-600);
                    border: 2px solid var(--gray-200);
                    overflow: hidden;
                }

                .user-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                .comment-content-wrapper {
                    flex: 1;
                    min-width: 0;
                }
                
                .comment-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--spacing-3);
                }
                
                .comment-user .user-name {
                    font-weight: 600;
                    color: var(--primary-color);
                    font-size: var(--font-size-sm);
                }

                .user-link {
                    text-decoration: none;
                    color: inherit;
                    transition: color var(--transition-fast);
                }

                .user-link:hover .user-name {
                    color: var(--primary-hover);
                    text-decoration: underline;
                }
                
                .comment-actions {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                
                .comment-time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                }
                
                .delete-comment-btn {
                    padding: var(--spacing-2) var(--spacing-3);
                    font-size: var(--font-size-sm);
                    border: 1px solid var(--red-300);
                    color: var(--red-600);
                    background-color: transparent;
                    border-radius: var(--border-radius-md);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    font-weight: 500;
                    min-height: 32px;
                }
                
                .delete-comment-btn:hover {
                    background-color: var(--red-50);
                    border-color: var(--red-400);
                    color: var(--red-700);
                }
                
                .delete-comment-btn:active {
                    background-color: var(--red-100);
                    transform: translateY(1px);
                }
                
                .comment-content {
                    line-height: 1.6;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-3);
                    word-wrap: break-word;
                    white-space: pre-line;
                    overflow-wrap: break-word;
                }

                .auto-link {
                    color: var(--primary-color);
                    text-decoration: none;
                    word-break: break-all;
                    transition: color var(--transition-fast);
                }

                .auto-link:hover {
                    color: var(--primary-hover);
                    text-decoration: underline;
                }
                
                .comment-replies {
                    display: flex;
                    justify-content: flex-end;
                }
                
                .reply-count {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    cursor: pointer;
                    transition: color var(--transition-fast);
                }
                
                .reply-count:hover {
                    color: var(--primary-color);
                }
                
                .no-comments {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }
                
                .no-comments p {
                    margin: 0;
                    font-style: italic;
                }
                
                .loading {
                    text-align: center;
                    color: var(--gray-500);
                    padding: var(--spacing-8);
                }
                
                .error-message {
                    text-align: center;
                    color: var(--error-color);
                    padding: var(--spacing-8);
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('article-comments-card', ArticleCommentsCard);
