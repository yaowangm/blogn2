/**
 * 留言列表行渲染（最近留言卡片与留言列表页共用）
 */
class MessageListRenderer {
    static getSmallAvatarPath(userId) {
        if (!userId) {
            return null;
        }
        const prefix = Math.floor(userId / 10000) + 1;
        return `/avatar/${prefix}/s_${userId}.jpg`;
    }

    static buildReplyExcerpt(message, escapeHtml) {
        if (message.reply_info) {
            return escapeHtml(String(message.reply_info));
        }

        const safeLastReplyAuthor = message.last_reply_author ? escapeHtml(message.last_reply_author) : '';
        const safeLastReplyTime = message.last_reply_time ? escapeHtml(message.last_reply_time) : '';

        if (safeLastReplyAuthor) {
            return `最后回复: ${safeLastReplyAuthor}${safeLastReplyTime ? ` · ${safeLastReplyTime}` : ''}`;
        }

        const replyCount = message.reply_count || 0;
        if (replyCount > 0) {
            return `回复数: ${replyCount}`;
        }

        return '';
    }

    static getMessageTime(message) {
        return message.time ?? message.post_time ?? '';
    }

    static renderAuthorMetaItem(component, authorName, avatar, userId, blogId = null) {
        const safeAuthor = component.escapeHtml(authorName || '匿名用户');
        const isAnonymous = component.isAnonymousUser(userId);
        const avatarPath = !isAnonymous ? (avatar || MessageListRenderer.getSmallAvatarPath(userId)) : null;
        const fallbackContent = component.getAuthorAvatarFallbackContent(authorName, userId);
        const fallbackClass = isAnonymous
            ? 'author-avatar-fallback author-avatar-fallback--default-user'
            : 'author-avatar-fallback';
        const canLinkBlog = !isAnonymous && blogId;

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

    static renderMessageMeta(component, message) {
        const safeTime = component.escapeHtml(MessageListRenderer.getMessageTime(message));
        const blogId = message.author_blog_id || message.blog_id || null;
        return `
            <div class="article-meta">
                <div class="meta-items-left">
                    ${MessageListRenderer.renderAuthorMetaItem(component, message.author, message.avatar, message.userid, blogId)}
                    <div class="meta-item">
                        <span>${safeTime}</span>
                    </div>
                </div>
            </div>
        `;
    }

    static renderMessageRowContent(component, message) {
        const safeSubject = component.escapeHtml(message.subject || '无标题');
        const replyExcerpt = MessageListRenderer.buildReplyExcerpt(message, component.escapeHtml.bind(component));

        return `
            ${MessageListRenderer.renderMessageMeta(component, message)}
            <p class="post-title">${safeSubject}</p>
            ${replyExcerpt ? `<p class="post-excerpt post-excerpt--single-line">${replyExcerpt}</p>` : ''}
        `;
    }

    static renderMessageItem(component, message, options = {}) {
        const { isAdmin = false, renderDeleteButton = null } = options;
        const messageId = message.id;
        const hasValidId = messageId !== null && messageId !== undefined;
        const contentHtml = MessageListRenderer.renderMessageRowContent(component, message);

        const linkHtml = hasValidId ? `
            <a href="/thread/${messageId}"
               class="post-item"
               target="_blank"
               rel="noopener noreferrer"
               title="查看留言">
                <div class="post-content">
                    ${contentHtml}
                </div>
            </a>
        ` : `
            <div class="post-item post-item-block disabled">
                <div class="post-content">
                    ${contentHtml}
                </div>
            </div>
        `;

        if (isAdmin && hasValidId && typeof renderDeleteButton === 'function') {
            return `
                <div class="message-item-row message-item-row--admin">
                    ${linkHtml}
                    ${renderDeleteButton(messageId)}
                </div>
            `;
        }

        return linkHtml;
    }

    static renderMessageList(component, messages, options = {}) {
        const { isAdmin = false, renderDeleteButton = null } = options;

        if (!messages.length) {
            return `
                <div class="post-list">
                    <div class="post-item post-item-block">
                        <div class="post-content">
                            <p class="post-excerpt">暂无留言</p>
                            ${options.emptyHint ? `<p class="post-excerpt post-excerpt--single-line">${component.escapeHtml(options.emptyHint)}</p>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="post-list">
                ${messages.map((message) => MessageListRenderer.renderMessageItem(component, message, {
                    isAdmin,
                    renderDeleteButton,
                })).join('')}
            </div>
        `;
    }

    static getRowStyles() {
        return `
            .post-title {
                font-size: var(--font-size-sm);
                font-weight: 400;
                color: var(--gray-600);
                line-height: 1.6;
            }

            .post-item:not(.post-item-block):hover .post-title,
            .post-item:not(.post-item-block):focus-visible .post-title {
                color: var(--gray-600);
            }

            .post-item:not(.post-item-block) .post-excerpt.post-excerpt--single-line {
                font-size: var(--font-size-xs);
                font-weight: 500;
                color: var(--gray-700);
                line-height: 1.35;
            }

            .post-item:not(.post-item-block):hover .post-excerpt.post-excerpt--single-line,
            .post-item:not(.post-item-block):focus-visible .post-excerpt.post-excerpt--single-line {
                color: var(--interactive-hover-text);
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

            @media (max-width: 768px) {
                .message-item-row .btn-delete-reveal {
                    opacity: 1;
                    pointer-events: auto;
                }
            }
        `;
    }
}
