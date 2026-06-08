class AboutCard extends BaseComponent {
    constructor() {
        super();
    }

    connectedCallback() {
        this.render();
        this.loadAboutContent();
    }

    /**
     * 加载关于页面内容
     */
    async loadAboutContent() {
        try {
            const response = await fetch('/api/blogs/about');
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
                let linkHtml = '';
                
                if (i === paragraphElements.length - 1 && data.link) {
                    // 处理链接，支持http、https协议和相对路径
                    const safeLink = this.escapeHtml(data.link);
                    let finalLink = safeLink;
                    
                    // 如果是旧的projectitem链接，转换为新的article链接
                    if (safeLink.startsWith('/projectitem/')) {
                        finalLink = safeLink.replace('/projectitem/', '/article/');
                    }
                    
                    if (safeLink.startsWith('http://') || safeLink.startsWith('https://') || safeLink.startsWith('/')) {
                        linkHtml = ` <a href="${finalLink}" class="read-more" target="_blank" rel="noopener noreferrer">查看详情</a>`;
                    }
                }
                
                // 安全处理段落内容，但不转义链接HTML
                const safeParagraph = this.escapeHtml(paragraph);
                contentHtml += `<p>${safeParagraph}${linkHtml}</p>`;
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
                @import url('/static/css/common-components.css');

                .card-body {
                    padding: calc(var(--spacing-3) + 5px) calc(var(--spacing-4) + 5px);
                }

                :host {
                    display: block;
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