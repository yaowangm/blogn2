class MessagesListCard extends BaseComponent {
    constructor() {
        super();
        this.messages = [];
        this.loading = true;
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPages = 0;
        this.total = 0;
    }

    connectedCallback() {
        this.currentPage = this.getCurrentPageFromUrl();
        this.render();
        this.loadMessages();
        this.setupPaginationListener();
    }

    setupPaginationListener() {
        // 分页事件通过 setPagination 回调处理
    }

    async loadMessages() {
        this.loading = true;
        this.updateLoadingState();
        this.updateHeaderCount();

        try {
            const response = await fetch(`/api/messages?page=${this.currentPage}&limit=${this.pageSize}`);
            if (!response.ok) {
                throw new Error('Failed to fetch messages');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading messages', error);
            this.showError();
        }
    }

    refreshToFirstPage() {
        this.currentPage = 1;
        this.loadMessages();
    }

    updateContent(data) {
        this.messages = data.messages || [];
        this.total = data.total || 0;
        this.totalPages = data.total_pages || 0;
        this.currentPage = data.current_page || 1;
        this.loading = false;

        this.renderMessagesList();
        this.updatePagination();
        this.updateHeaderCount();
    }

    updateHeaderCount() {
        const countEl = this.shadowRoot?.querySelector('.thread-total-count');
        if (!countEl) {
            return;
        }
        if (this.loading) {
            countEl.textContent = '';
            countEl.hidden = true;
            return;
        }
        countEl.textContent = `${this.total.toLocaleString()} 条`;
        countEl.hidden = false;
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderAuthorMetaItem(authorName, avatar, userId) {
        const safeAuthor = this.escapeHtml(authorName || '匿名用户');
        const isAnonymous = this.isAnonymousUser(userId);
        const avatarPath = !isAnonymous ? (avatar || this.getSmallAvatarPath(userId)) : null;
        const fallbackContent = this.getAuthorAvatarFallbackContent(authorName, userId);
        const fallbackClass = isAnonymous
            ? 'author-avatar-fallback author-avatar-fallback--default-user'
            : 'author-avatar-fallback';

        const avatarHtml = `
            <span class="author-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="${fallbackClass}" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackContent}</span>
            </span>
        `;

        return `
            <div class="meta-item meta-item-author">
                ${avatarHtml}
                <span class="author-name">${safeAuthor}</span>
            </div>
        `;
    }

    renderMessageMeta(message) {
        const safePostTime = this.escapeHtml(message.post_time || '');
        return `
            <div class="article-meta">
                <div class="meta-items-left">
                    ${this.renderAuthorMetaItem(message.author, message.avatar, message.userid)}
                    <div class="meta-item">
                        <span>${safePostTime}</span>
                    </div>
                </div>
            </div>
        `;
    }

    buildReplyExcerpt(message) {
        const safeLastReplyAuthor = message.last_reply_author ? this.escapeHtml(message.last_reply_author) : '';
        const safeLastReplyTime = message.last_reply_time ? this.escapeHtml(message.last_reply_time) : '';

        if (safeLastReplyAuthor) {
            return `最后回复: ${safeLastReplyAuthor}${safeLastReplyTime ? ` · ${safeLastReplyTime}` : ''}`;
        }

        const replyCount = message.reply_count || 0;
        if (replyCount > 0) {
            return `回复数: ${replyCount}`;
        }

        return '';
    }

    renderDeleteButton(messageId) {
        return `
            <button type="button"
                    class="btn btn-danger btn-sm btn-icon-only btn-delete-reveal"
                    data-message-id="${messageId}"
                    data-is-main="true"
                    title="删除留言"
                    aria-label="删除留言">
                ${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.delete) : `<svg class="delete-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="3,6 5,6 21,6"></polyline><path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>`}
            </button>
        `;
    }

    renderMessageItem(message, isAdmin) {
        const safeSubject = this.escapeHtml(message.subject || '无标题');
        const replyExcerpt = this.buildReplyExcerpt(message);

        const contentHtml = `
            ${this.renderMessageMeta(message)}
            <p class="post-title">${safeSubject}</p>
            ${replyExcerpt ? `<p class="post-excerpt post-excerpt--single-line">${replyExcerpt}</p>` : ''}
        `;

        return `
            <div class="message-item-row${isAdmin ? ' message-item-row--admin' : ''}">
                <a href="/thread/${message.id}"
                   class="post-item"
                   target="_blank"
                   rel="noopener noreferrer"
                   title="查看留言">
                    <div class="post-content">
                        ${contentHtml}
                    </div>
                </a>
                ${isAdmin ? this.renderDeleteButton(message.id) : ''}
            </div>
        `;
    }

    renderMessagesList() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (!cardBody) {
            return;
        }

        if (this.messages.length === 0) {
            cardBody.innerHTML = `
                <div class="post-list">
                    <div class="post-item post-item-block">
                        <div class="post-content">
                            <p class="post-excerpt">暂无留言</p>
                            <p class="post-excerpt post-excerpt--single-line">成为第一个发表留言的人吧</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        const isAdmin = typeof UserManager !== 'undefined' && UserManager.isAdmin();
        const messagesHtml = this.messages.map((message) => this.renderMessageItem(message, isAdmin)).join('');

        cardBody.innerHTML = `
            <div class="post-list">
                ${messagesHtml}
            </div>
        `;

        if (isAdmin) {
            this.attachDeleteListeners();
        }
    }

    attachDeleteListeners() {
        this.shadowRoot.querySelectorAll('.btn-delete-reveal').forEach((button) => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                event.stopPropagation();
                const messageId = button.getAttribute('data-message-id');
                await this.showDeleteConfirmation(messageId, true);
            });
        });
    }

    async showDeleteConfirmation(messageId, isMainPost) {
        const confirmMessage = isMainPost
            ? '删除主贴将同时删除所有相关的跟贴，此操作不可撤销！'
            : '此操作不可撤销！';

        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: isMainPost ? '删除主贴' : '删除跟贴',
            message: confirmMessage,
            danger: true,
        })) {
            return;
        }
        this.deleteMessage(messageId);
    }

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
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            const result = await response.json();

            if (response.ok && result.success) {
                alert(result.message);
                this.loadMessages();
            } else {
                alert(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除留言失败:', error);
            alert('删除失败，请稍后重试');
        }
    }

    updatePagination() {
        const paginationCard = document.querySelector('navigation-card[mode="pagination"]');
        if (paginationCard) {
            paginationCard.setPagination({
                current_page: this.currentPage,
                total_pages: this.totalPages,
                total: this.total,
                total_count: this.total,
                has_prev: this.currentPage > 1,
                has_next: this.currentPage < this.totalPages,
                item_type: '条留言',
            }, (page) => {
                this.currentPage = page;
                this.loadMessages();
            });
        }
    }

    updateLoadingState() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = `
                <div class="loading">${this.createLoadingHTML()}</div>
            `;
        }
    }

    showError() {
        this.loading = false;
        this.updateHeaderCount();
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML('加载失败，请稍后重试');
        }
    }

    renderCardTitleIcon() {
        if (typeof Icons !== 'undefined' && Icons.message) {
            return Icons.message.replace('class="nav-icon"', 'class="title-icon"');
        }
        return '';
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');

                :host {
                    display: block;
                }

                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    flex-wrap: wrap;
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                    flex-shrink: 0;
                }

                .thread-total-count {
                    margin-left: auto;
                    display: inline-flex;
                    align-items: center;
                    padding: 0.125rem 0.625rem;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    font-variant-numeric: tabular-nums;
                    color: var(--gray-600);
                    background: var(--gray-100);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-full);
                    line-height: 1.4;
                }

                .thread-total-count[hidden] {
                    display: none;
                }

                .message-item-row {
                    position: relative;
                }

                .message-item-row--admin .post-item {
                    padding-right: calc(var(--spacing-3) + 2.25rem);
                }

                .message-item-row .btn-delete-reveal {
                    position: absolute;
                    top: var(--spacing-2);
                    right: var(--spacing-2);
                    z-index: 1;
                }

                .post-title {
                    font-weight: 400;
                }

                .message-item-row .post-excerpt.post-excerpt--single-line {
                    font-size: var(--font-size-xs);
                    font-weight: 500;
                    color: var(--gray-700);
                    line-height: 1.35;
                }

                .message-item-row a.post-item:hover .post-excerpt.post-excerpt--single-line,
                .message-item-row a.post-item:focus-visible .post-excerpt.post-excerpt--single-line {
                    color: var(--interactive-hover-text);
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                @media (max-width: 768px) {
                    .message-item-row .btn-delete-reveal {
                        opacity: 1;
                        pointer-events: auto;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${this.renderCardTitleIcon()}
                        留言本
                        <span class="thread-total-count" hidden></span>
                    </h3>
                </div>
                <div class="card-body">
                    <div class="loading">${this.createLoadingHTML()}</div>
                </div>
            </div>
        `;
    }
}

customElements.define('messages-list-card', MessagesListCard);
