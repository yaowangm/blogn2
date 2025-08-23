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
            const response = await fetch(`/api/articles/${this.articleId}`);
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

        const { content, attachment } = this.articleData;

        this.shadowRoot.innerHTML = `
            <div class="card article-content-card">
                <div class="card-body">
                    <div class="article-content">
                        ${this.formatContent(content)}
                    </div>
                    
                    ${attachment ? this.renderAttachment(attachment) : ''}
                </div>
            </div>
        `;

        this.addStyles();
    }

    /**
     * 格式化文章内容
     */
    formatContent(content) {
        if (!content) {
            return '<p class="no-content">暂无内容</p>';
        }

        // 将换行符转换为HTML段落
        const paragraphs = content.split(/\r?\n/).filter(p => p.trim());
        
        if (paragraphs.length === 0) {
            return '<p class="no-content">暂无内容</p>';
        }

        return paragraphs.map(p => `<p>${this.processTextWithLinks(p)}</p>`).join('');
    }

    /**
     * 渲染附件
     */
    renderAttachment(attachment) {
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
    processTextWithLinks(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }

        // 安全的URL正则表达式，只匹配http/https链接
        const urlRegex = /(https?:\/\/[^\s<>"']+)/gi;
        
        return text.replace(urlRegex, (url) => {
            // 验证URL格式
            try {
                const urlObj = new URL(url);
                // 只允许http和https协议
                if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
                    return this.escapeHtml(url);
                }
                
                // 转义URL中的特殊字符
                const safeUrl = this.escapeHtml(url);
                const displayUrl = this.escapeHtml(url);
                
                return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="auto-link">${displayUrl}</a>`;
            } catch (error) {
                // 如果URL无效，只转义显示
                return this.escapeHtml(url);
            }
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
                :host {
                    display: block;
                    font-family: var(--font-family);
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-xl);
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    margin-bottom: var(--spacing-6);
                }

                .card-body {
                    padding: var(--spacing-6);
                }
                
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
                
                .no-content {
                    color: var(--gray-500);
                    font-style: italic;
                    text-align: center;
                    padding: var(--spacing-8);
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
