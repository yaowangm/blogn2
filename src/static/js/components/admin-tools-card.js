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
                :host { display: block; }
                .card-title {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-2);
                }
                .title-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--primary-color);
                    flex-shrink: 0;
                }
                .title-icon svg {
                    width: 100%;
                    height: 100%;
                    display: block;
                }
                .hint {
                    font-size: var(--font-size-sm);
                    color: var(--gray-600);
                    margin: 0 0 var(--spacing-3);
                    line-height: 1.5;
                }
                .msg {
                    margin-top: var(--spacing-3);
                    font-size: var(--font-size-sm);
                }
                .msg.ok { color: var(--success-color, #059669); }
                .msg.err { color: var(--error-color); }
            </style>
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">
                        <span class="title-icon">${Icons.settings}</span>
                        管理工具
                    </h2>
                </div>
                <div class="card-body">
                    <p class="hint">根据每篇已发布文章的发表/编辑时间，批量重算并写回所有博客的「更新时间」字段（用于历史数据修复）。</p>
                    <button type="button" class="btn btn-primary btn-sm" id="recalcBtn">重新计算博客的更新时间</button>
                    <div class="msg" id="recalcMsg" style="display:none;"></div>
                </div>
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
