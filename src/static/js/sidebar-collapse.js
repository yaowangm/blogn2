/**
 * 单列布局（≤1024px）时，左侧栏卡片仅保留自身标题栏，点击标题展开/收起内容。
 * 样式注入各卡片 Shadow DOM，不插入额外 DOM 包裹层。
 */
(function () {
    const BREAKPOINT = 1024;
    const COLLAPSE_STYLE_ID = 'sidebar-collapse-host-styles';
    const NO_COLLAPSE_TAGS = new Set(['blog-profile-card']);
    const COLLAPSE_HOST_CSS = `
:host([data-sidebar-collapsible]) .card-header {
    position: relative;
    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    padding-right: calc(var(--spacing-4) + 1.25rem);
    transition: background-color var(--transition-fast);
}
:host([data-sidebar-collapsible]) .card-header:hover {
    background: var(--gray-100);
}
:host([data-sidebar-collapsible]) .card-header::after {
    content: "";
    position: absolute;
    right: var(--spacing-4);
    top: 50%;
    width: 0.5rem;
    height: 0.5rem;
    margin-top: -0.15rem;
    border-right: 2px solid var(--gray-400);
    border-bottom: 2px solid var(--gray-400);
    transform: translateY(-50%) rotate(45deg);
    transition: transform var(--transition-fast), border-color var(--transition-fast);
}
:host([data-sidebar-collapsible]:not([data-sidebar-collapsed])) .card-header::after {
    transform: translateY(-35%) rotate(-135deg);
    border-color: var(--gray-500);
}
:host([data-sidebar-collapsible][data-sidebar-collapsed]) .card > :not(.card-header) {
    display: none !important;
}
:host([data-sidebar-collapsible][data-sidebar-collapsed]) .card-header {
    border-bottom-color: transparent;
}
:host([data-sidebar-collapsible][data-sidebar-collapsed]) .card:hover {
    box-shadow: var(--shadow-sm);
}
:host([data-sidebar-collapsible]) .card-header:focus {
    outline: none;
}
:host([data-sidebar-collapsible]) .card-header:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: -2px;
}
`;

    function injectCollapseStyles(el) {
        if (!el.shadowRoot) {
            return;
        }
        const css = el.hasAttribute('data-sidebar-collapsible') ? COLLAPSE_HOST_CSS : '';
        let style = el.shadowRoot.getElementById(COLLAPSE_STYLE_ID);
        if (!style) {
            style = document.createElement('style');
            style.id = COLLAPSE_STYLE_ID;
            el.shadowRoot.appendChild(style);
        } else if (style.textContent === css) {
            return;
        }
        style.textContent = css;
    }

    function hasCollapsibleHeader(el) {
        return Boolean(el.shadowRoot && el.shadowRoot.querySelector('.card-header'));
    }

    function syncHeaderAria(el) {
        const header = el.shadowRoot && el.shadowRoot.querySelector('.card-header');
        if (!header) {
            return;
        }
        if (!el.hasAttribute('data-sidebar-collapsible')) {
            header.removeAttribute('role');
            header.removeAttribute('aria-expanded');
            header.removeAttribute('tabindex');
            return;
        }
        const expanded = !el.hasAttribute('data-sidebar-collapsed');
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        header.setAttribute('tabindex', '0');
    }

    function toggleCollapse(el) {
        if (el.hasAttribute('data-sidebar-collapsed')) {
            el.removeAttribute('data-sidebar-collapsed');
            el.setAttribute('data-sidebar-expanded', '');
        } else {
            el.setAttribute('data-sidebar-collapsed', '');
            el.removeAttribute('data-sidebar-expanded');
        }
        syncHeaderAria(el);
    }

    function bindCollapseInteraction(el) {
        if (el._sidebarCollapseBound) {
            return;
        }
        el._sidebarCollapseBound = true;

        el.addEventListener('click', function (event) {
            if (!el.hasAttribute('data-sidebar-collapsible')) {
                return;
            }
            const header = event.composedPath().find((node) => (
                node.classList && node.classList.contains('card-header')
            ));
            if (!header) {
                return;
            }
            const interactive = event.target.closest('a, button');
            if (interactive && interactive !== header) {
                return;
            }
            toggleCollapse(el);
        });

        el.addEventListener('keydown', function (event) {
            if (!el.hasAttribute('data-sidebar-collapsible')) {
                return;
            }
            const header = el.shadowRoot && el.shadowRoot.querySelector('.card-header');
            if (!header || !header.contains(event.target)) {
                return;
            }
            if (event.key !== 'Enter' && event.key !== ' ') {
                return;
            }
            event.preventDefault();
            toggleCollapse(el);
        });
    }

    function enableCollapse(el) {
        if (!hasCollapsibleHeader(el)) {
            return;
        }
        if (el.hasAttribute('data-sidebar-collapsible') && el._sidebarCollapseBound) {
            syncHeaderAria(el);
            return;
        }
        el.setAttribute('data-sidebar-collapsible', '');
        if (!el.hasAttribute('data-sidebar-expanded')) {
            el.setAttribute('data-sidebar-collapsed', '');
        }
        injectCollapseStyles(el);
        bindCollapseInteraction(el);
        syncHeaderAria(el);
    }

    function disableCollapse(el) {
        el.removeAttribute('data-sidebar-collapsible');
        el.removeAttribute('data-sidebar-collapsed');
        el.removeAttribute('data-sidebar-expanded');
        if (el._sidebarRenderObserver) {
            el._sidebarRenderObserver.disconnect();
            el._sidebarRenderObserver = null;
        }
        injectCollapseStyles(el);
        syncHeaderAria(el);
    }

    function observeCardRender(el) {
        if (el._sidebarRenderObserver) {
            return;
        }
        const scheduleEnable = function () {
            if (window.innerWidth > BREAKPOINT) {
                return;
            }
            if (el._sidebarCollapseSchedule) {
                return;
            }
            el._sidebarCollapseSchedule = requestAnimationFrame(function () {
                el._sidebarCollapseSchedule = null;
                enableCollapse(el);
            });
        };
        const attach = function () {
            if (!el.shadowRoot || el._sidebarRenderObserver) {
                return;
            }
            el._sidebarRenderObserver = new MutationObserver(scheduleEnable);
            el._sidebarRenderObserver.observe(el.shadowRoot, { childList: true, subtree: true });
            scheduleEnable();
        };

        if (el.shadowRoot) {
            attach();
        } else {
            requestAnimationFrame(attach);
        }
    }

    function isSidebarCard(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) {
            return false;
        }
        const tag = el.tagName && el.tagName.toLowerCase();
        return tag && tag.includes('-') && !NO_COLLAPSE_TAGS.has(tag);
    }

    function observeSidebar(sidebar) {
        if (sidebar._sidebarListObserver) {
            return;
        }
        sidebar._sidebarListObserver = new MutationObserver(scheduleUpdate);
        sidebar._sidebarListObserver.observe(sidebar, { childList: true });
    }

    let updateScheduled = false;
    function scheduleUpdate() {
        if (updateScheduled) {
            return;
        }
        updateScheduled = true;
        requestAnimationFrame(function () {
            updateScheduled = false;
            update();
        });
    }

    function applyMobile(sidebar) {
        Array.from(sidebar.children).forEach(function (el) {
            if (isSidebarCard(el)) {
                observeCardRender(el);
            }
        });
    }

    function applyDesktop(sidebar) {
        Array.from(sidebar.children).forEach(function (el) {
            if (isSidebarCard(el)) {
                disableCollapse(el);
            }
        });
    }

    function update() {
        const singleColumn = window.innerWidth <= BREAKPOINT;
        document.body.classList.toggle('layout-single-column', singleColumn);

        document.querySelectorAll('.sidebar.sidebar-left').forEach(function (sidebar) {
            observeSidebar(sidebar);
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
    window.addEventListener('orientationchange', function () {
        setTimeout(update, 100);
    });
})();
