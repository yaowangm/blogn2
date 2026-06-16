/**
 * 友情链接管理页面脚本
 * 
 * 提供完整的友情链接管理功能，包括：
 * - 友情链接的增删改查操作
 * - 权限验证（仅博客所有者和管理员可管理）
 * - 数量限制控制（最多20个链接）
 * - 模态框表单交互
 * - 实时数据更新和缓存清理
 * 
 * @author Blogn Team
 * @version 1.0.0
 */
class FriendLinksManager {
    constructor() {
        this.projectId = null;
        this.friendLinks = [];
        this.editingLinkId = null;
        this.isLoading = false;
        
        this.init();
    }
    
    /**
     * 初始化友情链接管理器
     * 
     * 执行以下初始化步骤：
     * 1. 从URL参数获取项目ID
     * 2. 验证用户权限
     * 3. 绑定事件监听器
     * 4. 加载友情链接数据
     */
    init() {
        // 获取项目ID
        this.projectId = this.getProjectIdFromUrl();
        // 允许 project_id=0（全站），仅在无法解析时提示
        if (this.projectId === null) {
            this.showError('缺少项目ID参数');
            return;
        }
        this.updatePageHeader();
        
        // 检查用户权限
        this.checkUserPermissions();
        
        // 绑定事件
        this.bindEvents();
        
        // 加载友情链接列表
        this.loadFriendLinks();
    }

    updatePageHeader() {
        const isGlobal = this.projectId === 0;
        const titleEl = document.querySelector('title');
        const pageTitle = document.getElementById('pageTitleText');
        const desc = document.getElementById('pageDescription');
        if (isGlobal) {
            if (titleEl) titleEl.textContent = '管理全站友情链接 - BlogN';
            if (pageTitle) pageTitle.textContent = '管理全站友情链接';
            if (desc) desc.textContent = '管理全站友情链接，最多可添加 20 个友情链接';
        } else {
            if (titleEl) titleEl.textContent = '管理友情链接 - BlogN';
            if (pageTitle) pageTitle.textContent = '管理友情链接';
            if (desc) desc.textContent = '管理您的博客友情链接，最多可添加 20 个友情链接';
        }
    }
    
    getProjectIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const raw = urlParams.get('project_id');
        // 无参数时默认全站模式（project_id=0）
        if (raw === null || raw === '') return 0;
        const num = parseInt(raw, 10);
        if (Number.isNaN(num)) return null;
        return num;
    }
    
    async checkUserPermissions() {
        try {
            if (!UserManager.isLoggedIn()) {
                this.showError('请先登录');
                return;
            }
            
            const currentUser = UserManager.getCurrentUser();
            const isAdmin = currentUser.state === 10;
            
            if (this.projectId === 0) {
                // 全站模式：仅管理员
                if (!isAdmin) {
                    this.showError('仅管理员可以管理全站友情链接');
                    return;
                }
            } else {
                const blogData = await BaseComponent.getProject(this.projectId);
                if (blogData === null) {
                    this.showError('无法获取博客信息');
                    return;
                }
                const isOwner = currentUser.id === blogData.userid;
                
                if (!isOwner && !isAdmin) {
                    this.showError('无权限管理该博客的友情链接');
                    return;
                }
            }
            
        } catch (error) {
            console.error('检查权限失败:', error);
            this.showError('权限检查失败');
        }
    }
    
    bindEvents() {
        // 延迟绑定事件，确保DOM完全加载
        setTimeout(() => {
            // 添加链接按钮
            const addBtn = document.getElementById('addLinkBtn');
            if (addBtn) {
                addBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showAddForm();
                });
            }
            
            // 不再需要绑定内联表单事件，因为现在使用模态框
        }, 100);
    }
    
    async loadFriendLinks() {
        this.isLoading = true;
        this.renderLinksList();
        
        try {
            const response = await fetch(`/api/projects/${this.projectId}/friend-links`);
            if (response.ok) {
                this.friendLinks = await response.json();
            } else {
                throw new Error('获取友情链接失败');
            }
        } catch (error) {
            console.error('加载友情链接失败:', error);
            this.showError('加载友情链接失败');
            this.friendLinks = [];
        } finally {
            this.isLoading = false;
            this.renderLinksList();
        }
    }
    
    renderLinksList() {
        const linksList = document.getElementById('linksList');
        
        if (this.isLoading) {
            linksList.innerHTML = '<div class="loading">加载中...</div>';
            return;
        }
        
        if (this.friendLinks.length === 0) {
            const linkIcon = typeof Icons !== 'undefined' ? Icons.friendLinks : '';
            linksList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${linkIcon}</div>
                    <p class="empty-state-title">暂无友情链接</p>
                    <p class="empty-state-description">点击「新建链接」开始添加友情链接</p>
                </div>
            `;
            return;
        }

        const limitNotice = this.friendLinks.length >= 20 ? `
            <div class="limit-notice">友情链接数量已达到上限（20 个），无法继续添加</div>
        ` : '';

        linksList.innerHTML = `
            <div class="link-rows">
                ${limitNotice}
                ${this.renderLinksItems()}
            </div>
        `;
    }
    
    renderLinksItems() {
        const editIcon = typeof Icons !== 'undefined'
            ? Icons.asBtnIcon(Icons.edit)
            : '';
        const deleteIcon = typeof Icons !== 'undefined'
            ? Icons.asBtnIcon(Icons.delete)
            : '';

        return this.friendLinks.map(link => `
            <div class="link-row" data-link-id="${link.id}">
                <div class="link-row-info">
                    <div class="link-row-name" title="${this.escapeHtml(link.subject)}">
                        ${this.escapeHtml(link.subject)}
                    </div>
                    <div class="link-row-url" title="${this.escapeHtml(link.linkstr)}">
                        ${this.escapeHtml(link.linkstr)}
                    </div>
                </div>
                <div class="link-row-actions">
                    <button type="button" class="btn btn-secondary btn-sm btn-icon-only" title="编辑" aria-label="编辑" onclick="friendLinksManager.editLink(${link.id})">
                        ${editIcon}
                    </button>
                    <button type="button" class="btn btn-danger btn-sm btn-icon-only" title="删除" aria-label="删除" onclick="friendLinksManager.deleteLink(${link.id})">
                        ${deleteIcon}
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    showAddForm() {
        this.editingLinkId = null;
        this.showModal('添加友情链接', '保存链接');
    }
    
    async editLink(linkId) {
        const link = this.friendLinks.find(l => l.id === linkId);
        if (!link) return;
        
        this.editingLinkId = linkId;
        this.showModal('编辑友情链接', '保存修改', {
            subject: link.subject,
            linkstr: link.linkstr,
            ordernum: link.ordernum || 0
        });
    }
    
    
    async createLink(linkData) {
        const response = await fetch(`/api/projects/${this.projectId}/friend-links`, {
            method: 'POST',
            headers: UserManager.createHeaders({
                'Content-Type': 'application/json'
            }),
            body: JSON.stringify(linkData)
        });
        
        if (response.ok) {
            this.showSuccess('友情链接添加成功');
            this.resetForm();
            await this.loadFriendLinks();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || '添加失败');
        }
    }
    
    async updateLink(linkId, linkData) {
        const response = await fetch(`/api/friend-links/${linkId}`, {
            method: 'PUT',
            headers: UserManager.createHeaders({
                'Content-Type': 'application/json'
            }),
            body: JSON.stringify(linkData)
        });
        
        if (response.ok) {
            this.showSuccess('友情链接更新成功');
            this.resetForm();
            await this.loadFriendLinks();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || '更新失败');
        }
    }
    
    async deleteLink(linkId) {
        if (typeof openConfirmDialog !== 'function' || !await openConfirmDialog({
            title: '删除友情链接',
            message: '确定要删除这个友情链接吗？',
            danger: true,
        })) {
            return;
        }
        
        try {
            const response = await fetch(`/api/friend-links/${linkId}`, {
                method: 'DELETE',
                headers: UserManager.createHeaders()
            });
            
            if (response.ok) {
                this.showSuccess('友情链接删除成功');
                await this.loadFriendLinks();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || '删除失败');
            }
        } catch (error) {
            console.error('删除友情链接失败:', error);
            this.showError('删除失败，请重试');
        }
    }
    
    showModal(title, buttonText, data = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-root';
        modal.innerHTML = `
            <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="friendLinkModalTitle">
                <div class="modal-header">
                    <h3 class="modal-title" id="friendLinkModalTitle">${title}</h3>
                    <button type="button" class="modal-close" aria-label="关闭" onclick="this.closest('.modal-root').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="modalLinkForm">
                        <div class="form-group">
                            <label class="form-label" for="modalLinkName">链接名称</label>
                            <input type="text" id="modalLinkName" class="form-input" name="subject" value="${this.escapeHtml(data.subject || '')}" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="modalLinkUrl">链接地址</label>
                            <input type="url" id="modalLinkUrl" class="form-input" name="linkstr" value="${this.escapeHtml(data.linkstr || '')}" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="modalLinkOrder">排序</label>
                            <input type="number" id="modalLinkOrder" class="form-input" name="ordernum" value="${data.ordernum || 0}" min="0">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-sm btn-icon-only" title="取消" aria-label="取消" onclick="this.closest('.modal-root').remove()">${typeof Icons !== 'undefined' ? Icons.asBtnIcon(Icons.close) : '取消'}</button>
                    <button type="button" class="btn btn-primary btn-sm" onclick="window.friendLinksManager.handleModalSubmit()">${buttonText}</button>
                </div>
            </div>
        `;

        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
        
        // 聚焦到第一个输入框
        const firstInput = modal.querySelector('#modalLinkName');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    handleModalSubmit() {
        const form = document.getElementById('modalLinkForm');
        const formData = new FormData(form);
        const linkData = {
            subject: formData.get('subject').trim(),
            linkstr: formData.get('linkstr').trim(),
            ordernum: parseInt(formData.get('ordernum')) || 0
        };
        
        // 验证数据
        if (!linkData.subject || !linkData.linkstr) {
            this.showError('请填写完整的链接信息');
            return;
        }
        
        if (linkData.linkstr && !this.isValidUrl(linkData.linkstr)) {
            this.showError('请输入有效的URL地址');
            return;
        }
        
        // 关闭模态框
        const modal = document.querySelector('.modal-root');
        if (modal) {
            modal.remove();
        }
        
        // 执行保存操作
        this.saveLinkData(linkData);
    }

    async saveLinkData(linkData) {
        try {
            if (this.editingLinkId) {
                await this.updateLink(this.editingLinkId, linkData);
            } else {
                await this.createLink(linkData);
            }
            // 注意：loadFriendLinks 已经在 createLink 和 updateLink 方法中调用了
        } catch (error) {
            console.error('保存友情链接失败:', error);
            this.showError('保存失败，请重试');
        }
    }

    resetForm() {
        // 这个方法现在主要用于重置编辑状态
        this.editingLinkId = null;
    }
    
    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showMessage(message, type) {
        const existingMessage = document.querySelector('.page-toast');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'error' ? 'page-toast page-toast-error' : 'page-toast page-toast-success';
        messageDiv.textContent = message;

        const container = document.querySelector('.management-container');
        if (container) {
            container.insertBefore(messageDiv, container.firstChild);
        } else {
            document.body.insertBefore(messageDiv, document.body.firstChild);
        }
        
        // 3秒后自动移除
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.friendLinksManager = new FriendLinksManager();
});
