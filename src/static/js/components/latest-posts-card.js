class LatestPostsCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const latestPosts = [
            {
                title: '如何提高编程效率：10个实用技巧',
                author: '技术探索者',
                date: '2024-01-15',
                excerpt: '在快节奏的软件开发环境中，提高编程效率是每个开发者都追求的目标。本文将分享10个经过实践验证的技巧...',
                image: '💻'
            },
            {
                title: 'Python异步编程实践指南',
                author: '编程之道',
                date: '2024-01-14',
                excerpt: '异步编程是现代Python开发中不可或缺的技能。本文将从基础概念开始，逐步深入异步编程的实践应用...',
                image: '🐍'
            },
            {
                title: '现代Web开发趋势分析',
                author: '前端达人',
                date: '2024-01-13',
                excerpt: 'Web开发技术日新月异，本文将分析当前最热门的技术趋势，包括框架选择、性能优化、用户体验等方面...',
                image: '🌐'
            },
            {
                title: 'React性能优化技巧详解',
                author: 'React专家',
                date: '2024-01-12',
                excerpt: 'React应用性能优化是一个复杂的话题。本文将详细介绍各种优化技巧，从组件设计到状态管理...',
                image: '⚛️'
            },
            {
                title: '摄影构图的艺术与科学',
                author: '摄影艺术',
                date: '2024-01-11',
                excerpt: '好的构图是优秀摄影作品的基础。本文将探讨构图的基本原则和高级技巧，帮助你拍出更好的照片...',
                image: '📷'
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

                .post-list {
                    display: flex;
                    flex-direction: column;
                    gap: var(--spacing-4);
                }

                .post-item {
                    display: flex;
                    gap: var(--spacing-4);
                    padding: var(--spacing-4);
                    border-radius: var(--radius-lg);
                    background: var(--gray-50);
                    border: 1px solid var(--gray-200);
                    transition: var(--transition-fast);
                    text-decoration: none;
                    color: inherit;
                }

                .post-item:hover {
                    background: var(--white);
                    box-shadow: var(--shadow-md);
                    transform: translateY(-2px);
                }

                .post-image {
                    width: 80px;
                    height: 80px;
                    border-radius: var(--radius-md);
                    background: var(--primary-color);
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--white);
                    font-size: var(--font-size-2xl);
                    font-weight: 700;
                }

                .post-content {
                    flex: 1;
                    min-width: 0;
                }

                .post-title {
                    font-size: var(--font-size-lg);
                    font-weight: 600;
                    color: var(--gray-900);
                    margin-bottom: var(--spacing-2);
                    line-height: 1.4;
                }

                .post-meta {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                    margin-bottom: var(--spacing-2);
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }

                .post-author {
                    font-weight: 500;
                    color: var(--primary-color);
                }

                .post-date {
                    color: var(--gray-500);
                }

                .post-excerpt {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    line-height: 1.6;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }

                @media (max-width: 768px) {
                    .post-item {
                        flex-direction: column;
                        gap: var(--spacing-3);
                    }
                    
                    .post-image {
                        width: 100%;
                        height: 120px;
                    }
                }
            </style>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">最新博文</h3>
                </div>
                <div class="card-body">
                    <div class="post-list">
                        ${latestPosts.map(post => `
                            <a href="/post/${post.title}" class="post-item">
                                <div class="post-image">${post.image}</div>
                                <div class="post-content">
                                    <h4 class="post-title">${post.title}</h4>
                                    <div class="post-meta">
                                        <span class="post-author">${post.author}</span>
                                        <span class="post-date">${post.date}</span>
                                    </div>
                                    <p class="post-excerpt">${post.excerpt}</p>
                                </div>
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define('latest-posts-card', LatestPostsCard); 