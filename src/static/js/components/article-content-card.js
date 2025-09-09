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
                    grid-template-columns: 1fr;
                    max-width: 400px;
                    margin: 0 auto;
                }
                
                .attachments-grid[data-count="2"] {
                    grid-template-columns: 1fr 1fr;
                    max-width: 600px;
                    margin: 0 auto;
                }
                
                .attachments-grid[data-count="3"] {
                    grid-template-columns: 1fr 1fr 1fr;
                }
                
                .attachments-grid[data-count="4"] {
                    grid-template-columns: 1fr 1fr;
                }
                
                .attachments-grid[data-count="5"] {
                    grid-template-columns: 1fr 1fr 1fr;
                }
                
                .attachments-grid[data-count="6"] {
                    grid-template-columns: 1fr 1fr 1fr;
                }
                
                .attachments-grid[data-count="7"] {
                    grid-template-columns: 1fr 1fr 1fr 1fr;
                }
                
                .attachments-grid[data-count="8"] {
                    grid-template-columns: 1fr 1fr 1fr 1fr;
                }
                
                .attachments-grid[data-count="9"] {
                    grid-template-columns: 1fr 1fr 1fr;
                }
                
                .attachments-grid[data-count="10"] {
                    grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
                }
                
                /* 超过10张图片时使用自适应布局 */
                .attachments-grid[data-count]:not([data-count="1"]):not([data-count="2"]):not([data-count="3"]):not([data-count="4"]):not([data-count="5"]):not([data-count="6"]):not([data-count="7"]):not([data-count="8"]):not([data-count="9"]):not([data-count="10"]) {
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                }
                
                /* 响应式设计 */
                @media (max-width: 768px) {
                    .attachments-grid[data-count="1"] {
                        max-width: 100%;
                    }
                    
                    .attachments-grid[data-count="2"] {
                        max-width: 100%;
                    }
                    
                    .attachments-grid[data-count="3"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="4"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="5"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="6"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="7"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="8"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="9"] {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .attachments-grid[data-count="10"] {
                        grid-template-columns: 1fr 1fr;
                    }
                }
                
                @media (max-width: 480px) {
                    .attachments-grid[data-count="3"],
                    .attachments-grid[data-count="4"],
                    .attachments-grid[data-count="5"],
                    .attachments-grid[data-count="6"],
                    .attachments-grid[data-count="7"],
                    .attachments-grid[data-count="8"],
                    .attachments-grid[data-count="9"],
                    .attachments-grid[data-count="10"] {
                        grid-template-columns: 1fr;
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
                    width: 100%;
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
