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
                :host { display: block; margin-bottom: var(--card-margin, 24px); }
                .card-wrap {
                    background: var(--card-bg, #fff);
                    border-radius: var(--card-radius, 8px);
                    box-shadow: var(--card-shadow, 0 1px 3px rgba(0,0,0,.1));
                    padding: var(--card-padding, 24px);
                    border: 1px solid var(--gray-200, #e5e7eb);
                }
                .card-header {
                    margin-bottom: 16px;
                    padding-bottom: 12px;
                    border-bottom: 1px solid var(--gray-200, #e5e7eb);
                }
                .card-title {
                    margin: 0;
                    font-size: 20px;
                    font-weight: 600;
                    color: var(--gray-800, #111827);
                }
                .hint {
                    font-size: 13px;
                    color: var(--gray-600, #4b5563);
                    margin-bottom: 16px;
                    line-height: 1.5;
                }
                .btn-primary {
                    background: var(--primary-color, #2563eb);
                    color: #fff;
                    border: none;
                    padding: 10px 18px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
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
        btn.addEventListener('click', () => this._onRecalculate(btn, msgEl));
    }

    async _onRecalculate(btn, msgEl) {
        if (this._busy) return;
        if (!confirm('确定要重新计算所有博客的更新时间吗？\n\n该操作会更新数据库中全部博客项目的 updatetime。')) {
            return;
        }
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
