/**
 * 管理友情链接页面脚本
 * 提供友情链接的增删改查功能
 */
class FriendLinksManager {
    constructor() {
        this.projectId = null;
        this.friendLinks = [];
        this.editingLinkId = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        // 获取项目ID
        this.projectId = this.getProjectIdFromUrl();
        if (!this.projectId) {
            this.showError('缺少项目ID参数');
            return;
        }
        
        // 检查用户权限
        this.checkUserPermissions();
        
        // 绑定事件
        this.bindEvents();
        
        // 加载友情链接列表
        this.loadFriendLinks();
    }
    
    getProjectIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('project_id');
    }
    
    async checkUserPermissions() {
        try {
            if (!UserManager.isLoggedIn()) {
                this.showError('请先登录');
                return;
            }
            
            const currentUser = UserManager.getCurrentUser();
            const isAdmin = currentUser.state === 10;
            
            // 检查是否为博客所有者
            const response = await fetch(`/api/projects/${this.projectId}`);
            if (!response.ok) {
                this.showError('无法获取博客信息');
                return;
            }
            
            const blogData = await response.json();
            const isOwner = currentUser.id === blogData.userid;
            
            if (!isOwner && !isAdmin) {
                this.showError('无权限管理该博客的友情链接');
                return;
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
            linksList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                        </svg>
                    </div>
                    <div class="empty-state-text">暂无友情链接</div>
                    <div class="empty-state-description">点击"添加链接"按钮开始添加友情链接</div>
                </div>
            `;
            return;
        }
        
        // 显示数量限制警告
        if (this.friendLinks.length >= 20) {
            linksList.innerHTML = `
                <div class="limit-warning">
                    ⚠️ 友情链接数量已达到上限（20个），无法继续添加
                </div>
            ` + this.renderLinksItems();
        } else {
            linksList.innerHTML = this.renderLinksItems();
        }
    }
    
    renderLinksItems() {
        return this.friendLinks.map(link => `
            <div class="link-item" data-link-id="${link.id}">
                <div class="link-info">
                    <div class="link-name" title="${this.escapeHtml(link.subject)}">
                        ${this.escapeHtml(link.subject)}
                    </div>
                    <div class="link-url" title="${this.escapeHtml(link.linkstr)}">
                        ${this.escapeHtml(link.linkstr)}
                    </div>
                </div>
                <div class="link-actions">
                    <button class="action-button edit-button" onclick="friendLinksManager.editLink(${link.id})">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        编辑
                    </button>
                    <button class="action-button delete-button" onclick="friendLinksManager.deleteLink(${link.id})">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        删除
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
        if (!confirm('确定要删除这个友情链接吗？')) {
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
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'friend-link-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>${title}</h3>
                        <button class="modal-close" onclick="this.closest('.friend-link-modal').remove()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="modalLinkForm">
                            <div class="form-group">
                                <label for="modalLinkName">链接名称</label>
                                <input type="text" id="modalLinkName" name="subject" value="${this.escapeHtml(data.subject || '')}" required>
                            </div>
                            <div class="form-group">
                                <label for="modalLinkUrl">链接地址</label>
                                <input type="url" id="modalLinkUrl" name="linkstr" value="${this.escapeHtml(data.linkstr || '')}" required>
                            </div>
                            <div class="form-group">
                                <label for="modalLinkOrder">排序</label>
                                <input type="number" id="modalLinkOrder" name="ordernum" value="${data.ordernum || 0}" min="0">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-cancel" onclick="this.closest('.friend-link-modal').remove()">取消</button>
                        <button type="button" class="btn-save" onclick="window.friendLinksManager.handleModalSubmit()">${buttonText}</button>
                    </div>
                </div>
            </div>
            <style>
                .friend-link-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 1000;
                }
                .modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .modal-content {
                    background: white;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 500px;
                    max-height: 90vh;
                    overflow-y: auto;
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid #e5e7eb;
                }
                .modal-header h3 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                }
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #6b7280;
                }
                .modal-body {
                    padding: 20px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 500;
                    color: #374151;
                }
                .form-group input {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    font-size: 14px;
                }
                .form-group input:focus {
                    outline: none;
                    border-color: #3b82f6;
                    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                }
                .modal-footer {
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                    padding: 20px;
                    border-top: 1px solid #e5e7eb;
                }
                .btn-cancel, .btn-save {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                }
                .btn-cancel {
                    background: #f3f4f6;
                    color: #374151;
                }
                .btn-cancel:hover {
                    background: #e5e7eb;
                }
                .btn-save {
                    background: #3b82f6;
                    color: white;
                }
                .btn-save:hover {
                    background: #2563eb;
                }
            </style>
        `;
        
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
        const modal = document.querySelector('.friend-link-modal');
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
        // 移除现有消息
        const existingMessage = document.querySelector('.error-message, .success-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
        messageDiv.textContent = message;
        
        // 在页面顶部显示消息
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.insertBefore(messageDiv, mainContent.firstChild);
        } else {
            // 如果找不到main元素，添加到body
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
