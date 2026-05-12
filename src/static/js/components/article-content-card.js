/**
 * 文章内容卡片组件 (ArticleContentCard)
 * 
 * 负责显示文章的完整内容，包括：
 * - Markdown内容的解析和渲染
 * - 单张图片附件的显示
 * - 多张图片附件的网格布局和模态框预览
 * - 安全的HTML内容过滤
 * - 响应式图片布局
 * 
 * 继承自BaseComponent，使用统一的工具方法。
 */

const ARTICLE_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];

/** 附件文件名是否为支持的图片类型 */
function isArticleImagePath(path) {
    const lower = String(path || '').toLowerCase();
    return ARTICLE_IMAGE_EXTENSIONS.some(ext => lower.endsWith(ext));
}

class ArticleContentCard extends BaseComponent {
    constructor() {
        super();
        this.articleId = null;
        this.articleData = null;
    }

    async connectedCallback() {
        // 从URL获取文章ID，或者从属性获取
        this.articleId = this.getArticleIdFromUrl() || this.getAttribute('article-id');
        if (!this.articleId) {
            this.showError('无法获取文章ID');
            return;
        }

        // 加载文章数据
        await this.loadArticleData();
        
        // 渲染组件
        this.render();
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
            const articleData = await BaseComponent.getArticle(this.articleId);
            if (articleData === null) {
                window.location.href = '/static/error.html';
                return;
            }
            this.articleData = articleData;
        } catch (error) {
            this.logError('Failed to load article data', error);
            window.location.href = '/static/error.html';
        }
    }

    /**
     * 渲染组件
     */
    render() {
        if (!this.articleData) {
            this.shadowRoot.innerHTML = `
                <div class="card article-content-card">
                    <div class="card-body">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            `;
            // 在设置 innerHTML 之后添加样式
            this.addStyles();
            return;
        }

        const { content, attachment, attachments } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-content-card">
                <div class="card-body">
                    <div class="article-content markdown-content">
                        ${this.formatContent(content)}
                    </div>
                    
                    ${this.renderAllAttachments(attachment, attachments)}
                </div>
            </div>
        `;
        
        // 在设置 innerHTML 之后添加样式
        this.addStyles();
        
        // 设置图片模态框事件监听器
        this.setupImageModalEvents();
    }

    /**
     * 格式化文章内容
     */
    formatContent(content) {
        if (!content) {
            return '<p class="no-content">暂无内容</p>';
        }

        try {
            // 检查marked.js是否可用
            const markedParser = typeof marked !== 'undefined' ? marked : window.marked;
            if (!markedParser) {
                console.warn('marked.js not available, using fallback formatting');
                return this.formatContentFallback(content);
            }

            // 配置marked.js选项（与预览功能保持一致）
            const options = {
                breaks: true,  // 支持换行符
                gfm: true,     // 启用GitHub风格的Markdown
                pedantic: false
            };
            
            // 使用marked.js解析Markdown
            const html = markedParser.parse(content, options);
            
            // 对解析后的HTML进行安全过滤
            const safeHtml = this.sanitizeHtml(html);
            
            // 处理文本中的链接（包括ed2k等非标准协议），采用DOM遍历避免破坏HTML结构
            const processedHtml = this.processTextWithLinks(safeHtml);
            
            return processedHtml;
        } catch (error) {
            this.logError('Markdown parsing failed', error);
            // 如果Markdown解析失败，回退到原始文本处理
            return this.formatContentFallback(content);
        }
    }

    /**
     * 回退的内容格式化方法（当Markdown解析失败时使用）
     */
    formatContentFallback(content) {
        // 首先对内容进行HTML转义，防止XSS攻击
        const escapedContent = this.escapeHtml(content);

        // 将换行符转换为HTML段落
        const paragraphs = escapedContent.split(/\r?\n/).filter(p => p.trim());
        
        if (paragraphs.length === 0) {
            return '<p class="no-content">暂无内容</p>';
        }

        return paragraphs.map(p => `<p>${this.processTextWithLinks(p)}</p>`).join('');
    }



    /**
     * 渲染所有附件（单张图片 + 多张图片）
     */
    renderAllAttachments(attachment, attachments) {
        let html = '';
        
        // 渲染单张图片附件（如果存在）
        if (attachment) {
            html += this.renderSingleAttachment(attachment);
        }
        
        // 渲染多张图片附件（如果存在）
        if (attachments && attachments.length > 0) {
            html += this.renderMultipleAttachments(attachments);
        }
        
        return html;
    }
    
    /**
     * 渲染单张图片附件
     */
    renderSingleAttachment(attachment) {
        if (!attachment) return '';

        if (isArticleImagePath(attachment)) {
            return `
                <div class="article-attachment">
                    <h3>附件图片</h3>
                    <div class="attachment-image">
                        <img src="/upload/${attachment}" alt="文章附件" loading="lazy">
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="article-attachment">
                    <h3>附件</h3>
                    <div class="attachment-file">
                        <a href="/upload/${attachment}" target="_blank" class="attachment-link">
                            📎 ${attachment}
                        </a>
                    </div>
                </div>
            `;
        }
    }
    
    /**
     * 渲染多张图片附件
     */
    renderMultipleAttachments(attachments) {
        if (!attachments || attachments.length === 0) return '';
        
        const imageAttachments = attachments.filter(att => isArticleImagePath(att.linkstr));
        
        if (imageAttachments.length === 0) return '';
        
        return `
            <div class="article-attachments">
                <h3>更多图片 (${imageAttachments.length})</h3>
                <div class="attachments-grid">
                    ${imageAttachments.map(att => {
                        const caption = att.comment ? this.escapeHtml(att.comment) : '';
                        const captionForAttr = this.escapeHtml(att.comment || '');
                        return `
                        <div class="attachment-item"
                             data-image-src="/upload/${att.linkstr}"
                             data-image-title="${captionForAttr}">
                            <div class="attachment-image">
                                <img src="/upload/${att.linkstr}" 
                                     alt="${this.escapeHtml(att.comment || '图片附件')}" 
                                     loading="lazy"
                                     title="${captionForAttr}">
                            </div>
                            <div class="attachment-comment">
                                ${caption || '<span class="attachment-comment-placeholder">暂无注释</span>'}
                            </div>
                        </div>
                    `;
                    }).join('')}
                </div>
            </div>
            
            <!-- 大图预览 lightbox -->
            <div class="image-modal" style="display: none;">
                <div class="modal-overlay"></div>
                <div class="modal-lightbox-card" role="dialog" aria-modal="true" aria-label="图片预览">
                    <div class="modal-lightbox-media">
                        <img class="modal-image" src="" alt="">
                    </div>
                    <div class="modal-lightbox-footer">
                        <div class="modal-lightbox-footer-inner">
                            <div class="modal-lightbox-caption"></div>
                            <button type="button" class="modal-close" aria-label="关闭"></button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 设置图片模态框事件监听器
     */
    setupImageModalEvents() {
        const attachmentsGrid = this.shadowRoot.querySelector('.attachments-grid');
        if (attachmentsGrid) {
            attachmentsGrid.addEventListener('click', (event) => {
                const item = event.target.closest('.attachment-item');
                if (!item) return;
                const imageSrc = item.getAttribute('data-image-src');
                if (!imageSrc) return;
                const imageTitle = item.getAttribute('data-image-title');
                this.showImage(imageSrc, imageTitle);
            });
        }

        const modal = this.getImageModal();
        if (!modal) return;

        modal.querySelector('.modal-overlay')?.addEventListener('click', () => this.hideImage());
        modal.querySelector('.modal-close')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.hideImage();
        });
    }

    /** @returns {HTMLElement | null} */
    getImageModal() {
        return this.shadowRoot.querySelector('.image-modal');
    }

    /**
     * 显示图片模态框
     */
    showImage(imageSrc, title) {
        const modal = this.getImageModal();
        if (!modal) return;
        const modalImage = modal.querySelector('.modal-image');
        const captionEl = modal.querySelector('.modal-lightbox-caption');
        const label = (title || '').trim();

        modalImage.src = imageSrc;
        modalImage.alt = label || '图片';
        if (label) {
            captionEl.textContent = label;
        } else {
            captionEl.innerHTML = '<span class="attachment-comment-placeholder">暂无注释</span>';
        }

        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // 防止背景滚动
    }
    
    /**
     * 隐藏图片模态框
     */
    hideImage() {
        const modal = this.getImageModal();
        if (modal) modal.style.display = 'none';
        document.body.style.overflow = ''; /* 恢复背景滚动 */
    }


    /**
     * 处理文本中的链接，安全地转换为可点击的链接
     */

    processTextWithLinks(htmlOrText) {
        if (!htmlOrText || typeof htmlOrText !== 'string') {
            return '';
        }
        // 通用URL正则，匹配 aaa://...
        const urlRegex = /([a-zA-Z][a-zA-Z0-9+.-]*:\/\/[\w\-._~:/?#\[\]@!$&'()*+,;=%]+)/g;
        // 用于测试的正则（无全局标志，避免 lastIndex 状态问题）
        const urlTestRegex = /[a-zA-Z][a-zA-Z0-9+.-]*:\/\/[\w\-._~:/?#\[\]@!$&'()*+,;=%]+/;

        // 使用DOM解析，避免正则直接切分HTML导致结构损坏
        const container = document.createElement('div');
        container.innerHTML = htmlOrText;

        const SKIP_TAGS = new Set(['A', 'CODE', 'PRE', 'SCRIPT', 'STYLE']);

        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
            acceptNode: (node) => {
                const parent = node.parentNode;
                if (!parent) return NodeFilter.FILTER_REJECT;
                let el = parent;
                while (el && el.nodeType === 1) {
                    if (SKIP_TAGS.has(el.nodeName)) return NodeFilter.FILTER_REJECT;
                    el = el.parentNode;
                }
                // 使用无全局标志的正则进行测试，避免 lastIndex 状态问题
                return urlTestRegex.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
            }
        });

        const nodes = [];
        let n;
        while ((n = walker.nextNode())) nodes.push(n);

        for (const textNode of nodes) {
            const text = textNode.nodeValue;
            const parts = [];
            let lastIndex = 0;
            text.replace(urlRegex, (match, url, offset) => {
                if (offset > lastIndex) parts.push(document.createTextNode(text.slice(lastIndex, offset)));
                try {
                    if (this.isValidUrl(url)) {
                        const a = document.createElement('a');
                        a.href = url;
                        a.target = '_blank';
                        a.rel = 'noopener noreferrer';
                        a.className = 'auto-link';
                        a.textContent = url;
                        parts.push(a);
                    } else {
                        parts.push(document.createTextNode(url));
                    }
                } catch (_) {
                    parts.push(document.createTextNode(url));
                }
                lastIndex = offset + match.length;
                return match;
            });
            if (lastIndex < text.length) parts.push(document.createTextNode(text.slice(lastIndex)));

            const parent = textNode.parentNode;
            if (parent) {
                for (const part of parts) parent.insertBefore(part, textNode);
                parent.removeChild(textNode);
            }
        }

        return container.innerHTML;
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        this.shadowRoot.innerHTML = `
            <div class="card article-content-card">
                <div class="card-body">
                    <div class="error-message">${message}</div>
                </div>
            </div>
        `;
        this.addStyles();
    }

    /**
     * 添加样式
     */
    addStyles() {
        if (!this.shadowRoot.querySelector('style')) {
            const style = document.createElement('style');
            style.textContent = `
                @import url('/static/css/common-components.css');
                @import url('/static/css/components.css');
                .card { margin-bottom: 0; }
                
                :host {
                    display: block;
                    max-width: 100%;
                    min-width: 0;
                }
                
                .article-content {
                    line-height: 1.8;
                    word-wrap: break-word;
                    overflow-wrap: anywhere; /* 允许在任意位置换行，避免超长连续字符撑破布局 */
                    word-break: break-word;   /* 在必要时对长单词/连续字符串进行断行 */
                    max-width: 100%;
                }
                /* 对所有后代启用任意位置换行，兜底避免极端长串文本导致变形 */
                .article-content * {
                    overflow-wrap: anywhere;
                    word-break: break-word;
                }
                
                .article-content a {
                    word-break: break-all;    /* 链接内优先允许任意断行 */
                    overflow-wrap: anywhere;
                    max-width: 100%;
                    display: inline-block;
                }
                
                .article-content p {
                    text-align: justify;
                }
                
                /* 代码块样式修复 - 防止变形并添加滚动条；移动端用 100% 避免向右溢出 */
                .markdown-content pre {
                    overflow-x: auto !important;
                    overflow-y: hidden !important;
                    white-space: pre !important;
                    word-wrap: normal !important;
                    word-break: normal !important;
                    max-width: min(700px, 100%) !important;
                    box-sizing: border-box !important;
                }
                
                .markdown-content pre code {
                    white-space: pre !important;
                    word-wrap: normal !important;
                    word-break: normal !important;
                    display: block !important;
                    overflow-x: auto !important;
                    max-width: 100% !important;
                }
                
                /* Markdown 表格在移动端不撑破布局，横向滚动 */
                .markdown-content table {
                    display: block !important;
                    max-width: 100% !important;
                    overflow-x: auto !important;
                }
                .markdown-content thead,
                .markdown-content tbody {
                    display: table-row-group;
                }
                .markdown-content tr {
                    display: table-row;
                }
                .markdown-content th,
                .markdown-content td {
                    display: table-cell;
                }
                
                .article-attachment,
                .article-attachments {
                    margin-top: var(--spacing-8);
                    padding-top: var(--spacing-6);
                    border-top: 1px solid var(--gray-200);
                }
                
                .article-attachment h3,
                .article-attachments h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-4);
                }
                
                .article-attachment .attachment-image img {
                    max-width: 100%;
                    height: auto;
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-md);
                }
                
                .attachment-file {
                    padding: var(--spacing-4);
                    background-color: var(--gray-50);
                    border-radius: var(--radius-lg);
                    border: 1px solid var(--gray-200);
                }
                
                .attachment-link {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                    transition: color var(--transition-fast);
                }
                
                .attachment-link:hover {
                    color: var(--primary-hover);
                    text-decoration: underline;
                }

                .article-attachments h3 {
                    text-align: left;
                }
                
                .attachments-grid {
                    display: grid;
                    justify-content: start;
                    grid-template-columns: repeat(auto-fit, minmax(min(100%, 11rem), 1fr));
                    gap: var(--spacing-2);
                    margin-bottom: var(--spacing-4);
                    width: 100%;
                }
                
                .attachments-grid:has(> .attachment-item:only-child) {
                    grid-template-columns: min(22rem, 100%);
                }
                
                .attachment-item {
                    display: flex;
                    flex-direction: column;
                    min-width: 0;
                    cursor: pointer;
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-lg);
                    background: var(--white);
                    overflow: hidden;
                    box-shadow: var(--shadow-sm);
                    transition: box-shadow var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast);
                }
                
                .attachment-item:hover {
                    box-shadow: var(--shadow-md);
                    border-color: var(--gray-300);
                    transform: translateY(-2px);
                }
                
                .attachment-item .attachment-image {
                    position: relative;
                    width: 100%;
                    aspect-ratio: 1;
                    overflow: hidden;
                    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
                    box-shadow: none;
                }
                
                .attachment-item .attachment-image img {
                    position: absolute;
                    inset: 0;
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                    border-radius: 0;
                    box-shadow: none;
                }
                
                .attachment-comment,
                .modal-lightbox-footer-inner {
                    box-sizing: border-box;
                    padding: var(--spacing-2) var(--spacing-3);
                    text-align: left;
                }
                
                .attachment-comment,
                .modal-lightbox-footer {
                    background-color: var(--gray-50);
                    border-top: 1px solid var(--gray-200);
                    min-height: 2.75rem;
                }
                
                .attachment-comment {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.45;
                }
                
                .attachment-comment-placeholder {
                    color: var(--gray-400);
                    font-style: italic;
                }

                /* lightbox：flex 居中卡片；图区固定高度 + object-fit:cover 铺满，避免 contain 与百分比宽度循环留白 */
                .image-modal {
                    position: fixed;
                    inset: 0;
                    z-index: 10000;
                    display: none;
                    box-sizing: border-box;
                    align-items: center;
                    justify-content: center;
                    padding: 0 var(--spacing-6);
                }
                
                .modal-overlay {
                    position: absolute;
                    inset: 0;
                    background-color: rgba(0, 0, 0, 0.8);
                    cursor: pointer;
                    z-index: 0;
                }
                
                .modal-lightbox-card {
                    position: relative;
                    z-index: 1;
                    flex: 0 1 auto;
                    display: flex;
                    flex-direction: column;
                    align-items: stretch;
                    min-width: 0;
                    max-width: 100%;
                    width: max-content;
                    border: none;
                    border-radius: var(--radius-lg);
                    background: var(--white);
                    overflow: hidden;
                    box-shadow: var(--shadow-xl);
                    box-sizing: border-box;
                }
                
                .modal-lightbox-media {
                    display: block;
                    width: 100%;
                    height: min(70vh, 85vh);
                    overflow: hidden;
                    line-height: 0;
                    background-color: var(--white);
                }
                
                .modal-lightbox-card .modal-image {
                    display: block;
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    object-fit: cover;
                    object-position: center;
                    border-radius: 0;
                    box-shadow: none;
                }
                
                .modal-lightbox-footer {
                    flex-shrink: 0;
                    box-sizing: border-box;
                    width: 100%;
                }
                
                .modal-lightbox-footer-inner {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    min-width: 0;
                    font-family: inherit;
                    font-size: var(--font-size-base);
                    line-height: 1.8;
                    color: var(--gray-800);
                }
                
                .modal-lightbox-caption {
                    flex: 1;
                    min-width: 0;
                    margin: 0;
                    overflow-wrap: anywhere;
                    word-break: break-word;
                }
                
                .modal-lightbox-footer .modal-close {
                    flex-shrink: 0;
                    position: relative;
                    box-sizing: border-box;
                    width: 2rem;
                    height: 2rem;
                    margin: 0;
                    padding: 0;
                    border: none;
                    border-radius: 50%;
                    font-size: 0;
                    line-height: 0;
                    color: transparent;
                    cursor: pointer;
                    background-color: var(--error-color, #ef4444);
                    -webkit-appearance: none;
                    appearance: none;
                    transition: background-color var(--transition-fast);
                }
                
                .modal-lightbox-footer .modal-close::before,
                .modal-lightbox-footer .modal-close::after {
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 0.7rem;
                    height: 2px;
                    background-color: var(--white, #fff);
                    border-radius: 1px;
                }
                
                .modal-lightbox-footer .modal-close::before {
                    transform: translate(-50%, -50%) rotate(45deg);
                }
                
                .modal-lightbox-footer .modal-close::after {
                    transform: translate(-50%, -50%) rotate(-45deg);
                }
                
                .modal-lightbox-footer .modal-close:hover {
                    background-color: #dc2626;
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
customElements.define('article-content-card', ArticleContentCard);
