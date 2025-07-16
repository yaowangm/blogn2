class RecentCommentsCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const recentComments = [
            { 
                author: '张三', 
                content: '这篇文章写得很好，对我很有帮助！', 
                time: '2小时前',
                post: '如何提高编程效率'
            },
            { 
                author: '李四', 
                content: '感谢分享，学到了很多新知识。', 
                time: '4小时前',
                post: 'Python异步编程实践'
            },
            { 
                author: '王五', 
                content: '这个观点很独特，值得深入思考。', 
                time: '6小时前',
                post: '现代Web开发趋势'
            },
            { 
                author: '赵六', 
                content: '期待更多相关内容！', 
                time: '1天前',
                post: 'React性能优化技巧'
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

                .comment-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-3);
                }

                .comment-item {
                    padding: var(--spacing-3);
                    border-radius: var(--radius-md);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                }

                .comment-header {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                    margin-bottom: var(--spacing-2);
                }

                .comment-author {
                    font-weight: 500;
                    color: var(--gray-900);
                }

                .comment-time {
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                .comment-post {
                    font-size: var(--font-size-sm);
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-2);
                }

                .comment-content {
                    font-size: var(--font-size-sm);
                    color: var(--gray-700);
                    line-height: 1.5;
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最近评论</h3>
                </div>
                <div class="card-body">
                    <div class="comment-list">
                        ${recentComments.map(comment => `
                            <div class="comment-item">
                                <div class="comment-header">
                                    <span class="comment-author">${comment.author}</span>
                                    <span class="comment-time">${comment.time}</span>
                                </div>
                                <div class="comment-post">评论于：${comment.post}</div>
                                <div class="comment-content">${comment.content}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('recent-comments-card', RecentCommentsCard); 