/**
 * 令牌管理服务
 * 负责JWT令牌的存储、验证和自动刷新
 */
class TokenManager {
    constructor() {
        this._originalFetch = window.fetch.bind(window);
        this._refreshPromise = null;
        this.init();
    }

    init() {
        this.checkAndRefreshToken();
        this.setupUserActivityListener();
        this.setupGlobalFetchInterceptor();
    }

    setupUserActivityListener() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        events.forEach((event) => {
            document.addEventListener(event, () => this.checkAndRefreshToken(), { passive: true });
        });
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkAndRefreshToken();
            }
        });
    }

    async checkAndRefreshToken() {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken || !localStorage.getItem('refresh_token')) {
            return false;
        }

        try {
            if (!this.isTokenExpiringSoon(accessToken)) {
                return true;
            }
            const refreshed = await this._refreshTokensShared();
            if (!refreshed) {
                const payload = this.decodeToken(accessToken);
                if (payload?.exp && payload.exp <= Math.floor(Date.now() / 1000)) {
                    this.clearTokens();
                }
            }
            return refreshed;
        } catch (error) {
            console.error('令牌检查失败:', error);
            return false;
        }
    }

    isTokenExpiringSoon(token) {
        try {
            const payload = this.decodeToken(token);
            if (!payload?.exp) {
                return true;
            }
            return payload.exp - Math.floor(Date.now() / 1000) <= 300;
        } catch (error) {
            console.error('令牌解析失败:', error);
            return true;
        }
    }

    decodeToken(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => (
                '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
            )).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('令牌解码失败:', error);
            return null;
        }
    }

    async getValidAccessToken() {
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken || !localStorage.getItem('refresh_token')) {
            return null;
        }
        if (this.isTokenExpiringSoon(accessToken)) {
            const refreshed = await this._refreshTokensShared();
            if (refreshed) {
                return localStorage.getItem('access_token');
            }
        }
        return accessToken;
    }

    async validateToken() {
        const token = await this.getValidAccessToken();
        if (!token) {
            return false;
        }

        try {
            const response = await fetch('/api/auth/validate', {
                headers: { Authorization: `Bearer ${token}` }
            });
            return response.ok;
        } catch (error) {
            console.error('令牌验证失败:', error);
            return false;
        }
    }

    clearTokens() {
        UserManager.clearPostFormDrafts();
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_info');
        window.dispatchEvent(new CustomEvent('tokensCleared'));
    }

    _refreshTokensShared() {
        if (this._refreshPromise) {
            return this._refreshPromise;
        }
        this._refreshPromise = this._fetchRefreshToken().finally(() => {
            this._refreshPromise = null;
        });
        return this._refreshPromise;
    }

    async _fetchRefreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await this._originalFetch('/api/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (!response.ok) {
                console.error('刷新令牌失败:', response.status, response.statusText);
                return false;
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            window.dispatchEvent(new CustomEvent('tokenRefreshed', {
                detail: { access_token: data.access_token }
            }));
            return true;
        } catch (error) {
            console.error('刷新访问令牌失败:', error);
            return false;
        }
    }

    setupGlobalFetchInterceptor() {
        const originalFetch = this._originalFetch;
        const tokenManager = this;

        window.fetch = async function (...args) {
            try {
                const requestUrl = typeof args[0] === 'string'
                    ? args[0]
                    : (args[0]?.url || '');

                const isApiRequest = requestUrl.startsWith('/api/')
                    || requestUrl.startsWith('http://localhost:')
                    || requestUrl.startsWith('https://');

                if (!isApiRequest) {
                    return await originalFetch(...args);
                }

                const skipAuthRetry = requestUrl.includes('/api/auth/refresh')
                    || requestUrl.includes('/api/auth/login');

                const response = await originalFetch(...args);
                if (skipAuthRetry || response.status !== 401 || !localStorage.getItem('refresh_token')) {
                    return response;
                }

                const refreshed = await tokenManager._refreshTokensShared();
                if (!refreshed) {
                    return response;
                }

                const newToken = localStorage.getItem('access_token');
                if (!newToken) {
                    return response;
                }

                const newHeaders = new Headers(args[1]?.headers || {});
                newHeaders.set('Authorization', `Bearer ${newToken}`);
                return await originalFetch(args[0], { ...(args[1] || {}), headers: newHeaders });
            } catch (error) {
                console.error('Fetch拦截器错误:', error);
                return await originalFetch(...args);
            }
        };
    }
}

window.tokenManager = new TokenManager();
