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
            
            // 表单提交
            const form = document.getElementById('linkForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleFormSubmit();
                });
            }
            
            // 取消按钮
            const cancelBtn = document.getElementById('cancelBtn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.resetForm();
                });
            }
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
                    <div class="empty-state-icon">🔗</div>
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
                        ✏️ 编辑
                    </button>
                    <button class="action-button delete-button" onclick="friendLinksManager.deleteLink(${link.id})">
                        🗑️ 删除
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    showAddForm() {
        this.editingLinkId = null;
        this.resetForm();
        document.getElementById('formTitle').textContent = '添加友情链接';
        document.getElementById('submitBtn').textContent = '保存链接';
        
        // 显示表单区域
        const formSection = document.getElementById('formSection');
        if (formSection) {
            formSection.classList.remove('hidden');
            formSection.style.display = 'block';
            formSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        // 聚焦到第一个输入框
        const firstInput = document.getElementById('linkName');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
    
    async editLink(linkId) {
        const link = this.friendLinks.find(l => l.id === linkId);
        if (!link) return;
        
        this.editingLinkId = linkId;
        document.getElementById('linkName').value = link.subject;
        document.getElementById('linkUrl').value = link.linkstr;
        document.getElementById('linkOrder').value = link.ordernum || 0;
        
        document.getElementById('formTitle').textContent = '编辑友情链接';
        document.getElementById('submitBtn').textContent = '保存修改';
        
        // 显示表单区域
        const formSection = document.getElementById('formSection');
        if (formSection) {
            formSection.classList.remove('hidden');
            formSection.style.display = 'block';
            formSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        // 聚焦到第一个输入框
        const firstInput = document.getElementById('linkName');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
    
    async handleFormSubmit() {
        const formData = new FormData(document.getElementById('linkForm'));
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
        
        try {
            if (this.editingLinkId) {
                await this.updateLink(this.editingLinkId, linkData);
            } else {
                await this.createLink(linkData);
            }
        } catch (error) {
            console.error('保存友情链接失败:', error);
            this.showError('保存失败，请重试');
        }
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
    
    resetForm() {
        document.getElementById('linkForm').reset();
        document.getElementById('linkOrder').value = 0;
        this.editingLinkId = null;
        document.getElementById('formTitle').textContent = '添加友情链接';
        document.getElementById('submitBtn').textContent = '保存链接';
        
        // 隐藏表单区域
        const formSection = document.getElementById('formSection');
        if (formSection) {
            formSection.classList.add('hidden');
            formSection.style.display = 'none';
        }
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
        
        const formContent = document.querySelector('.form-content');
        formContent.insertBefore(messageDiv, formContent.firstChild);
        
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
