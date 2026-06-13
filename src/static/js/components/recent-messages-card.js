class RecentMessagesCard extends BaseComponent {
    constructor() {
        super();
        this.messages = [];
        this.loading = true;
        this.error = false;
    }

    connectedCallback() {
        this.render();
        BaseComponent.observeWhenVisible(this, () => this.loadContent());
    }

    async loadContent() {
        try {
            this.loading = true;
            this.error = false;
            this.render();

            const response = await fetch('/api/blogs/messages/recent');
            if (!response.ok) {
                throw new Error('Failed to fetch recent messages');
            }
            this.messages = await response.json();
        } catch (error) {
            this.logError('Error loading recent messages', error);
            this.messages = [];
            this.error = true;
        } finally {
            this.loading = false;
            this.render();
        }
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
        const safeTime = this.escapeHtml(message.time || '');
        return `
            <div class="article-meta">
                <div class="meta-items-left">
                    ${this.renderAuthorMetaItem(message.author, message.avatar, message.userid)}
                    <div class="meta-item">
                        <span>${safeTime}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderMessageItem(message) {
        const safeSubject = this.escapeHtml(message.subject || '无标题');
        const safeReplyInfo = message.reply_info ? this.escapeHtml(message.reply_info) : '';
        const messageId = message.id;
        const hasValidId = messageId !== null && messageId !== undefined;

        const contentHtml = `
            ${this.renderMessageMeta(message)}
            <p class="post-title">${safeSubject}</p>
            ${safeReplyInfo ? `<p class="post-excerpt post-excerpt--single-line">${safeReplyInfo}</p>` : ''}
        `;

        if (hasValidId) {
            return `
                <a href="/thread/${messageId}" class="post-item" target="_blank" rel="noopener noreferrer" title="查看留言">
                    <div class="post-content">
                        ${contentHtml}
                    </div>
                </a>
            `;
        }

        return `
            <div class="post-item post-item-block disabled">
                <div class="post-content">
                    ${contentHtml}
                </div>
            </div>
        `;
    }

    renderMessages() {
        if (this.messages.length === 0) {
            return `
                <div class="post-list">
                    <div class="post-item post-item-block">
                        <div class="post-content">
                            <p class="post-excerpt">暂无留言</p>
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="post-list">
                ${this.messages.map((message) => this.renderMessageItem(message)).join('')}
            </div>
        `;
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');

                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }

                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                    flex-shrink: 0;
                }

                .view-all-link {
                    font-size: var(--font-size-sm);
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                    transition: var(--transition-fast);
                }

                .view-all-link:hover {
                    color: var(--primary-color-dark);
                    text-decoration: underline;
                }

                .loading {
                    text-align: center;
                    padding: var(--spacing-8);
                    color: var(--gray-500);
                }

                .post-title {
                    font-weight: 400;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <span class="title-icon">${typeof Icons !== 'undefined' ? Icons.message : ''}</span>
                        最近留言
                    </h3>
                    <a href="/messages" class="view-all-link" target="_blank" rel="noopener noreferrer">查看全部</a>
                </div>
                <div class="card-body">
                    ${this.loading ? `<div class="loading">${this.createLoadingHTML()}</div>` :
                      this.error ? this.createErrorHTML('加载失败，请稍后重试') :
                      this.renderMessages()}
                </div>
            </div>
        `;
    }
}

customElements.define('recent-messages-card', RecentMessagesCard);
