/**
 * 注册码管理页面脚本
 * 负责注册码列表的加载、显示和兑换功能
 */

class RegistrationCodeManager {
    constructor() {
        this.regkeyData = [];
        this.currentUser = null;
        this.init();
    }

    async init() {
        // 检查用户登录状态
        await this.checkAuthStatus();
        
        // 绑定事件
        this.bindEvents();
        
        // 加载用户积分
        await this.loadUserPoints();
        
        // 加载注册码数据
        await this.loadRegKeyData();
        
        // 更新兑换按钮状态
        this.updateExchangeButtonState();
    }

    async checkAuthStatus() {
        try {
            // 检查本地存储的认证状态（与header-component保持一致）
            const token = localStorage.getItem('access_token');
            const userInfo = localStorage.getItem('user_info');
            
            if (!token || !userInfo) {
                // 没有认证信息，重定向到首页（让用户通过登录模态框登录）
                window.location.href = '/';
                return;
            }
            
            try {
                this.currentUser = JSON.parse(userInfo);
            } catch (error) {
                console.error('解析用户信息失败:', error);
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_info');
                window.location.href = '/';
                return;
            }
            
            // 验证令牌是否有效（可选，如果令牌过期会通过API调用发现）
            
        } catch (error) {
            console.error('检查认证状态失败:', error);
            window.location.href = '/';
        }
    }

    bindEvents() {
        const exchangeBtn = document.getElementById('exchangeBtn');
        if (exchangeBtn) {
            exchangeBtn.addEventListener('click', () => this.handleExchange());
        }
    }

    async loadUserPoints() {
        try {
            // 永远从服务端获取积分信息
            let token;
            if (window.tokenManager) {
                token = await window.tokenManager.getValidAccessToken();
            } else {
                token = localStorage.getItem('access_token');
            }
            
            if (!token) {
                throw new Error('未找到访问令牌');
            }
            
            // 获取用户详细信息（包含积分）
            if (!this.currentUser || !this.currentUser.id) {
                throw new Error('用户信息不完整');
            }
            
            const response = await fetch(`/api/users/${this.currentUser.id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const userData = await response.json();
            const userPoints = userData.point || 0;
            
            // 更新页面显示的积分
            const pointsElement = document.getElementById('userPoints');
            if (pointsElement) {
                pointsElement.textContent = userPoints;
            }
            
            // 保存用户积分到实例变量，用于兑换时的验证
            this.userPoints = userPoints;
            
        } catch (error) {
            console.error('加载用户积分失败:', error);
            // 如果获取积分失败，显示默认值
            const pointsElement = document.getElementById('userPoints');
            if (pointsElement) {
                pointsElement.textContent = '--';
            }
        }
    }

    async loadRegKeyData() {
        const container = document.getElementById('regkeyTableContainer');
        if (!container) return;

        try {
            container.innerHTML = '<div class="loading">加载中...</div>';
            
            // 使用令牌管理服务获取有效令牌
            let token;
            if (window.tokenManager) {
                token = await window.tokenManager.getValidAccessToken();
            } else {
                token = localStorage.getItem('access_token');
            }
            
            if (!token) {
                throw new Error('未找到访问令牌');
            }
            
            const response = await fetch('/api/regkey/list', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.regkeyData = data.regkeys || [];
            
            this.renderRegKeyTable();
        } catch (error) {
            console.error('加载注册码数据失败:', error);
            
            // 检查是否是认证错误
            if (error.message && error.message.includes('401')) {
                // 清除过期的认证信息
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_info');
                
                container.innerHTML = `
                    <div class="error">
                        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        <p>登录已过期，请重新登录</p>
                        <button class="login-btn" onclick="window.location.href='/'">
                            返回首页登录
                        </button>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="error">
                        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        加载失败，请稍后重试
                    </div>
                `;
            }
        }
    }

    renderRegKeyTable() {
        const container = document.getElementById('regkeyTableContainer');
        if (!container) return;

        if (this.regkeyData.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 0 1 21.75 8.25z"></path>
                    </svg>
                    暂无注册码数据
                </div>
            `;
            return;
        }

        const tableHTML = `
            <table class="regkey-table">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>注册码</th>
                        <th>申请者</th>
                        <th>使用者</th>
                        <th>状态</th>
                        <th>创建时间</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.regkeyData.map((item, index) => `
                        <tr>
                            <td>${index + 1}</td>
                            <td><code>${this.escapeHtml(window.RegKeyFormatter.format(item.regkey))}</code></td>
                            <td>
                                ${item.ownerid && item.owner_name ? 
                                    `<a href="/profile/${item.ownerid}" class="user-link" target="_blank" rel="noopener noreferrer">${this.escapeHtml(item.owner_name)}</a>` : 
                                    this.escapeHtml(item.owner_name || '未知')
                                }
                            </td>
                            <td>
                                ${item.userid && item.user_name ? 
                                    `<a href="/profile/${item.userid}" class="user-link" target="_blank" rel="noopener noreferrer">${this.escapeHtml(item.user_name)}</a>` : 
                                    (item.user_name ? this.escapeHtml(item.user_name) : '-')
                                }
                            </td>
                            <td>
                                <span class="status-badge ${item.status === 1 ? 'status-unused' : 'status-used'}">
                                    ${item.status === 1 ? '未使用' : '已使用'}
                                </span>
                            </td>
                            <td>${this.formatDateTime(item.createtime)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.innerHTML = tableHTML;
    }

    updateExchangeButtonState() {
        const exchangeBtn = document.getElementById('exchangeBtn');
        if (!exchangeBtn || !this.currentUser) return;

        // 使用实时积分数据
        const currentPoints = this.userPoints !== undefined ? this.userPoints : this.currentUser.point;
        const hasEnoughPoints = currentPoints >= 10;
        exchangeBtn.disabled = !hasEnoughPoints;
        
        if (!hasEnoughPoints) {
            exchangeBtn.title = `积分不足，当前积分：${currentPoints}，需要10积分`;
        } else {
            exchangeBtn.title = `当前积分：${currentPoints}，兑换后将扣除10积分`;
        }
    }

    async handleExchange() {
        if (!this.currentUser) {
            alert('请先登录');
            return;
        }

        // 使用实时积分数据
        const currentPoints = this.userPoints !== undefined ? this.userPoints : this.currentUser.point;
        
        if (currentPoints < 10) {
            alert(`积分不足，当前积分：${currentPoints}，需要10积分`);
            return;
        }

        if (!confirm(`确定要使用10积分兑换一个注册码吗？\n当前积分：${currentPoints}`)) {
            return;
        }

        try {
            // 使用令牌管理服务获取有效令牌
            let token;
            if (window.tokenManager) {
                token = await window.tokenManager.getValidAccessToken();
            } else {
                token = localStorage.getItem('access_token');
            }
            
            if (!token) {
                throw new Error('未找到访问令牌');
            }
            
            const response = await fetch('/api/regkey/exchange', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '兑换失败');
            }

            const result = await response.json();
            const formattedRegkey = window.RegKeyFormatter.format(result.regkey);
            alert(`兑换成功！\n注册码：${formattedRegkey}\n请妥善保管，注册码只能使用一次。`);
            
            // 刷新数据
            await this.loadRegKeyData();
            
            // 更新用户积分信息
            this.currentUser.point -= 10;
            this.userPoints = result.remaining_points || (this.userPoints - 10);
            
            // 更新页面显示的积分
            const pointsElement = document.getElementById('userPoints');
            if (pointsElement) {
                pointsElement.textContent = this.userPoints;
            }
            
            this.updateExchangeButtonState();
            
        } catch (error) {
            console.error('兑换注册码失败:', error);
            
            // 检查是否是认证错误
            if (error.message && error.message.includes('401')) {
                // 清除过期的认证信息
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_info');
                alert('登录已过期，请重新登录');
                window.location.href = '/';
            } else {
                alert(`兑换失败：${error.message}`);
            }
        }
    }

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '-';
        try {
            const date = new Date(dateTimeStr);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateTimeStr;
        }
    }


}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new RegistrationCodeManager();
});
