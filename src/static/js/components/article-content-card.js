/**
 * 文章内容卡片组件
 * 显示文章的完整内容和可能的图片
 */
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
            // 获取认证token
            const token = localStorage.getItem('access_token');
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(`/api/articles/${this.articleId}`, {
                headers: headers
            });
            if (response.ok) {
                this.articleData = await response.json();
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
            return;
        }

        const { content, attachment, attachments } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-content-card">
                <div class="card-body">
                    <div class="article-content">
                        ${this.formatContent(content)}
                    </div>
                    
                    ${this.renderAllAttachments(attachment, attachments)}
                </div>
            </div>
        `;

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
            
            return safeHtml;
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
     * 安全的HTML过滤，防止XSS攻击
     */
    sanitizeHtml(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }

        // 使用更简单的方法：先清理危险内容，再过滤标签
        let cleanHtml = html;
        
        // 移除危险的脚本和事件
        cleanHtml = cleanHtml.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        cleanHtml = cleanHtml.replace(/on\w+\s*=\s*["'][^"']*["']/gi, '');
        cleanHtml = cleanHtml.replace(/javascript:/gi, '');
        
        // 创建临时DOM元素
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = cleanHtml;
        
        // 允许的HTML标签
        const allowedTags = [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'del', 'strike',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'blockquote', 'pre', 'code',
            'a', 'img',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'hr', 'div', 'span'
        ];

        // 递归过滤节点
        const filterNode = (node) => {
            if (node.nodeType === Node.TEXT_NODE) {
                return node.cloneNode(true);
            }

            if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                // 检查标签是否被允许
                if (!allowedTags.includes(tagName)) {
                    // 如果不允许，返回文本内容
                    return document.createTextNode(node.textContent);
                }

                // 创建新的元素
                const newElement = document.createElement(tagName);

                // 复制安全的属性
                for (const attr of node.attributes) {
                    const attrName = attr.name.toLowerCase();
                    if (['href', 'src', 'alt', 'title', 'class', 'id'].includes(attrName)) {
                        if (attrName === 'href') {
                            const href = attr.value;
                            if (this.isValidUrl(href)) {
                                newElement.setAttribute('href', href);
                                if (href.startsWith('http') && !href.includes(window.location.hostname)) {
                                    newElement.setAttribute('target', '_blank');
                                    newElement.setAttribute('rel', 'noopener noreferrer');
                                }
                            }
                        } else if (attrName === 'src') {
                            const src = attr.value;
                            if (this.isValidImageSrc(src)) {
                                newElement.setAttribute('src', src);
                            }
                        } else {
                            newElement.setAttribute(attrName, this.escapeHtml(attr.value));
                        }
                    }
                }

                // 递归处理子节点
                for (const child of node.childNodes) {
                    const filteredChild = filterNode(child);
                    if (filteredChild) {
                        newElement.appendChild(filteredChild);
                    }
                }

                return newElement;
            }

            return null;
        };

        // 过滤所有子节点
        const filteredNodes = [];
        for (const child of tempDiv.childNodes) {
            const filteredChild = filterNode(child);
            if (filteredChild) {
                filteredNodes.push(filteredChild);
            }
        }

        // 创建新的容器
        const newContainer = document.createElement('div');
        filteredNodes.forEach(node => newContainer.appendChild(node));

        return newContainer.innerHTML;
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

        // 检查是否是图片文件
        const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];
        const isImage = imageExtensions.some(ext => 
            attachment.toLowerCase().endsWith(ext)
        );

        if (isImage) {
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
        
        // 过滤出图片文件
        const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];
        const imageAttachments = attachments.filter(att => 
            imageExtensions.some(ext => att.linkstr.toLowerCase().endsWith(ext))
        );
        
        if (imageAttachments.length === 0) return '';
        
        return `
            <div class="article-attachments">
                <h3>更多图片 (${imageAttachments.length})</h3>
                <div class="attachments-grid" data-count="${imageAttachments.length}">
                    ${imageAttachments.map(att => `
                        <div class="attachment-item">
                            <div class="attachment-image" style="cursor: pointer;">
                                <img src="/upload/${att.linkstr}" 
                                     alt="${this.escapeHtml(att.comment || '图片附件')}" 
                                     loading="lazy"
                                     title="${this.escapeHtml(att.comment || '')}"
                                     data-image-src="/upload/${att.linkstr}" 
                                     data-image-title="${this.escapeHtml(att.comment || '')}">
                            </div>
                            ${att.comment ? `
                                <div class="attachment-comment">
                                    ${this.escapeHtml(att.comment)}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <!-- 图片模态框 -->
            <div class="image-modal" style="display: none;">
                <div class="modal-overlay"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <span class="modal-title"></span>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <img class="modal-image" src="" alt="">
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 设置图片模态框事件监听器
     */
    setupImageModalEvents() {
        // 使用事件委托，为整个容器添加点击事件
        const attachmentsGrid = this.shadowRoot.querySelector('.attachments-grid');
        if (attachmentsGrid) {
            attachmentsGrid.addEventListener('click', (event) => {
                const clickedImage = event.target.closest('.attachment-image img');
                if (clickedImage) {
                    const imageSrc = clickedImage.getAttribute('data-image-src');
                    const imageTitle = clickedImage.getAttribute('data-image-title');
                    this.showImage(imageSrc, imageTitle);
                }
            });
        }
        
        // 为模态框背景添加点击事件
        const modalOverlay = this.shadowRoot.querySelector('.modal-overlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', () => {
                this.hideImage();
            });
        }
        
        // 为关闭按钮添加点击事件
        const closeButton = this.shadowRoot.querySelector('.modal-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.hideImage();
            });
        }
    }

    /**
     * 显示图片模态框
     */
    showImage(imageSrc, title) {
        const modal = this.shadowRoot.querySelector('.image-modal');
        const modalImage = modal.querySelector('.modal-image');
        const modalTitle = modal.querySelector('.modal-title');
        
        modalImage.src = imageSrc;
        modalImage.alt = title || '图片';
        modalTitle.textContent = title || '图片';
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // 防止背景滚动
    }
    
    /**
     * 隐藏图片模态框
     */
    hideImage() {
        const modal = this.shadowRoot.querySelector('.image-modal');
        modal.style.display = 'none';
        document.body.style.overflow = ''; // 恢复背景滚动
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

    /**
     * 处理文本中的链接，安全地转换为可点击的链接
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
                
                .article-content {
                    line-height: 1.8;
                    color: var(--gray-800);
                }
                
                .article-content p {
                    margin-bottom: var(--spacing-4);
                    text-align: justify;
                }
                
                .article-content p:last-child {
                    margin-bottom: 0;
                }

                /* Markdown样式 */
                .article-content h1,
                .article-content h2,
                .article-content h3,
                .article-content h4,
                .article-content h5,
                .article-content h6 {
                    margin-top: var(--spacing-6);
                    margin-bottom: var(--spacing-4);
                    font-weight: 600;
                    line-height: 1.3;
                    color: var(--gray-900);
                }

                .article-content h1 {
                    font-size: var(--font-size-2xl);
                    border-bottom: 2px solid var(--gray-200);
                    padding-bottom: var(--spacing-2);
                }

                .article-content h2 {
                    font-size: var(--font-size-xl);
                    border-bottom: 1px solid var(--gray-200);
                    padding-bottom: var(--spacing-1);
                }

                .article-content h3 {
                    font-size: var(--font-size-lg);
                }

                .article-content h4 {
                    font-size: var(--font-size-base);
                }

                .article-content h5,
                .article-content h6 {
                    font-size: var(--font-size-sm);
                }

                .article-content ul,
                .article-content ol {
                    margin: var(--spacing-4) 0;
                    padding-left: var(--spacing-6);
                }

                .article-content li {
                    margin-bottom: var(--spacing-2);
                }

                .article-content ul li {
                    list-style-type: disc;
                }

                .article-content ol li {
                    list-style-type: decimal;
                }

                .article-content blockquote {
                    margin: var(--spacing-4) 0;
                    padding: var(--spacing-4) var(--spacing-5);
                    border-left: 4px solid var(--primary-color);
                    background-color: var(--gray-50);
                    color: var(--gray-700);
                    font-style: italic;
                }

                .article-content blockquote p {
                    margin-bottom: 0;
                }

                .article-content code {
                    background-color: var(--gray-100);
                    color: var(--gray-800);
                    padding: 2px 4px;
                    border-radius: var(--radius-sm);
                    font-family: 'Consolas', 'Monaco', 'Menlo', 'Ubuntu Mono', 'Courier New', monospace;
                    font-size: 0.9em;
                }

                .article-content pre {
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

                .article-content pre code {
                    background-color: transparent;
                    color: inherit;
                    padding: 0;
                    border-radius: 0;
                }

                .article-content table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: var(--spacing-4) 0;
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    overflow: hidden;
                }

                .article-content th,
                .article-content td {
                    padding: var(--spacing-3);
                    text-align: left;
                    border-bottom: 1px solid var(--gray-200);
                }

                .article-content th {
                    background-color: var(--gray-50);
                    font-weight: 600;
                    color: var(--gray-900);
                }

                .article-content tr:last-child td {
                    border-bottom: none;
                }

                .article-content hr {
                    border: none;
                    height: 1px;
                    background-color: var(--gray-200);
                    margin: var(--spacing-6) 0;
                }

                .article-content a {
                    color: var(--primary-color);
                    text-decoration: none;
                    transition: color var(--transition-fast);
                }

                .article-content a:hover {
                    color: var(--primary-hover);
                    text-decoration: underline;
                }

                .article-content img {
                    max-width: 100%;
                    height: auto;
                    border-radius: var(--radius-md);
                    margin: var(--spacing-4) 0;
                    box-shadow: var(--shadow-sm);
                }

                .article-content strong,
                .article-content b {
                    font-weight: 600;
                }

                .article-content em,
                .article-content i {
                    font-style: italic;
                }

                .article-content del,
                .article-content s {
                    text-decoration: line-through;
                    color: var(--gray-500);
                }
                
                .article-attachment {
                    margin-top: var(--spacing-8);
                    padding-top: var(--spacing-6);
                    border-top: 1px solid var(--gray-200);
                }
                
                .article-attachment h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-4);
                }
                
                .attachment-image img {
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

                .article-attachments {
                    margin-top: var(--spacing-8);
                    padding-top: var(--spacing-6);
                    border-top: 1px solid var(--gray-200);
                }
                
                .article-attachments h3 {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-700);
                    margin-bottom: var(--spacing-4);
                }
                
                .attachments-grid {
                    display: grid;
                    gap: var(--spacing-4);
                    margin-bottom: var(--spacing-4);
                }
                
                /* 根据图片数量设置不同的网格布局 */
                .attachments-grid[data-count="1"] {
                    grid-template-columns: 200px;
                    justify-content: start;
                }
                
                .attachments-grid[data-count="2"] {
                    grid-template-columns: 200px 200px;
                    justify-content: start;
                }
                
                .attachments-grid[data-count="3"] {
                    grid-template-columns: 200px 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="4"] {
                    grid-template-columns: 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="5"] {
                    grid-template-columns: 200px 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="6"] {
                    grid-template-columns: 200px 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="7"] {
                    grid-template-columns: 200px 200px 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="8"] {
                    grid-template-columns: 200px 200px 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="9"] {
                    grid-template-columns: 200px 200px 200px;
                    justify-content: center;
                }
                
                .attachments-grid[data-count="10"] {
                    grid-template-columns: 200px 200px 200px 200px 200px;
                    justify-content: center;
                }
                
                /* 超过10张图片时使用自适应布局 */
                .attachments-grid[data-count]:not([data-count="1"]):not([data-count="2"]):not([data-count="3"]):not([data-count="4"]):not([data-count="5"]):not([data-count="6"]):not([data-count="7"]):not([data-count="8"]):not([data-count="9"]):not([data-count="10"]) {
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                }
                
                /* 响应式设计 */
                @media (max-width: 768px) {
                    .attachments-grid[data-count="1"] {
                        grid-template-columns: 200px;
                    }
                    
                    .attachments-grid[data-count="2"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="3"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="4"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="5"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="6"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="7"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="8"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="9"] {
                        grid-template-columns: 200px 200px;
                    }
                    
                    .attachments-grid[data-count="10"] {
                        grid-template-columns: 200px 200px;
                    }
                }
                
                @media (max-width: 480px) {
                    .attachments-grid[data-count="1"] {
                        grid-template-columns: 200px;
                    }
                    
                    .attachments-grid[data-count="2"] {
                        grid-template-columns: 200px;
                    }
                    
                    .attachments-grid[data-count="3"],
                    .attachments-grid[data-count="4"],
                    .attachments-grid[data-count="5"],
                    .attachments-grid[data-count="6"],
                    .attachments-grid[data-count="7"],
                    .attachments-grid[data-count="8"],
                    .attachments-grid[data-count="9"],
                    .attachments-grid[data-count="10"] {
                        grid-template-columns: 200px;
                    }
                }
                
                .attachment-item {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-2);
                }
                
                .attachment-item .attachment-image {
                    position: relative;
                    overflow: hidden;
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-md);
                    transition: transform var(--transition-fast);
                }
                
                .attachment-item .attachment-image:hover {
                    transform: scale(1.02);
                }
                
                .attachment-item .attachment-image img {
                    width: 200px;
                    height: 200px;
                    object-fit: cover;
                    display: block;
                }
                
                .attachment-comment {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    text-align: center;
                    padding: var(--spacing-2);
                    background-color: var(--gray-50);
                    border-radius: var(--radius-md);
                    border: 1px solid var(--gray-200);
                }

                /* 图片模态框样式 */
                .image-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 10000;
                    display: none;
                }
                
                .modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.8);
                    cursor: pointer;
                }
                
                .modal-content {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background-color: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-xl);
                    max-width: 90%;
                    max-height: 90%;
                    overflow: hidden;
                }
                
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: var(--spacing-4);
                    border-bottom: 1px solid var(--gray-200);
                    background-color: var(--gray-50);
                }
                
                .modal-title {
                    font-weight: 600;
                    color: var(--gray-800);
                    font-size: var(--font-size-lg);
                }
                
                .modal-close {
                    background: none;
                    border: none;
                    font-size: var(--font-size-xl);
                    color: var(--gray-500);
                    cursor: pointer;
                    padding: var(--spacing-1);
                    border-radius: var(--radius-sm);
                    transition: color var(--transition-fast);
                }
                
                .modal-close:hover {
                    color: var(--gray-700);
                }
                
                .modal-body {
                    padding: var(--spacing-4);
                    text-align: center;
                }
                
                .modal-image {
                    max-width: 100%;
                    max-height: 70vh;
                    height: auto;
                    border-radius: var(--radius-md);
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
