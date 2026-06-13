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

    disconnectedCallback() {
        this._detachCommentScrollCorrection();
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
            const headers = UserManager.createHeaders();

            const response = await fetch(
                `/api/articles/${this.articleId}/comments?page=${this.currentPage}&limit=${this.perPage}`,
                { headers }
            );
            if (response.ok) {
                const data = await response.json();
                this.articleData = {
                    comments: data.comments || [],
                    comment_count: data.comment_count ?? data.pagination?.total ?? 0,
                };

                if (data.pagination) {
                    this.pagination = data.pagination;
                }

                this.buildUserMapFromComments(this.articleData.comments);
            } else if (response.status === 404) {
                window.location.href = '/static/error.html';
                return;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            this.logError('Failed to load article comments', error);
            window.location.href = '/static/error.html';
        }
    }

    buildUserMapFromComments(comments) {
        this.userMap = {};
        (comments || []).forEach((comment) => {
            if (!comment.user_id) return;
            this.userMap[comment.user_id] = {
                id: comment.user_id,
                name: comment.author_name || `用户${comment.user_id}`,
                avatar: comment.author_avatar,
                projectid: comment.author_blog_id,
            };
        });
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderAuthorMetaItem(userName, userAvatar, userId, blogId) {
        const safeAuthor = this.escapeHtml(userName || '匿名用户');
        const isAnonymous = !userId || userId === 0;
        const avatarPath = !isAnonymous ? (userAvatar || this.getSmallAvatarPath(userId)) : null;
        const fallbackLetter = isAnonymous ? '?' : safeAuthor.charAt(0).toUpperCase();
        const canLinkBlog = !isAnonymous && blogId;

        const avatarHtml = `
            <span class="author-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="author-avatar-fallback" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackLetter}</span>
            </span>
        `;
        const nameHtml = `<span class="author-name">${safeAuthor}</span>`;

        if (canLinkBlog) {
            return `
                <div class="meta-item meta-item-author">
                    <a href="/blog/${blogId}" class="author-link" title="查看博客" target="_blank" rel="noopener noreferrer">
                        ${avatarHtml}
                        ${nameHtml}
                    </a>
                </div>
            `;
        }

        return `
            <div class="meta-item meta-item-author">
                ${avatarHtml}
                ${nameHtml}
            </div>
        `;
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.shadowRoot.innerHTML = `
                <div class="card article-comments-card">
                    <div class="card-header">
                        <h3 class="card-title">
                            ${typeof Icons !== 'undefined' ? Icons.comments : ''}
                            评论
                        </h3>
                    </div>
                    <div class="loading">加载中...</div>
                </div>
            `;
            this.addStyles();
            return;
        }

        const { comments, comment_count } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-comments-card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${typeof Icons !== 'undefined' ? Icons.comments : ''}
                        评论 (${comment_count || 0})
                    </h3>
                </div>
                ${this.renderComments(comments)}
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
        if (!UserManager.isLoggedIn()) {
            return false;
        }

        try {
            const currentUser = UserManager.getCurrentUser();
            if (!currentUser) return false;

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

        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '删除评论',
            message: `确定要删除这条评论吗？\n\n评论内容预览：${contentPreview}\n\n此操作不可撤销。`,
            danger: true,
        })) {
            return;
        }

        try {
            // 获取认证头
            const headers = UserManager.createHeaders({
                'Content-Type': 'application/json'
            });

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
    async refreshComments(commentId = null) {
        try {
            // 跳转到第一页以显示最新评论
            this.currentPage = 1;

            // 重新加载文章数据（包含评论）
            await this.loadArticleData();

            // 重新渲染组件
            this.render();

            // 重新加载用户信息
            await this.loadCommentUsers();

            // 重新渲染以显示用户信息
            this.render();

            // 如果有指定的评论ID，滚动到该评论并突出显示
            if (commentId) {
                this.scrollToCommentAndHighlight(commentId);
            }
        } catch (error) {
            console.error('Failed to refresh comments:', error);
            this.showError('刷新评论失败');
        }
    }

    /**
     * 滚动到指定评论并突出显示
     */
    scrollToCommentAndHighlight(commentId) {
        void this.scrollToCommentElement(commentId);
    }

    /**
     * 将评论滚入视口中央。
     */
    scrollCommentIntoView(commentElement, behavior = 'auto') {
        commentElement.scrollIntoView({ behavior, block: 'center' });
    }

    /**
     * 正文附图加载或布局变化后再次校正滚动位置（不重复高亮）。
     */
    _attachCommentScrollCorrection(commentElement) {
        this._detachCommentScrollCorrection();

        const resync = () => {
            if (!commentElement.isConnected) {
                this._detachCommentScrollCorrection();
                return;
            }
            this.scrollCommentIntoView(commentElement);
        };

        const contentRoot = document.querySelector('article-content-card')?.shadowRoot;
        const imageCleanups = [];

        if (contentRoot) {
            contentRoot.querySelectorAll('img').forEach((img) => {
                if (img.complete) {
                    return;
                }
                const onImageSettled = () => resync();
                img.addEventListener('load', onImageSettled, { once: true });
                img.addEventListener('error', onImageSettled, { once: true });
                imageCleanups.push(() => {
                    img.removeEventListener('load', onImageSettled);
                    img.removeEventListener('error', onImageSettled);
                });
            });
        }

        let resizeFrame = null;
        const resizeObserver = new ResizeObserver(() => {
            if (resizeFrame !== null) {
                cancelAnimationFrame(resizeFrame);
            }
            resizeFrame = requestAnimationFrame(() => {
                resizeFrame = null;
                resync();
            });
        });

        if (contentRoot) {
            resizeObserver.observe(contentRoot);
        }

        this._commentScrollCleanupTimer = setTimeout(() => {
            this._detachCommentScrollCorrection();
        }, 30000);

        this._commentScrollCorrection = {
            resizeObserver,
            imageCleanups,
            cancelResizeFrame: () => {
                if (resizeFrame !== null) {
                    cancelAnimationFrame(resizeFrame);
                    resizeFrame = null;
                }
            }
        };
    }

    _detachCommentScrollCorrection() {
        if (this._commentScrollCleanupTimer) {
            clearTimeout(this._commentScrollCleanupTimer);
            this._commentScrollCleanupTimer = null;
        }

        const state = this._commentScrollCorrection;
        if (!state) {
            return;
        }

        state.cancelResizeFrame();
        state.resizeObserver.disconnect();
        state.imageCleanups.forEach((cleanup) => cleanup());
        this._commentScrollCorrection = null;
    }

    /**
     * 定位到评论：先按当前布局立即滚动，再在正文图片加载后校正。
     */
    async scrollToCommentElement(commentId) {
        this._detachCommentScrollCorrection();

        for (let attempt = 0; attempt < 8; attempt += 1) {
            const commentElement = this.shadowRoot.querySelector(`#post${commentId}`);
            if (commentElement) {
                this.scrollCommentIntoView(commentElement);
                this.highlightComment(commentElement);
                this._attachCommentScrollCorrection(commentElement);
                return;
            }
            await new Promise((resolve) => setTimeout(resolve, 100));
        }
    }

    /** 锚点定位评论的蓝色边框闪烁总时长（毫秒），与原先整行高亮一致 */
    static COMMENT_HASH_FLASH_MS = 3000;

    /**
     * 突出显示目标评论：仅边缘蓝色闪烁，不覆盖文字/背景。
     */
    highlightComment(commentElement) {
        commentElement.classList.remove('comment-hash-flash');
        // 强制重绘，便于从 hash 再次点击同一条时重触发动画
        void commentElement.offsetWidth;
        commentElement.classList.add('comment-hash-flash');
        setTimeout(() => {
            commentElement.classList.remove('comment-hash-flash');
        }, ArticleCommentsCard.COMMENT_HASH_FLASH_MS);
    }

    /**
     * 检查URL锚点并滚动到对应评论
     */
    checkAndScrollToComment() {
        const hash = window.location.hash;
        if (!hash) return;

        const match = hash.match(/^#post(\d+)$/);
        if (!match) return;

        void this.scrollToCommentElement(match[1]);
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
            <ul class="comments-list">
                ${comments.map(comment => this.renderComment(comment)).join('')}
            </ul>
        `;
    }

    /**
     * 渲染单个评论
     */
    renderComment(comment) {
        const { id, content, user_id, post_time, reply_count, author_name, author_avatar, author_blog_id } = comment;

        let userName = author_name || '匿名';
        let blogId = (user_id && user_id !== 0 && author_blog_id) ? author_blog_id : null;
        let userAvatar = author_avatar || null;

        const canDelete = this.canDeleteComment(comment);

        if (user_id) {
            if (this.userMap && this.userMap[user_id]) {
                const user = this.userMap[user_id];
                userName = user.name || userName;
                if (!blogId && user.projectid) {
                    blogId = user.projectid;
                }
                if (!userAvatar && user.avatar) {
                    userAvatar = user.avatar;
                }
            } else if (!author_name) {
                userName = `用户${user_id}`;
            }
        }

        return `
            <li class="comment-item" id="post${id}" data-comment-id="${id}">
                <div class="comment-content-wrapper">
                    <div class="comment-main">
                        <div class="comment-header">
                            ${this.renderAuthorMetaItem(userName, userAvatar, user_id, blogId)}
                            <span class="comment-time">${this.formatDate(post_time)}</span>
                        </div>
                        <div class="comment-text">${HtmlUtils.linkifyPlainTextToHtml(content || '')}</div>
                        ${reply_count > 0 ? `
                            <div class="comment-replies">
                                <span class="reply-count">${reply_count} 条回复</span>
                            </div>
                        ` : ''}
                    </div>
                    ${canDelete ? `
                        <div class="comment-actions">
                            <button type="button" class="btn btn-danger btn-sm btn-icon-only delete-comment-btn"
                                    data-comment-id="${id}"
                                    title="删除评论"
                                    aria-label="删除评论">
                                ${this.getDeleteBtnIcon()}
                            </button>
                        </div>
                    ` : ''}
                </div>
            </li>
        `;
    }

    getDeleteBtnIcon() {
        if (typeof Icons !== 'undefined') {
            return Icons.asBtnIcon(Icons.delete);
        }
        return `<svg class="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="3,6 5,6 21,6"/><path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6m3,0V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"/></svg>`;
    }

    /**
     * 验证URL是否安全有效
     * @param {string} url - 要验证的URL
     * @returns {boolean} - 是否安全有效
     */
    isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            // 只允许指定的安全协议
            const allowedProtocols = ['http:', 'https:', 'ftp:', 'mailto:', 'tel:', 'ed2k:', 'thunder:'];
            return allowedProtocols.includes(urlObj.protocol);
        } catch (error) {
            return false;
        }
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="card article-comments-card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${typeof Icons !== 'undefined' ? Icons.comments : ''}
                        评论
                    </h3>
                </div>
                <div class="error-message">${message}</div>
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

                .card { margin-bottom: 0; overflow: visible; }

                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                }

                .comments-list {
                    list-style: none;
                    margin: 0;
                    padding: 2px var(--spacing-1);
                }

                .comment-item {
                    padding: var(--spacing-3) var(--spacing-4);
                    border-bottom: 1px solid var(--gray-100);
                    transition: background-color var(--transition-fast);
                    border-radius: var(--radius-md, 8px);
                }

                .comment-item:last-child {
                    border-bottom: none;
                }

                .comment-item:hover,
                .comment-item:focus-within {
                    background: var(--interactive-hover-bg);
                }

                .comment-item:hover .author-name,
                .comment-item:focus-within .author-name {
                    color: var(--interactive-hover-text);
                }

                /* 从 #post{id} 进入：内嵌蓝框闪烁，避免被卡片裁切，总时长 3s（6×0.5s） */
                .comment-item.comment-hash-flash {
                    position: relative;
                    z-index: 1;
                    background-color: var(--white);
                    animation: commentHashBorderBlink 0.5s ease-in-out 6;
                }

                @keyframes commentHashBorderBlink {
                    0%, 100% {
                        box-shadow: inset 0 0 0 2px rgba(37, 99, 235, 0.95);
                    }
                    50% {
                        box-shadow: inset 0 0 0 2px rgba(37, 99, 235, 0.12);
                    }
                }

                .comment-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: var(--spacing-2);
                    margin-bottom: var(--spacing-1);
                }

                .meta-item {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    min-width: 0;
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                    white-space: nowrap;
                }

                .meta-item-author {
                    gap: var(--spacing-2);
                }

                .author-link {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    text-decoration: none;
                    color: inherit;
                    min-width: 0;
                }

                .author-link:hover {
                    text-decoration: none;
                }

                .author-link:hover .author-name {
                    color: var(--interactive-hover-text);
                }

                .author-avatar {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--gray-100);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                }

                .author-avatar img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                }

                .author-avatar-fallback {
                    width: 100%;
                    height: 100%;
                    align-items: center;
                    justify-content: center;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    color: var(--gray-600);
                }

                .author-name {
                    font-weight: 500;
                    color: var(--gray-700);
                    transition: color var(--transition-fast);
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .comment-content-wrapper {
                    display: grid;
                    grid-template-columns: minmax(0, 1fr) auto;
                    align-items: start;
                    column-gap: var(--spacing-2);
                    flex: 1;
                    min-width: 0;
                }

                .comment-main {
                    grid-column: 1;
                    min-width: 0;
                }

                .comment-actions {
                    grid-column: 2;
                    grid-row: 1;
                    align-self: start;
                    margin: 0;
                    padding: 0;
                }

                .comment-time {
                    font-size: var(--font-size-xs);
                    color: var(--gray-500);
                    line-height: 1.3;
                    white-space: nowrap;
                }

                .btn.btn-sm {
                    min-height: 36px;
                    padding: 0 12px;
                    gap: 6px;
                    font-size: var(--font-size-sm);
                    line-height: 1.25;
                }

                .btn.btn-sm.btn-icon-only {
                    width: 36px;
                    height: 36px;
                    min-width: 36px;
                    min-height: 36px;
                    padding: 0;
                    gap: 0;
                }

                .btn .btn-icon {
                    width: 18px;
                    height: 18px;
                }

                .comment-text {
                    line-height: 1.6;
                    color: var(--gray-600);
                    font-size: var(--font-size-sm);
                    font-weight: 400;
                    margin: 0;
                    padding: 0;
                    word-wrap: break-word;
                    white-space: pre-line;
                    overflow-wrap: break-word;
                }

                .comment-text a {
                    word-break: break-all;
                    overflow-wrap: anywhere;
                    max-width: 100%;
                    display: inline-block;
                }

                .comment-replies {
                    display: flex;
                    justify-content: flex-end;
                    margin-top: var(--spacing-1);
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
                    padding: var(--spacing-3) var(--spacing-4);
                    color: var(--gray-500);
                }

                .no-comments p {
                    margin: 0;
                    font-style: italic;
                }

                .pagination-container {
                    padding: var(--spacing-2) var(--spacing-4);
                    border-top: 1px solid var(--gray-100);
                    background: var(--gray-50);
                }

                .loading {
                    text-align: center;
                    color: var(--gray-500);
                    padding: var(--spacing-3) var(--spacing-4);
                }

                .error-message {
                    text-align: center;
                    color: var(--error-color);
                    padding: var(--spacing-3) var(--spacing-4);
                    background: var(--gray-50);
                }
            `;
            this.shadowRoot.appendChild(style);
        }
    }
}

// 注册组件
customElements.define('article-comments-card', ArticleCommentsCard);
