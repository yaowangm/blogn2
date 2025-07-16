5class RecentMessagesCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const recentMessages = [
            { 
                author: '小明', 
                content: '这个平台真的很棒，界面简洁美观，功能也很实用！', 
                time: '1小时前'
            },
            { 
                author: '小红', 
                content: '希望能增加更多的主题模板，让博客更有个性化。', 
                time: '3小时前'
            },
            { 
                author: '小李', 
                content: '社区氛围很好，大家都很友善，学到了很多。', 
                time: '5小时前'
            },
            { 
                author: '小王', 
                content: '建议增加更多的互动功能，比如点赞、收藏等。', 
                time: '1天前'
            }
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

                .message-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-3);
                }

                .message-item {
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                }

                .message-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: var(--spacing-2);
                }

                .message-author {
                    font-weight: 500;
                    color: var(--gray-900);
                }

                .message-time {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                .message-content {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.5;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近留言</h3>
                </div>
                <div class="card-body">
                    <div class="message-list">
                        ${recentMessages.map(message => `
                            <div class="message-item">
                                <div class="message-header">
                                    <span class="message-author">${message.author}</span>
                                    <span class="message-time">${message.time}</span>
                                </div>
                                <div class="message-content">${message.content}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('recent-messages-card', RecentMessagesCard); 