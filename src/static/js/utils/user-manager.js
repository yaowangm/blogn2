/**
 * 用户管理工具类
 * 提供统一的用户认证状态检查和用户信息获取功能
 */
class UserManager {
    /**
     * 检查用户是否已登录
     * @returns {boolean} 是否已登录
     */
    static isLoggedIn() {
        const token = localStorage.getItem('access_token');
        const userInfo = localStorage.getItem('user_info');
        return !!(token && userInfo);
    }

    /**
     * 获取当前用户ID
     * @returns {number} 用户ID，未登录返回0
     */
    static getCurrentUserId() {
        const userInfo = localStorage.getItem('user_info');
        if (userInfo) {
            try {
                const user = JSON.parse(userInfo);
                return user.id;
            } catch (e) {
                console.error('Failed to parse user info:', e);
            }
        }
        return 0; // 匿名用户返回0
    }

    /**
     * 获取当前用户信息
     * @returns {Object|null} 用户信息对象，未登录返回null
     */
    static getCurrentUser() {
        const userInfo = localStorage.getItem('user_info');
        if (userInfo) {
            try {
                return JSON.parse(userInfo);
            } catch (e) {
                console.error('Failed to parse user info:', e);
            }
        }
        return null;
    }

    /**
     * 获取访问令牌
     * @returns {string|null} 访问令牌，未登录返回null
     */
    static getAccessToken() {
        return localStorage.getItem('access_token');
    }

    /**
     * 检查用户是否为管理员
     * @returns {boolean} 是否为管理员
     */
    static isAdmin() {
        const user = this.getCurrentUser();
        return user && user.state === 10;
    }

    /**
     * 检查用户是否为作者
     * @param {number} authorId - 作者ID
     * @returns {boolean} 是否为作者
     */
    static isAuthor(authorId) {
        const currentUserId = this.getCurrentUserId();
        return currentUserId === authorId;
    }

    /**
     * 获取认证请求头
     * @returns {Object} 包含Authorization头的对象
     */
    static getAuthHeaders() {
        const headers = {};
        const token = this.getAccessToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    }

    /**
     * 创建带认证的请求头
     * @param {Object} additionalHeaders - 额外的请求头
     * @returns {Object} 包含认证头的完整请求头对象
     */
    static createHeaders(additionalHeaders = {}) {
        return {
            ...additionalHeaders,
            ...this.getAuthHeaders()
        };
    }
}

// 导出到全局作用域
window.UserManager = UserManager;
