class FooterComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const currentYear = new Date().getFullYear();

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    background: var(--white);
                    color: var(--gray-600);
                    padding: var(--spacing-8) 0;
                    margin-top: auto;
                    border-top: 1px solid var(--gray-200);
                }

                .footer-container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 var(--spacing-4);
                    text-align: center;
                }

                .footer-content {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: var(--spacing-4);
                }

                .footer-logo {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    color: var(--gray-900);
                    text-decoration: none;
                }

                .footer-logo:hover {
                    color: var(--primary-color);
                }

                .logo-icon {
                    width: 24px;
                    height: 24px;
                    background: var(--primary-color);
                    border-radius: var(--radius-md);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--white);
                    font-weight: 700;
                    font-size: var(--font-size-sm);
                }

                .logo-text {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                }

                .footer-copyright {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                @media (max-width: 768px) {
                    .footer-container {
                        padding: 0 var(--spacing-3);
                    }
                }

                @media (max-width: 480px) {
                    .footer-container {
                        padding: 0 var(--spacing-2);
                    }
                }
            </style>

            <div class="footer-container">
                <div class="footer-content">
                    <a href="/" class="footer-logo">
                        <div class="logo-icon">B</div>
                        <span class="logo-text">BlogN2</span>
                    </a>
                    <div class="footer-copyright">
                        © ${currentYear} BlogN2. 保留所有权利。
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('footer-component', FooterComponent); 