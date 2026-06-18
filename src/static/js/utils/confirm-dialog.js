/**
 * 全站统一样式的确认对话框（挂载到 document.body，适用于任意页面/Shadow DOM）
 * 与 admin-tools-card 弹窗一致：白底黑字、favicon 标题、底部取消/确定两端对齐、较宽按钮
 */
(function (global) {
    const STYLE_ID = 'blogn-confirm-dialog-styles';
    const Z_INDEX = 10050;

    function ensureStyles() {
        if (document.getElementById(STYLE_ID)) return;
        const s = document.createElement('style');
        s.id = STYLE_ID;
        s.textContent = `
            @import url('/static/css/common-components.css');
            .blogn-confirm-dialog-overlay {
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: ${Z_INDEX};
                padding: 24px;
                box-sizing: border-box;
            }
            .blogn-confirm-dialog-panel {
                background: #ffffff;
                color: #111827;
                width: 100%;
                max-width: 560px;
                min-width: min(100%, 320px);
                border-radius: var(--radius-lg, 12px);
                box-shadow: var(--shadow-xl, 0 20px 25px -5px rgba(0,0,0,.1), 0 10px 10px -5px rgba(0,0,0,.04));
                padding: var(--spacing-6, 24px) var(--spacing-8, 28px);
                box-sizing: border-box;
            }
            .blogn-confirm-dialog-header {
                display: flex;
                align-items: center;
                gap: 12px;
                padding-bottom: var(--spacing-4, 16px);
                margin-bottom: var(--spacing-4, 16px);
                border-bottom: 1px solid var(--gray-200, #e5e7eb);
            }
            .blogn-confirm-dialog-favicon {
                width: 32px;
                height: 32px;
                flex-shrink: 0;
                display: block;
            }
            .blogn-confirm-dialog-title {
                margin: 0;
                font-size: var(--font-size-lg, 18px);
                font-weight: 600;
                color: #111827;
                line-height: 1.3;
            }
            .blogn-confirm-dialog-body {
                font-size: var(--font-size-sm, 14px);
                line-height: 1.65;
                color: #111827;
            }
            .blogn-confirm-dialog-body p {
                margin: 0 0 10px 0;
            }
            .blogn-confirm-dialog-body p:last-child {
                margin-bottom: 0;
            }
            .blogn-confirm-dialog-body code {
                font-size: 0.92em;
                background: #f3f4f6;
                padding: 2px 6px;
                border-radius: 4px;
            }
            .blogn-confirm-dialog-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: var(--spacing-3, 12px);
                margin-top: var(--spacing-6, 24px);
                padding-top: var(--spacing-4, 16px);
                border-top: 1px solid var(--gray-200, #e5e7eb);
            }
            .blogn-confirm-dialog-footer .btn {
                min-width: 7.5rem;
            }
        `;
        document.head.appendChild(s);
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    /**
     * @param {string} block
     * @returns {string}
     */
    function paragraphHtml(block) {
        const lines = block.split('\n').map((l) => l.trimEnd()).filter((l, i, arr) => !(l === '' && i === arr.length - 1));
        if (lines.length <= 1) {
            return `<p>${escapeHtml(block.trim())}</p>`;
        }
        return `<p>${lines.map((l) => escapeHtml(l)).join('<br>')}</p>`;
    }

    /**
     * @param {Object} opts
     * @param {string} opts.title
     * @param {string[]} [opts.paragraphs]
     * @param {string} [opts.message] — 与 paragraphs 二选一，按空行分段；段内单行换行转为 &lt;br&gt;
     * @param {string} [opts.confirmText='确定']
     * @param {string} [opts.cancelText='取消']
     * @param {boolean} [opts.danger=false]
     * @returns {Promise<boolean>}
     */
    function openConfirmDialog(opts) {
        ensureStyles();
        const title = opts.title || '确认';
        const confirmText = opts.confirmText != null ? opts.confirmText : '确定';
        const cancelText = opts.cancelText != null ? opts.cancelText : '取消';
        const danger = !!opts.danger;

        let paragraphs = opts.paragraphs;
        if (!paragraphs || !paragraphs.length) {
            const msg = (opts.message || '').trim();
            paragraphs = msg ? msg.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean) : [];
        }
        if (!paragraphs.length) {
            paragraphs = ['请确认是否继续。'];
        }

        const bodyHtml = paragraphs.map(paragraphHtml).join('');

        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'blogn-confirm-dialog-overlay';
            overlay.setAttribute('role', 'presentation');
            overlay.innerHTML = `
                <div class="blogn-confirm-dialog-panel" role="dialog" aria-modal="true" aria-labelledby="blogn-cd-title">
                    <div class="blogn-confirm-dialog-header">
                        <img class="blogn-confirm-dialog-favicon" src="/static/favicon.svg" width="32" height="32" alt="" />
                        <h3 class="blogn-confirm-dialog-title" id="blogn-cd-title">${escapeHtml(title)}</h3>
                    </div>
                    <div class="blogn-confirm-dialog-body">${bodyHtml}</div>
                    <div class="blogn-confirm-dialog-footer">
                        <button type="button" class="btn btn-secondary btn-sm" data-blogncd="cancel">${escapeHtml(cancelText)}</button>
                        <button type="button" class="btn ${danger ? 'btn-danger' : 'btn-primary'} btn-sm" data-blogncd="confirm">${escapeHtml(confirmText)}</button>
                    </div>
                </div>
            `;

            function cleanup(result) {
                document.removeEventListener('keydown', onKey);
                overlay.remove();
                resolve(result);
            }

            function onKey(e) {
                if (e.key === 'Escape') {
                    e.preventDefault();
                    cleanup(false);
                }
            }

            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) cleanup(false);
            });

            const panel = overlay.querySelector('.blogn-confirm-dialog-panel');
            panel.addEventListener('click', (e) => e.stopPropagation());

            const btnCancel = overlay.querySelector('[data-blogncd="cancel"]');
            const btnOk = overlay.querySelector('[data-blogncd="confirm"]');
            btnCancel.addEventListener('click', () => cleanup(false));
            btnOk.addEventListener('click', () => cleanup(true));

            document.addEventListener('keydown', onKey);
            document.body.appendChild(overlay);
            btnOk.focus();
        });
    }

    global.openConfirmDialog = openConfirmDialog;
})(typeof window !== 'undefined' ? window : globalThis);
