/**
 * 令牌管理服务
 * 负责JWT令牌的存储、验证和自动刷新
 */
class TokenManager {
    constructor() {
        this.refreshTimeout = null;
        this.init();
    }

    init() {
        // 检查是否有有效的令牌
        this.checkAndRefreshToken();
        
        // 设置定期检查（每5分钟检查一次）
        setInterval(() => {
            this.checkAndRefreshToken();
        }, 5 * 60 * 1000);
    }

    /**
     * 检查并刷新令牌
     */
    async checkAndRefreshToken() {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!accessToken || !refreshToken) {
            return false;
        }

        try {
            // 检查访问令牌是否即将过期（提前2分钟刷新）
            if (this.isTokenExpiringSoon(accessToken)) {
                return await this.refreshAccessToken(refreshToken);
            }
        } catch (error) {
            console.error('令牌检查失败:', error);
            this.clearTokens();
            return false;
        }
        
        return true;
    }

    /**
     * 检查令牌是否即将过期
     */
    isTokenExpiringSoon(token) {
        try {
            const payload = this.decodeToken(token);
            if (!payload || !payload.exp) return true;
            
            const now = Math.floor(Date.now() / 1000);
            const expiresIn = payload.exp - now;
            
            // 如果令牌在2分钟内过期，则刷新
            return expiresIn <= 120;
        } catch (error) {
            console.error('令牌解析失败:', error);
            return true;
        }
    }

    /**
     * 解码JWT令牌（不验证签名）
     */
    decodeToken(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('令牌解码失败:', error);
            return null;
        }
    }

    /**
     * 刷新访问令牌
     */
    async refreshAccessToken(refreshToken) {
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                
                // 触发令牌刷新事件
                window.dispatchEvent(new CustomEvent('tokenRefreshed', { 
                    detail: { access_token: data.access_token } 
                }));
                
                return true;
            } else {
                throw new Error('刷新令牌失败');
            }
        } catch (error) {
            console.error('刷新访问令牌失败:', error);
            this.clearTokens();
            return false;
        }
    }

    /**
     * 获取有效的访问令牌
     */
    async getValidAccessToken() {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) return null;

        // 如果令牌即将过期，先刷新
        if (this.isTokenExpiringSoon(accessToken)) {
            const refreshed = await this.checkAndRefreshToken();
            if (refreshed) {
                return localStorage.getItem('access_token');
            }
        }

        return accessToken;
    }

    /**
     * 验证令牌有效性
     */
    async validateToken() {
        const token = await this.getValidAccessToken();
        if (!token) return false;

        try {
            const response = await fetch('/api/auth/validate', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            return response.ok;
        } catch (error) {
            console.error('令牌验证失败:', error);
            return false;
        }
    }

    /**
     * 清除所有令牌
     */
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        
        // 触发令牌清除事件
        window.dispatchEvent(new CustomEvent('tokensCleared'));
    }

    /**
     * 设置令牌
     */
    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }
}

// 创建全局实例
window.tokenManager = new TokenManager();

export default TokenManager;
