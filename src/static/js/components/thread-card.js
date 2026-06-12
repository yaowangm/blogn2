class ThreadCard extends BaseComponent {
    constructor() {
        super();
        this.threadId = null;
        this.messages = [];
        this.loading = true;
    }

    static get observedAttributes() {
        return ['thread-id'];
    }

    connectedCallback() {
        this.threadId = this.getAttribute('thread-id');
        this.render();
        this.loadThread();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'thread-id' && newValue) {
            this.threadId = newValue;
            this.loadThread();
        }
    }

    async loadThread() {
        if (!this.threadId) {
            this.showError('无效的主题ID');
            return;
        }

        this.loading = true;
        this.updateLoadingState();
        this.updateCardHeader();

        try {
            const response = await fetch(`/api/thread/${this.threadId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch thread');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading thread', error);
            this.showError('加载主题失败，请稍后重试');
        }
    }

    updateContent(data) {
        this.messages = data.messages || [];
        this.loading = false;
        this.renderMessagesList();
        this.updateCardHeader();
        this.updatePageTitle();
    }

    getMainPost() {
        return this.messages.find((message) => message.is_main_post) || this.messages[0] || null;
    }

    getReplyCount() {
        const mainPost = this.getMainPost();
        if (mainPost && typeof mainPost.replycount === 'number') {
            return mainPost.replycount;
        }
        return Math.max(0, this.messages.length - 1);
    }

    updateCardHeader() {
        const titleText = this.shadowRoot?.querySelector('.card-title-text');
        const replyCountEl = this.shadowRoot?.querySelector('.thread-reply-count');
        if (!titleText || !replyCountEl) {
            return;
        }

        if (this.loading) {
            titleText.textContent = '主题讨论';
            replyCountEl.hidden = true;
            return;
        }

        const mainPost = this.getMainPost();
        titleText.textContent = mainPost?.subject || '主题讨论';
        const replyCount = this.getReplyCount();
        replyCountEl.textContent = `${replyCount.toLocaleString()} 回复`;
        replyCountEl.hidden = false;
    }

    static get ICON_STROKE() {
        return 'currentColor';
    }

    getMetaIcon(type) {
        const s = ThreadCard.ICON_STROKE;
        const svg = (paths) =>
            `<svg class="meta-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
        switch (type) {
            case 'time':
                return svg('<circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>');
            case 'replies':
                return svg('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>');
            case 'floor':
                return svg('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>');
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

    renderDeleteButton(messageId, isMainPost) {
        return `
            <button type="button"
                    class="delete-button"
                    data-message-id="${messageId}"
                    data-is-main="${isMainPost ? 'true' : 'false'}"
                    aria-label="${isMainPost ? '删除主题' : '删除回复'}">
                <svg class="delete-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <polyline points="3,6 5,6 21,6"></polyline>
                    <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
            </button>
        `;
    }

    renderPostMeta(message) {
        const safeAuthor = this.escapeHtml(message.author);
        const safePostTime = this.escapeHtml(message.post_time);

        return `
            <div class="post-meta">
                <div class="meta-item meta-item-author">
                    ${this.renderAuthorAvatar(message.author, message.userid)}
                    <span class="author-name">${safeAuthor}</span>
                </div>
                <div class="meta-item">
                    ${this.getMetaIcon('time')}
                    <span>${safePostTime}</span>
                </div>
            </div>
        `;
    }

    renderMainPost(message, isAdmin) {
        const safeSubject = this.escapeHtml(message.subject);
        const safeContent = HtmlUtils.linkifyPlainTextToHtml(message.content || '');

        return `
            <article class="post-card post-card-main${isAdmin ? ' post-card-has-admin' : ''}" data-message-id="${message.id}">
                <div class="post-card-top">
                    <span class="post-badge post-badge-main">主题</span>
                    ${isAdmin ? this.renderDeleteButton(message.id, true) : ''}
                </div>
                <h2 class="post-title">${safeSubject}</h2>
                ${this.renderPostMeta(message)}
                <div class="post-content">${safeContent}</div>
            </article>
        `;
    }

    renderReplyPost(message, floor, isAdmin) {
        const safeContent = HtmlUtils.linkifyPlainTextToHtml(message.content || '');

        return `
            <article class="post-card post-card-reply${isAdmin ? ' post-card-has-admin' : ''}" data-message-id="${message.id}">
                <div class="post-card-top">
                    <span class="post-badge post-badge-reply">
                        ${this.getMetaIcon('floor')}
                        <span>#${floor}</span>
                    </span>
                    ${isAdmin ? this.renderDeleteButton(message.id, false) : ''}
                </div>
                ${this.renderPostMeta(message)}
                <div class="post-content">${safeContent}</div>
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
                <div class="thread-posts thread-posts-empty">
                    <div class="empty-state">
                        <div class="empty-icon">${this.getMetaIcon('replies')}</div>
                        <p class="empty-title">暂无留言</p>
                        <p class="empty-hint">该主题下还没有讨论内容</p>
                    </div>
                </div>
            `;
            return;
        }

        const isAdmin = typeof UserManager !== 'undefined' && UserManager.isAdmin();
        const mainPost = this.getMainPost();
        const replies = this.messages.filter((message) => !message.is_main_post && message.id !== mainPost?.id);
        let floor = 1;

        const repliesHtml = replies.map((message) => {
            const html = this.renderReplyPost(message, floor, isAdmin);
            floor += 1;
            return html;
        }).join('');

        cardBody.innerHTML = `
            <div class="thread-posts">
                ${mainPost ? this.renderMainPost(mainPost, isAdmin) : ''}
                ${replies.length > 0 ? `
                    <div class="reply-list">
                        <div class="reply-list-label">
                            ${this.getMetaIcon('replies')}
                            <span>全部回复</span>
                            <span class="reply-list-count">${replies.length.toLocaleString()}</span>
                        </div>
                        ${repliesHtml}
                    </div>
                ` : ''}
            </div>
        `;

        if (isAdmin) {
            this.attachDeleteListeners();
        }
    }

    updateLoadingState() {
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = `
                <div class="thread-posts thread-posts-loading">
                    <div class="loading-state">正在加载主题...</div>
                </div>
            `;
        }
    }

    refreshMessages() {
        if (this.threadId) {
            this.loadThread();
        }
    }

    attachDeleteListeners() {
        this.shadowRoot.querySelectorAll('.delete-button').forEach((button) => {
            button.addEventListener('click', async (event) => {
                event.stopPropagation();
                const messageId = button.getAttribute('data-message-id');
                const isMainPost = button.getAttribute('data-is-main') === 'true';
                await this.showDeleteConfirmation(messageId, isMainPost);
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
                if (result.is_main_post) {
                    window.location.href = '/messages';
                } else {
                    this.loadThread();
                }
            } else {
                alert(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除留言失败:', error);
            alert('删除失败，请稍后重试');
        }
    }

    showError(message) {
        this.loading = false;
        this.updateCardHeader();
        const cardBody = this.shadowRoot.querySelector('.card-body');
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML(message);
        }
    }

    updatePageTitle() {
        const mainPost = this.getMainPost();
        if (mainPost?.subject) {
            const title = mainPost.subject.length > 20
                ? `${mainPost.subject.substring(0, 20)}...`
                : mainPost.subject;
            document.title = `${title} - 留言本`;
        } else {
            document.title = '留言本主题 - BlogN2';
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
                    min-width: 0;
                }

                .card-title :is(svg, .title-icon) {
                    width: 18px;
                    height: 18px;
                    color: var(--primary-color);
                    flex-shrink: 0;
                }

                .card-title-text {
                    min-width: 0;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .thread-reply-count {
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
                    flex-shrink: 0;
                }

                .thread-reply-count[hidden] {
                    display: none;
                }

                .thread-posts {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }

                .post-card {
                    position: relative;
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    padding: var(--spacing-3);
                    transition:
                        background-color var(--transition-fast),
                        border-color var(--transition-fast),
                        box-shadow var(--transition-fast);
                }

                .post-card:hover {
                    background: var(--white);
                    border-color: var(--gray-300);
                    box-shadow: var(--shadow-sm);
                }

                .post-card-main {
                    background: #eff6ff;
                    border-color: #bfdbfe;
                }

                .post-card-main:hover {
                    background: var(--white);
                    border-color: #93c5fd;
                }

                .post-card-top {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: var(--spacing-2);
                    margin-bottom: var(--spacing-2);
                }

                .post-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-1);
                    padding: 0.125rem 0.5rem;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    border-radius: var(--radius-full);
                    line-height: 1.4;
                }

                .post-badge-main {
                    color: var(--primary-color);
                    background: var(--white);
                    border: 1px solid #93c5fd;
                }

                .post-badge-reply {
                    color: var(--gray-600);
                    background: var(--white);
                    border: 1px solid var(--gray-200);
                }

                .post-badge-reply .meta-icon {
                    width: 14px;
                    height: 14px;
                }

                .post-title {
                    margin: 0 0 var(--spacing-2);
                    font-size: var(--font-size-lg);
                    font-weight: 700;
                    color: var(--gray-900);
                    line-height: 1.45;
                    word-wrap: break-word;
                    overflow-wrap: anywhere;
                }

                .post-meta {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: var(--spacing-2) var(--spacing-3);
                    margin-bottom: var(--spacing-3);
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

                .post-content {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.7;
                    word-wrap: break-word;
                    overflow-wrap: anywhere;
                    white-space: pre-wrap;
                }

                .post-content a {
                    color: var(--primary-color);
                    text-decoration: underline;
                    word-break: break-word;
                }

                .post-content a:hover {
                    color: var(--primary-hover, #1f5fbf);
                }

                .reply-list {
                    display: flex;
                    flex-direction: column;
                    gap: calc(var(--spacing-2) + 2px);
                }

                .reply-list-label {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    padding: 0 var(--spacing-1);
                    font-size: var(--font-size-sm);
                    font-weight: 600;
                    color: var(--gray-700);
                }

                .reply-list-count {
                    display: inline-flex;
                    align-items: center;
                    min-width: 1.5rem;
                    padding: 0.125rem 0.5rem;
                    font-size: var(--font-size-xs);
                    font-weight: 600;
                    font-variant-numeric: tabular-nums;
                    color: var(--primary-color);
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    border-radius: var(--radius-full);
                }

                .post-card-reply {
                    margin-left: var(--spacing-4);
                    border-left: 3px solid var(--gray-300);
                    border-top-left-radius: 0;
                    border-bottom-left-radius: 0;
                }

                .delete-button {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 2rem;
                    height: 2rem;
                    padding: 0;
                    background: var(--white);
                    color: var(--gray-400);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    opacity: 0;
                    transition:
                        opacity var(--transition-fast),
                        color var(--transition-fast),
                        border-color var(--transition-fast),
                        background-color var(--transition-fast);
                }

                .post-card-has-admin .post-card-top {
                    min-height: 2rem;
                }

                .post-card:hover .delete-button,
                .delete-button:focus-visible {
                    opacity: 1;
                }

                .delete-button:hover {
                    color: #dc2626;
                    border-color: #fecaca;
                    background: #fef2f2;
                }

                .delete-icon {
                    width: 16px;
                    height: 16px;
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
                    .post-card-reply {
                        margin-left: var(--spacing-2);
                    }

                    .delete-button {
                        opacity: 1;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        ${this.renderCardTitleIcon()}
                        <span class="card-title-text">主题讨论</span>
                        <span class="thread-reply-count" hidden></span>
                    </h3>
                </div>
                <div class="card-body">
                    <div class="thread-posts thread-posts-loading">
                        <div class="loading-state">正在加载主题...</div>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('thread-card', ThreadCard);
