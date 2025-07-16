class AboutCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
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
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">关于BlogN2</h3>
                </div>
                <div class="card-body">
                    <div class="about-content">
                        <p>
                            <span class="highlight">BlogN2</span> 是一个现代化的博客平台，致力于为创作者提供最佳的写作和分享体验。
                        </p>
                        <p>
                            我们相信每个人都有独特的故事和见解值得分享。无论你是技术专家、生活达人，还是文学爱好者，这里都是你展示才华的理想平台。
                        </p>
                        <p>
                            平台采用最新的Web技术构建，提供流畅的用户体验、强大的内容管理功能，以及丰富的社交互动特性。
                        </p>
                        <p>
                            加入我们，开始你的创作之旅，与志同道合的朋友们一起成长！
                        </p>
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('about-card', AboutCard); 