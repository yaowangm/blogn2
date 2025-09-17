/**
 * RSS自动发现脚本
 * 动态添加RSS自动发现链接到HTML head中
 */

class RSSDiscovery {
    constructor() {
        this.init();
    }
    
    init() {
        // 根据当前页面类型添加相应的RSS链接
        this.addRSSDiscoveryLinks();
    }
    
    /**
     * 添加RSS自动发现链接
     */
    addRSSDiscoveryLinks() {
        const currentPath = window.location.pathname;
        
        if (currentPath === '/') {
            // 首页 - 添加全站RSS链接
            this.addSiteRSSLinks();
        } else if (currentPath.startsWith('/blog/') && currentPath.split('/').length === 3) {
            // 博客页面 - 添加博客RSS链接
            const projectId = this.getProjectIdFromUrl();
            if (projectId) {
                this.addBlogRSSLinks(projectId);
            }
        } else if (currentPath.startsWith('/article/')) {
            // 文章页面 - 需要从页面内容获取博客ID
            this.addArticlePageRSSLinks();
        }
    }
    
    /**
     * 添加全站RSS链接
     */
    addSiteRSSLinks() {
        const links = [
            {
                rel: 'alternate',
                type: 'application/rss+xml',
                title: 'BlogN2 - 全站RSS',
                href: '/api/rss/site'
            },
            {
                rel: 'alternate',
                type: 'application/atom+xml',
                title: 'BlogN2 - 全站Atom',
                href: '/api/rss/site?format=atom'
            }
        ];
        
        this.addLinks(links);
    }
    
    /**
     * 添加博客RSS链接
     */
    addBlogRSSLinks(projectId) {
        const links = [
            {
                rel: 'alternate',
                type: 'application/rss+xml',
                title: '博客RSS订阅',
                href: `/api/rss/blog/${projectId}`
            },
            {
                rel: 'alternate',
                type: 'application/atom+xml',
                title: '博客Atom订阅',
                href: `/api/rss/blog/${projectId}?format=atom`
            }
        ];
        
        this.addLinks(links);
    }
    
    /**
     * 添加文章页面RSS链接
     * 需要等待页面加载完成后获取博客ID
     */
    addArticlePageRSSLinks() {
        // 等待页面加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.waitForBlogId();
            });
        } else {
            this.waitForBlogId();
        }
    }
    
    /**
     * 等待获取博客ID
     */
    waitForBlogId() {
        // 尝试从URL获取博客ID
        const urlMatch = window.location.pathname.match(/\/blog\/(\d+)\/article\/(\d+)/);
        if (urlMatch) {
            const projectId = urlMatch[1];
            this.addBlogRSSLinks(projectId);
            return;
        }
        
        // 如果URL中没有，尝试从页面组件获取
        this.waitForComponentData();
    }
    
    /**
     * 等待组件数据加载完成
     */
    waitForComponentData() {
        let attempts = 0;
        const maxAttempts = 50; // 最多等待5秒
        
        const checkInterval = setInterval(() => {
            attempts++;
            
            // 尝试从blog-profile-card获取projectId
            const blogProfileCard = document.querySelector('blog-profile-card');
            if (blogProfileCard && blogProfileCard.projectId) {
                clearInterval(checkInterval);
                this.addBlogRSSLinks(blogProfileCard.projectId);
                return;
            }
            
            // 尝试从blog-navigation-card获取projectId
            const blogNavCard = document.querySelector('blog-navigation-card');
            if (blogNavCard && blogNavCard.projectId) {
                clearInterval(checkInterval);
                this.addBlogRSSLinks(blogNavCard.projectId);
                return;
            }
            
            // 尝试从article-header-card获取projectId
            const articleHeaderCard = document.querySelector('article-header-card');
            if (articleHeaderCard && articleHeaderCard.articleData && articleHeaderCard.articleData.projectid) {
                clearInterval(checkInterval);
                this.addBlogRSSLinks(articleHeaderCard.articleData.projectid);
                return;
            }
            
            // 超时处理
            if (attempts >= maxAttempts) {
                clearInterval(checkInterval);
                console.warn('RSS Discovery: 无法获取博客ID，使用默认值');
                // 使用默认博客ID 4
                this.addBlogRSSLinks(4);
            }
        }, 100);
    }
    
    /**
     * 从URL获取项目ID
     */
    getProjectIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length >= 3 && pathParts[1] === 'blog') {
            const projectId = parseInt(pathParts[2]);
            if (!isNaN(projectId)) {
                return projectId;
            }
        }
        return null;
    }
    
    /**
     * 添加链接到head
     */
    addLinks(links) {
        const head = document.head;
        
        links.forEach(linkData => {
            // 检查是否已存在相同的链接
            const existingLink = head.querySelector(`link[href="${linkData.href}"]`);
            if (existingLink) {
                return; // 已存在，跳过
            }
            
            const link = document.createElement('link');
            Object.assign(link, linkData);
            head.appendChild(link);
            
            // console.log(`RSS Discovery: 添加链接 ${linkData.title} -> ${linkData.href}`);
        });
    }
}

// 页面加载完成后初始化RSS发现
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new RSSDiscovery();
    });
} else {
    new RSSDiscovery();
}
