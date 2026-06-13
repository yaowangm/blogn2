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

    static get ICON_STROKE() {
        return 'currentColor';
    }

    getMetaIcon(type) {
        const s = MessagesListCard.ICON_STROKE;
        const svg = (paths) =>
            `<svg class="meta-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        switch (type) {
            case 'user':
                return svg('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>');
            case 'time':
                return svg('<circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>');
            case 'views':
                return svg('<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>');
            case 'replies':
                return svg('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>');
            case 'reply':
                return svg('<polyline points="9 17 4 12 9 7"/><path d="M20 18v-2a4 4 0 0 0-4-4H4"/>');
            default:
                return svg('<circle cx="12" cy="12" r="10"/>');
        }
    }

    getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    renderAuthorAvatar(authorName, userId) {
        const safeAuthor = this.escapeHtml(authorName || '用户');
        const avatarPath = this.getSmallAvatarPath(userId);
        const fallbackLetter = safeAuthor.charAt(0).toUpperCase();

        return `
            <span class="author-avatar" aria-hidden="true">
                ${avatarPath ? `
                    <img src="${avatarPath}" alt=""
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                         onload="this.style.display='block'; this.nextElementSibling.style.display='none';">
                ` : ''}
                <span class="author-avatar-fallback" style="display: ${avatarPath ? 'none' : 'flex'};">${fallbackLetter}</span>
            </span>
        `;
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
        const safeAuthor = this.escapeHtml(message.author);
        const safeSubject = this.escapeHtml(message.subject);
        const safeLastReplyAuthor = message.last_reply_author ? this.escapeHtml(message.last_reply_author) : '';
        const safePostTime = this.escapeHtml(message.post_time);
        const safeLastReplyTime = message.last_reply_time ? this.escapeHtml(message.last_reply_time) : '';
        const hits = message.hits || 0;
        const replyCount = message.reply_count || 0;

        const lastReplyHtml = safeLastReplyAuthor ? `
            <div class="thread-last-reply">
                ${this.getMetaIcon('reply')}
                <span>最后回复 <strong>${safeLastReplyAuthor}</strong>${safeLastReplyTime ? ` · ${safeLastReplyTime}` : ''}</span>
            </div>
        ` : '';

        return `
            <article class="thread-row${isAdmin ? ' thread-row-has-admin' : ''}" data-message-id="${message.id}">
                <a class="thread-row-link"
                   href="/thread/${message.id}"
                   target="_blank"
                   rel="noopener">
                    <div class="thread-row-body">
                        <h4 class="thread-title">${safeSubject}</h4>
                        <div class="thread-meta">
                            <div class="meta-item meta-item-author">
                                ${this.renderAuthorAvatar(message.author, message.userid)}
                                <span class="author-name">${safeAuthor}</span>
                            </div>
                            <div class="meta-item">
                                ${this.getMetaIcon('time')}
                                <span>${safePostTime}</span>
                            </div>
                            <div class="meta-item">
                                ${this.getMetaIcon('views')}
                                <span>${hits.toLocaleString()} 阅读</span>
                            </div>
                        </div>
                        ${lastReplyHtml}
                    </div>
                    <div class="thread-row-aside">
                        <span class="reply-pill">
                            ${this.getMetaIcon('replies')}
                            <span>${replyCount.toLocaleString()} 回复</span>
                        </span>
                    </div>
                </a>
                ${isAdmin ? this.renderDeleteButton(message.id) : ''}
            </article>
        `;
    }

    renderMessagesList() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (!cardBody) {
            return;
        }

        if (this.messages.length === 0) {
            cardBody.innerHTML = `
                <div class="thread-list thread-list-empty">
                    <div class="empty-state">
                        <div class="empty-icon">${this.getMetaIcon('replies')}</div>
                        <p class="empty-title">暂无留言</p>
                        <p class="empty-hint">成为第一个发表留言的人吧</p>
                    </div>
                </div>
            `;
            return;
        }

        const isAdmin = typeof UserManager !== 'undefined' && UserManager.isAdmin();
        const messagesHtml = this.messages.map((message) => this.renderMessageItem(message, isAdmin)).join('');

        cardBody.innerHTML = `
            <div class="thread-list">
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
                <div class="thread-list thread-list-loading">
                    <div class="loading-state">正在加载留言...</div>
                </div>
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
        return this.getMetaIcon('replies');
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

                .card-title :is(svg, .title-icon) {
                    width: 18px;
                    height: 18px;
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

                .thread-list {
                    display: flex;
                    flex-direction: column;
                    gap: calc(var(--spacing-2) + 2px);
                }

                .thread-row {
                    position: relative;
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    transition:
                        background-color var(--transition-fast),
                        border-color var(--transition-fast),
                        box-shadow var(--transition-fast);
                }

                .thread-row:hover {
                    background: var(--white);
                    border-color: var(--gray-300);
                    box-shadow: var(--shadow-sm);
                }

                .thread-row-link {
                    display: grid;
                    grid-template-columns: minmax(0, 1fr) auto;
                    gap: var(--spacing-3);
                    align-items: center;
                    padding: var(--spacing-3);
                    text-decoration: none;
                    color: inherit;
                }

                .thread-row-has-admin .thread-row-link {
                    padding-right: calc(var(--spacing-3) + 2.25rem);
                }

                .thread-row-link:focus {
                    outline: none;
                }

                .thread-row-link:focus-visible {
                    outline: 2px solid var(--primary-color);
                    outline-offset: 2px;
                    border-radius: var(--radius-md);
                }

                .thread-row-body {
                    min-width: 0;
                }

                .thread-title {
                    margin: 0 0 var(--spacing-2);
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-900);
                    line-height: 1.45;
                    word-wrap: break-word;
                    overflow-wrap: anywhere;
                }

                .thread-row:hover .thread-title {
                    color: var(--primary-color);
                }

                .thread-meta {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: var(--spacing-2) var(--spacing-3);
                }

                .meta-item {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                    white-space: nowrap;
                }

                .meta-item-author {
                    gap: var(--spacing-2);
                }

                .meta-icon {
                    display: block;
                    width: 16px;
                    height: 16px;
                    flex-shrink: 0;
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
                }

                .thread-last-reply {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    margin-top: var(--spacing-2);
                    padding-top: var(--spacing-2);
                    border-top: 1px dashed var(--gray-200);
                    color: var(--gray-500);
                    font-size: var(--font-size-xs);
                    min-width: 0;
                }

                .thread-last-reply span {
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .thread-last-reply strong {
                    color: var(--gray-700);
                    font-weight: 600;
                }

                .thread-row-aside {
                    flex-shrink: 0;
                }

                .reply-pill {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    padding: 0.375rem 0.625rem;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    font-variant-numeric: tabular-nums;
                    color: var(--primary-color);
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    border-radius: var(--radius-full);
                    white-space: nowrap;
                }

                .reply-pill .meta-icon {
                    color: var(--primary-color);
                }

                .thread-row .btn-delete-reveal {
                    position: absolute;
                    top: var(--spacing-2);
                    right: var(--spacing-2);
                }

                .loading-state,
                .empty-state {
                    text-align: center;
                    padding: var(--spacing-6) var(--spacing-4);
                    color: var(--gray-500);
                }

                .empty-icon {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 3rem;
                    height: 3rem;
                    margin-bottom: var(--spacing-3);
                    border-radius: var(--radius-full);
                    background: var(--gray-100);
                    color: var(--gray-400);
                }

                .empty-icon .meta-icon {
                    width: 20px;
                    height: 20px;
                }

                .empty-title {
                    margin: 0 0 var(--spacing-1);
                    font-size: var(--font-size-base);
                    font-weight: 600;
                    color: var(--gray-700);
                }

                .empty-hint {
                    margin: 0;
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                @media (max-width: 768px) {
                    .thread-row-link {
                        grid-template-columns: 1fr;
                    }

                    .thread-row-aside {
                        justify-self: start;
                    }

                    .btn-delete-reveal {
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
                    <div class="thread-list thread-list-loading">
                        <div class="loading-state">正在加载留言...</div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('messages-list-card', MessagesListCard);
