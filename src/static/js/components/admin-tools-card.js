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

                .recalc-modal {
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.5);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    padding: 24px;
                    box-sizing: border-box;
                }
                .recalc-modal.show {
                    display: flex;
                }
                .recalc-modal-content {
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
                .recalc-modal-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding-bottom: var(--spacing-4, 16px);
                    margin-bottom: var(--spacing-4, 16px);
                    border-bottom: 1px solid var(--gray-200, #e5e7eb);
                }
                .recalc-modal-favicon {
                    width: 32px;
                    height: 32px;
                    flex-shrink: 0;
                    display: block;
                }
                .recalc-modal-title {
                    margin: 0;
                    font-size: var(--font-size-lg, 18px);
                    font-weight: 600;
                    color: #111827;
                    line-height: 1.3;
                }
                .recalc-modal-body {
                    font-size: var(--font-size-sm, 14px);
                    line-height: 1.65;
                    color: #111827;
                }
                .recalc-modal-body p {
                    margin: 0 0 10px 0;
                }
                .recalc-modal-body p:last-child {
                    margin-bottom: 0;
                }
                .recalc-modal-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: var(--spacing-3, 12px);
                    margin-top: var(--spacing-6, 24px);
                    padding-top: var(--spacing-4, 16px);
                    border-top: 1px solid var(--gray-200, #e5e7eb);
                }
                .recalc-modal .btn-secondary {
                    background-color: var(--gray-100, #f3f4f6);
                    color: var(--gray-700, #374151);
                    border: 1px solid var(--gray-300, #d1d5db);
                    padding: var(--spacing-2, 8px) var(--spacing-6, 24px);
                    min-width: 7.5rem;
                    border-radius: var(--radius-md, 6px);
                    font-size: var(--font-size-base, 14px);
                    font-weight: 500;
                    cursor: pointer;
                    transition: background-color var(--transition-fast, 0.15s ease), border-color var(--transition-fast, 0.15s ease);
                }
                .recalc-modal .btn-secondary:hover {
                    background-color: var(--gray-200, #e5e7eb);
                    border-color: var(--gray-400, #9ca3af);
                }
                .recalc-modal .btn-primary {
                    background-color: var(--primary-color, #2563eb);
                    color: #ffffff;
                    border: 1px solid var(--primary-color, #2563eb);
                    padding: var(--spacing-2, 8px) var(--spacing-6, 24px);
                    min-width: 7.5rem;
                    border-radius: var(--radius-md, 6px);
                    font-size: var(--font-size-base, 14px);
                    font-weight: 500;
                    cursor: pointer;
                    transition: background-color var(--transition-fast, 0.15s ease), border-color var(--transition-fast, 0.15s ease);
                }
                .recalc-modal .btn-primary:hover:not(:disabled) {
                    background-color: var(--primary-hover, #1d4ed8);
                    border-color: var(--primary-hover, #1d4ed8);
                }
                .recalc-modal .btn-primary:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
            </style>
            <div class="card-wrap">
                <div class="card-header">
                    <h2 class="card-title">管理工具</h2>
                </div>
                <p class="hint">根据每篇已发布文章的发表/编辑时间，批量重算并写回所有博客的「更新时间」字段（用于历史数据修复）。</p>
                <button type="button" class="btn-primary" id="recalcBtn">重新计算博客的更新时间</button>
                <div class="msg" id="recalcMsg" style="display:none;"></div>
            </div>
            <div class="recalc-modal" id="recalcConfirmModal" aria-hidden="true">
                <div class="recalc-modal-content" role="dialog" aria-labelledby="recalcModalTitle">
                    <div class="recalc-modal-header">
                        <img class="recalc-modal-favicon" src="/static/favicon.svg" width="32" height="32" alt="" />
                        <h3 class="recalc-modal-title" id="recalcModalTitle">重新计算博客更新时间</h3>
                    </div>
                    <div class="recalc-modal-body">
                        <p>确定要为<strong>全部博客</strong>重新计算「更新时间」吗？</p>
                        <p>该操作会根据每篇已发布文章的发表/编辑时间，将结果写回数据库中对应博客项目的 <code>updatetime</code> 字段。</p>
                    </div>
                    <div class="recalc-modal-footer">
                        <button type="button" class="btn-secondary" id="recalcModalCancel">取消</button>
                        <button type="button" class="btn-primary" id="recalcModalConfirm">确定</button>
                    </div>
                </div>
            </div>
        `;

        const btn = this.shadowRoot.getElementById('recalcBtn');
        const msgEl = this.shadowRoot.getElementById('recalcMsg');
        const modal = this.shadowRoot.getElementById('recalcConfirmModal');
        const modalCancel = this.shadowRoot.getElementById('recalcModalCancel');
        const modalConfirm = this.shadowRoot.getElementById('recalcModalConfirm');

        btn.addEventListener('click', () => this._showRecalcModal(modal));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this._hideRecalcModal(modal);
        });
        modalCancel.addEventListener('click', () => this._hideRecalcModal(modal));
        modalConfirm.addEventListener('click', () => {
            this._hideRecalcModal(modal);
            this._executeRecalculate(btn, msgEl, modalConfirm);
        });
    }

    _showRecalcModal(modal) {
        if (!modal) return;
        modal.classList.add('show');
        modal.setAttribute('aria-hidden', 'false');
    }

    _hideRecalcModal(modal) {
        if (!modal) return;
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
    }

    async _executeRecalculate(btn, msgEl, modalConfirmBtn) {
        if (this._busy) return;
        this._busy = true;
        btn.disabled = true;
        if (modalConfirmBtn) modalConfirmBtn.disabled = true;
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
            if (modalConfirmBtn) modalConfirmBtn.disabled = false;
        }
    }
}

customElements.define('admin-tools-card', AdminToolsCard);
