class AboutCard extends BaseComponent {
    constructor() {
        super();
    }

    connectedCallback() {
        this.render();
        this.loadContent();
    }

    /**
     * 加载关于页面内容
     */
    async loadAboutContent() {
        try {
            const response = await fetch('/api/about');
            if (!response.ok) {
                throw new Error('Failed to fetch about content');
            }
            const data = await response.json();
            this.updateContent(data);
        } catch (error) {
            this.logError('Error loading about content', error);
            this.showError();
        }
    }

    /**
     * HTML转义函数，防止XSS攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的安全文本
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    updateContent(data) {
        const cardTitle = this.shadowRoot.querySelector('.card-title');
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardTitle) {
            // 安全处理标题
            const safeTitle = this.escapeHtml(data.title || 'Why Blogn');
            cardTitle.textContent = safeTitle;
        }
        
        if (cardBody) {
            let content = data.content || '内容暂不可用';
            
            // 将<br>标签分割成多个段落
            const paragraphs = content.split('<br>');
            const paragraphElements = paragraphs.map(p => p.trim()).filter(p => p.length > 0);
            
            // 如果有链接，在最后一个段落后添加链接
            let contentHtml = '';
            for (let i = 0; i < paragraphElements.length; i++) {
                let paragraph = paragraphElements[i];
                if (i === paragraphElements.length - 1 && data.link) {
                    // 安全处理链接，只允许http和https协议
                    const safeLink = this.escapeHtml(data.link);
                    if (safeLink.startsWith('http://') || safeLink.startsWith('https://')) {
                        paragraph += ` <a href="${safeLink}" class="read-more">查看详情</a>`;
                    }
                }
                // 安全处理段落内容
                const safeParagraph = this.escapeHtml(paragraph);
                contentHtml += `<p>${safeParagraph}</p>`;
            }
            
            cardBody.innerHTML = `
                <div class="about-content">
                    ${contentHtml}
                </div>
            `;
        }
    }

    showError() {
        const cardTitle = this.shadowRoot.querySelector('.card-title');
        const cardBody = this.shadowRoot.querySelector('.card-body');
        
        if (cardTitle) {
            cardTitle.textContent = 'Why Blogn';
        }
        
        if (cardBody) {
            cardBody.innerHTML = this.createErrorHTML('内容加载失败，请稍后重试。');
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .card {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--gray-200);
                    overflow: hidden;
                    transition: var(--transition-normal);
                }

                .card:hover {
                    box-shadow: var(--shadow-md);
                    transform: translateY(-2px);
                }

                .card-header {
                    padding: var(--spacing-4) var(--spacing-5);
                    border-bottom: 1px solid var(--gray-200);
                    background: var(--gray-50);
                }

                .card-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin: 0;
                }

                .card-body {
                    padding: var(--spacing-5);
                }

                .about-content {
                    line-height: 1.7;
                    color: var(--gray-700);
                }

                .about-content p {
                    margin-bottom: var(--spacing-4);
                }

                .about-content p:last-child {
                    margin-bottom: 0;
                }

                .highlight {
                    color: var(--primary-color);
                    font-weight: 500;
                }

                .read-more {
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                    margin-left: var(--spacing-2);
                }

                .read-more:hover {
                    text-decoration: underline;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Why Blogn</h3>
                </div>
                <div class="card-body">
                    <div class="about-content">
                        <p>正在加载内容...</p>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('about-card', AboutCard); 