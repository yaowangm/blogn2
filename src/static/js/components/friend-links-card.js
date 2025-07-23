class FriendLinksCard extends BaseComponent {
    constructor() {
        super();
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const friendLinks = [
            { name: 'GitHub', url: 'https://github.com' },
            { name: 'Stack Overflow', url: 'https://stackoverflow.com' },
            { name: '掘金', url: 'https://juejin.cn' },
            { name: 'CSDN', url: 'https://csdn.net' },
            { name: '博客园', url: 'https://cnblogs.com' },
            { name: '简书', url: 'https://jianshu.com' }
        ];

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

                .friend-links {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: var(--spacing-2);
                }

                .friend-link {
                    padding: var(--spacing-2) var(--spacing-3);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    border-radius: var(--radius-md);
                    text-decoration: none;
                    color: var(--gray-700);
                    font-size: var(--font-size-sm);
                    text-align: center;
                    transition: var(--transition-fast);
                }

                .friend-link:hover {
                    background: var(--primary-color);
                    color: var(--white);
                    border-color: var(--primary-color);
                }

                @media (max-width: 768px) {
                    .friend-links {
                        grid-template-columns: 1fr;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">友情链接</h3>
                </div>
                <div class="card-body">
                    <div class="friend-links">
                        ${friendLinks.map(link => `
                            <a href="${link.url}" class="friend-link" target="_blank" rel="noopener noreferrer">
                                ${link.name}
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('friend-links-card', FriendLinksCard); 