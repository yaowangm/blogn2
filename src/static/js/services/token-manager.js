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
        
        // 监听用户活动，在用户活跃时主动刷新令牌
        this.setupUserActivityListener();
        
        // 设置全局请求拦截器
        this.setupGlobalFetchInterceptor();
    }

    /**
     * 设置用户活动监听器
     */
    setupUserActivityListener() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        // 监听用户活动事件，在用户活跃时检查令牌
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.checkAndRefreshToken();
            }, { passive: true });
        });
        
        // 页面可见性变化时也检查令牌
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkAndRefreshToken();
            }
        });
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
            // 检查访问令牌是否即将过期（提前5分钟刷新）
            if (this.isTokenExpiringSoon(accessToken)) {
                const refreshed = await this.refreshAccessToken(refreshToken);
                if (!refreshed) {
                    // 只有在刷新失败且令牌确实过期时才清除
                    const payload = this.decodeToken(accessToken);
                    if (payload && payload.exp) {
                        const now = Math.floor(Date.now() / 1000);
                        if (payload.exp <= now) {
                            this.clearTokens();
                        }
                    }
                }
                return refreshed;
            }
        } catch (error) {
            console.error('令牌检查失败:', error);
            // 不要立即清除令牌，让用户继续使用直到真正过期
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
            
            // 如果令牌在5分钟内过期，则刷新（提前更长时间）
            return expiresIn <= 300;
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
                // 不要立即清除令牌，让调用者决定如何处理
                console.error('刷新令牌失败:', response.status, response.statusText);
                return false;
            }
        } catch (error) {
            console.error('刷新访问令牌失败:', error);
            // 网络错误等情况下不要清除令牌
            return false;
        }
    }

    /**
     * 获取有效的访问令牌
     */
    async getValidAccessToken() {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!accessToken || !refreshToken) return null;

        // 策略1：提前刷新（减少失败请求）
        if (this.isTokenExpiringSoon(accessToken)) {
            const refreshed = await this.refreshAccessToken(refreshToken);
            if (refreshed) {
                return localStorage.getItem('access_token');
            }
        }

        // 策略2：过期后自动刷新（兜底机制）
        const payload = this.decodeToken(accessToken);
        if (payload && payload.exp) {
            const now = Math.floor(Date.now() / 1000);
            if (payload.exp <= now) {
                // 令牌已过期，立即刷新
                const refreshed = await this.refreshAccessToken(refreshToken);
                if (refreshed) {
                    return localStorage.getItem('access_token');
                }
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

    /**
     * 设置全局请求拦截器
     */
    setupGlobalFetchInterceptor() {
        try {
            // 防重复刷新的标志
            let isRefreshing = false;
            let refreshPromise = null;
            let hasRetried = false; // 是否已经重试过
            
            // 全局请求拦截器
            const originalFetch = window.fetch;
            window.fetch = async function(...args) {
                try {
                    // 只拦截API请求，避免影响页面资源加载
                    const url = args[0];
                    const isApiRequest = typeof url === 'string' && (
                        url.startsWith('/api/') || 
                        url.startsWith('http://localhost:') ||
                        url.startsWith('https://')
                    );
                    
                    if (!isApiRequest) {
                        // 非API请求，直接使用原始fetch
                        return await originalFetch(...args);
                    }
                    
                    const response = await originalFetch(...args);
                    
                    if (response.status === 401 && !hasRetried) {
                        // 防止重复刷新
                        if (isRefreshing) {
                            // 如果正在刷新，等待刷新完成
                            if (refreshPromise) {
                                await refreshPromise;
                                // 刷新完成后，使用新令牌重新发起请求
                                const newToken = localStorage.getItem('access_token');
                                if (newToken) {
                                    hasRetried = true;
                                    const newHeaders = new Headers(args[1]?.headers);
                                    newHeaders.set('Authorization', `Bearer ${newToken}`);
                                    
                                    const newArgs = [...args];
                                    if (newArgs[1]) {
                                        newArgs[1] = { ...newArgs[1], headers: newHeaders };
                                    } else {
                                        newArgs[1] = { headers: newHeaders };
                                    }
                                    
                                    return await originalFetch(...newArgs);
                                }
                            }
                        } else {
                            // 开始刷新令牌
                            isRefreshing = true;
                            refreshPromise = window.tokenManager.checkAndRefreshToken();
                            
                            try {
                                const refreshed = await refreshPromise;
                                if (refreshed) {
                                    // 刷新成功，使用新令牌重新发起请求
                                    const newToken = localStorage.getItem('access_token');
                                    if (newToken) {
                                        hasRetried = true;
                                        const newHeaders = new Headers(args[1]?.headers);
                                        newHeaders.set('Authorization', `Bearer ${newToken}`);
                                        
                                        const newArgs = [...args];
                                        if (newArgs[1]) {
                                            newArgs[1] = { ...newArgs[1], headers: newHeaders };
                                        } else {
                                            newArgs[1] = { headers: newHeaders };
                                        }
                                        
                                        return await originalFetch(...newArgs);
                                    }
                                }
                            } finally {
                                // 重置刷新状态
                                isRefreshing = false;
                                refreshPromise = null;
                            }
                        }
                    }
                    
                    // 重置重试标志（成功响应或非401错误）
                    if (response.status !== 401) {
                        hasRetried = false;
                    }
                    
                    return response;
                } catch (error) {
                    console.error('Fetch拦截器错误:', error);
                    // 出错时回退到原始fetch
                    return await originalFetch(...args);
                }
            };
        } catch (error) {
            console.error('设置全局请求拦截器失败:', error);
        }
    }
}

// 创建全局实例
window.tokenManager = new TokenManager();
