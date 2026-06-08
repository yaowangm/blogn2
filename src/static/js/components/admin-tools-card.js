/**
 * 个人资料页：管理员专属「管理工具」卡片
 */
class AdminToolsCard extends BaseComponent {
    constructor() {
        super();
        this._busy = false;
    }

    connectedCallback() {
        this.render();
    }

    render() {
        if (typeof UserManager === 'undefined' || !UserManager.isAdmin()) {
            this.style.display = 'none';
            this.shadowRoot.innerHTML = '';
            return;
        }

        this.style.display = '';
        this.shadowRoot.innerHTML = `
            <style>
                @import url('/static/css/common-components.css');
                :host { display: block; margin-bottom: var(--card-margin, 24px); }
                .card-wrap {
                    background: var(--white);
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-sm);
                    padding: var(--spacing-3) var(--spacing-4);
                    border: 1px solid var(--gray-200);
                }
                .card-wrap:hover {
                    box-shadow: var(--shadow-md);
                }
                .card-header {
                    margin-bottom: var(--spacing-3);
                    padding-bottom: var(--spacing-2);
                    border-bottom: 1px solid var(--gray-200);
                }
                .hint {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    margin-bottom: var(--spacing-3);
                    line-height: 1.5;
                }
                .btn-primary {
                    padding: calc(var(--spacing-2) * 1.2) calc(var(--spacing-3) * 1.2);
                    font-size: calc(var(--font-size-xs) * 1.2);
                    line-height: 1.25;
                }
                .btn-primary:hover:not(:disabled) {
                    filter: brightness(0.95);
                }
                .btn-primary:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                .msg { margin-top: 12px; font-size: 14px; }
                .msg.ok { color: #059669; }
                .msg.err { color: #dc2626; }
            </style>
            <div class="card-wrap">
                <div class="card-header">
                    <h2 class="card-title">管理工具</h2>
                </div>
                <p class="hint">根据每篇已发布文章的发表/编辑时间，批量重算并写回所有博客的「更新时间」字段（用于历史数据修复）。</p>
                <button type="button" class="btn-primary" id="recalcBtn">重新计算博客的更新时间</button>
                <div class="msg" id="recalcMsg" style="display:none;"></div>
            </div>
        `;

        const btn = this.shadowRoot.getElementById('recalcBtn');
        const msgEl = this.shadowRoot.getElementById('recalcMsg');
        btn.addEventListener('click', () => this._onRecalculateClick(btn, msgEl));
    }

    async _onRecalculateClick(btn, msgEl) {
        if (this._busy) return;
        if (typeof openConfirmDialog !== 'function') {
            console.error('openConfirmDialog 未加载，请引入 /static/js/utils/confirm-dialog.js');
            return;
        }
        const ok = await openConfirmDialog({
            title: '重新计算博客更新时间',
            paragraphs: [
                '确定要为全部博客重新计算「更新时间」吗？',
                '该操作会根据每篇已发布文章的发表/编辑时间，将结果写回数据库中对应博客项目的 updatetime 字段。',
            ],
        });
        if (!ok) return;
        await this._executeRecalculate(btn, msgEl);
    }

    async _executeRecalculate(btn, msgEl) {
        if (this._busy) return;
        this._busy = true;
        btn.disabled = true;
        msgEl.style.display = 'none';
        try {
            const res = await fetch('/api/admin/projects/recalculate-updatetimes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...UserManager.createHeaders()
                }
            });
            const data = await res.json().catch(() => ({}));
            msgEl.style.display = 'block';
            if (res.ok) {
                msgEl.className = 'msg ok';
                msgEl.textContent = data.message
                    ? `${data.message}（共 ${data.project_count} 个博客）`
                    : '操作完成';
            } else {
                msgEl.className = 'msg err';
                msgEl.textContent = data.detail || `请求失败（${res.status}）`;
            }
        } catch (e) {
            msgEl.style.display = 'block';
            msgEl.className = 'msg err';
            msgEl.textContent = e.message || '网络错误';
        } finally {
            this._busy = false;
            btn.disabled = false;
        }
    }
}

customElements.define('admin-tools-card', AdminToolsCard);
