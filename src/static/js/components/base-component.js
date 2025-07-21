/**
 * 基础组件类
 * 提供所有Web组件共用的基础功能
 */
class BaseComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.metadata = null;
    }

    /**
     * 加载网站元数据
     * 所有组件共享的元数据加载逻辑
     */
    async loadMetadata() {
        try {
            const response = await fetch('/api/metadata');
            if (response.ok) {
                this.metadata = await response.json();
            } else {
                this.logError('Failed to load metadata', response.status);
                this.metadata = this.getDefaultMetadata();
            }
        } catch (error) {
            this.logError('Error loading metadata', error);
            this.metadata = this.getDefaultMetadata();
        }
    }

    /**
     * 统一的错误日志记录
     * @param {string} message - 错误消息
     * @param {any} error - 错误对象
     */
    logError(message, error) {
        console.error(`${message}:`, error);
        // 这里可以添加错误上报逻辑
    }

    /**
     * 获取默认元数据
     * 当API请求失败时使用的默认值
     */
    getDefaultMetadata() {
        return {
            site_name: 'BlogN',
            logo_url: '/static/images/logo.svg',
            user_count: 0,
            post_count: 0
        };
    }

    /**
     * 获取Logo URL
     * 根据当前主题返回相应的Logo URL
     */
    getLogoUrl() {
        const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const baseUrl = this.metadata?.logo_url || '/static/images/logo.svg';
        
        if (isDarkMode) {
            return baseUrl.replace('logo.svg', 'logo-dark.svg');
        } else {
            return baseUrl.replace('logo.svg', 'logo-light.svg');
        }
    }

    /**
     * 格式化日期
     * 将ISO日期字符串格式化为可读格式
     */
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return '昨天';
        } else if (diffDays < 7) {
            return `${diffDays}天前`;
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }

    /**
     * 截断文本
     * 将长文本截断到指定长度并添加省略号
     */
    truncateText(text, maxLength = 20) {
        if (!text) return '';
        
        const cleanText = text.replace(/\\r\\n/g, ' ').replace(/\\n/g, ' ').trim();
        return cleanText.length > maxLength 
            ? cleanText.substring(0, maxLength) + '...' 
            : cleanText;
    }

    /**
     * 创建加载状态HTML
     * 统一的加载状态显示
     */
    createLoadingHTML() {
        return `
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                color: var(--gray-500);
                font-size: 14px;
            ">
                <div style="
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--gray-200);
                    border-top: 2px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 8px;
                "></div>
                加载中...
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
    }

    /**
     * 创建错误状态HTML
     * 统一的错误状态显示
     */
    createErrorHTML(message = '加载失败') {
        return `
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                color: var(--red-500);
                font-size: 14px;
            ">
                <span style="margin-right: 8px;">⚠️</span>
                ${message}
            </div>
        `;
    }
}

// 注册基础组件（不直接使用，仅作为基类）
customElements.define('base-component', BaseComponent); 