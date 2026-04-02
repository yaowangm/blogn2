/**
 * 移动端左侧栏折叠：合并布局时（≤1024px）仅显示标题行，点击展开/收起内容。
 */
(function () {
    const BREAKPOINT = 1024;
    /** 左侧栏中始终不折叠的组件（任何情况下都完整显示） */
    const NO_COLLAPSE_TAGS = new Set(['blog-profile-card']);
    const TITLE_MAP = {
        'blog-profile-card': '博客信息',
        'blog-navigation-card': '博客导航',
        'recent-comments-card': '最近评论',
        'recent-updates-card': '最近更新',
        'friend-links-card': '外站链接',
        'popular-blogs-card': '热门博客',
        'recent-blogs-card': '最近博客',
        'categories-card': '分类',
        'blog-posts-list-card': '文章列表',
        'blog-info-card': '博客信息',
        'user-profile-card': '个人资料',
        'admin-tools-card': '管理工具',
        'about-card': '关于',
        'subscriptions-list-card': '订阅列表',
        'stats-card': '统计',
        'messages-list-card': '消息列表',
        'navigation-card': '导航',
        'category-maintenance-card': '分类维护',
        'edit-post-form': '编辑文章',
        'create-post-form': '发表文章'
    };

    function getTitle(el) {
        const tag = (el && el.tagName && el.tagName.toLowerCase()) || '';
        return TITLE_MAP[tag] || el.getAttribute('data-collapse-title') || '卡片';
    }

    function isCollapsibleElement(el) {
        if (!el || el.classList.contains('sidebar-left-collapsible')) return false;
        return el.nodeType === Node.ELEMENT_NODE;
    }

    function createHeader(title) {
        const header = document.createElement('div');
        header.className = 'sidebar-left-collapsible-header';
        header.setAttribute('role', 'button');
        header.setAttribute('tabindex', '0');
        header.setAttribute('aria-expanded', 'false');
        header.innerHTML = `
            <span class="sidebar-left-collapsible-title">${escapeHtml(title)}</span>
            <button type="button" class="sidebar-left-collapsible-toggle" aria-label="展开或收起">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                    <polyline points="6,9 12,15 18,9"></polyline>
                </svg>
            </button>
        `;
        return header;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function wrapCard(sidebar, card) {
        const title = getTitle(card);
        const wrap = document.createElement('div');
        wrap.className = 'sidebar-left-collapsible collapsed';

        const header = createHeader(title);
        const content = document.createElement('div');
        content.className = 'sidebar-left-collapsible-content';

        wrap.appendChild(header);
        wrap.appendChild(content);
        sidebar.replaceChild(wrap, card);
        content.appendChild(card);

        const toggle = function () {
            wrap.classList.toggle('collapsed');
            header.setAttribute('aria-expanded', wrap.classList.contains('collapsed') ? 'false' : 'true');
        };

        header.addEventListener('click', function () {
            toggle();
        });
        header.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggle();
            }
        });
    }

    function unwrapCard(sidebar, wrap) {
        const content = wrap.querySelector('.sidebar-left-collapsible-content');
        const card = content && content.firstElementChild;
        if (card) {
            sidebar.replaceChild(card, wrap);
        }
    }

    function applyMobile(sidebar) {
        const children = Array.from(sidebar.children);
        children.forEach(function (el) {
            if (!isCollapsibleElement(el)) return;
            const tag = el.tagName && el.tagName.toLowerCase();
            if (NO_COLLAPSE_TAGS.has(tag)) return;
            wrapCard(sidebar, el);
        });
    }

    function applyDesktop(sidebar) {
        const wrappers = Array.from(sidebar.querySelectorAll(':scope > .sidebar-left-collapsible'));
        wrappers.forEach(function (wrap) {
            unwrapCard(sidebar, wrap);
        });
    }

    function update() {
        const width = window.innerWidth;
        const singleColumn = width <= BREAKPOINT;
        document.body.classList.toggle('layout-single-column', singleColumn);

        const sidebars = document.querySelectorAll('.sidebar.sidebar-left');
        sidebars.forEach(function (sidebar) {
            if (singleColumn) {
                applyMobile(sidebar);
            } else {
                applyDesktop(sidebar);
            }
        });
    }

    let resizeTimer;
    function onResize() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(update, 100);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', update);
    } else {
        update();
    }
    window.addEventListener('resize', onResize);
    window.addEventListener('load', update);
    window.addEventListener('orientationchange', function () { setTimeout(update, 100); });
})();
