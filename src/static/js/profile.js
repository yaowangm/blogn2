/**
 * 个人资料页面脚本
 * 处理页面初始化、数据加载和用户交互
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('个人资料页面加载完成');
    
    // 获取目标用户ID（从URL或当前登录用户）
    const targetUserId = getTargetUserId();
    
    // 检查用户认证状态
    checkAuthStatus();
    
    // 初始化页面
    initializePage(targetUserId);
});

/**
 * 获取目标用户ID
 * 从URL路径中提取用户ID，如果没有则返回当前登录用户的ID
 * @returns {number|null} 目标用户ID
 */
function getTargetUserId() {
    const pathSegments = window.location.pathname.split('/');
    const profileIndex = pathSegments.indexOf('profile');
    
    if (profileIndex !== -1 && pathSegments[profileIndex + 1]) {
        const userId = parseInt(pathSegments[profileIndex + 1]);
        if (!isNaN(userId) && userId > 0) {
            console.log('从URL获取到目标用户ID:', userId);
            return userId;
        }
    }
    
    // 如果没有指定用户ID，则使用当前登录用户
    const userInfo = localStorage.getItem('user_info');
    if (userInfo) {
        try {
            const user = JSON.parse(userInfo);
            console.log('使用当前登录用户ID:', user.id);
            return user.id;
        } catch (error) {
            console.error('解析用户信息失败:', error);
        }
    }
    
    console.log('无法获取用户ID');
    return null;
}

/**
 * 检查用户认证状态
 */
function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    const userInfo = localStorage.getItem('user_info');
    
    if (!token || !userInfo) {
        // 用户未登录，在开发环境中使用测试数据
        console.log('用户未登录，使用测试数据');
        // 为了测试，我们可以设置一些测试数据
        // 在实际生产环境中，这里应该重定向到登录页面
        // window.location.href = '/';
        return;
    }
    
    try {
        const user = JSON.parse(userInfo);
        console.log('当前用户:', user.name);
    } catch (error) {
        console.error('解析用户信息失败:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        // 在开发环境中不重定向
        // window.location.href = '/';
    }
}

/**
 * 初始化页面
 * @param {number} targetUserId - 目标用户ID
 */
function initializePage(targetUserId) {
    // 设置页面标题
    updatePageTitle();
    
    // 将目标用户ID存储到全局变量，供组件使用
    window.targetUserId = targetUserId;
    
    // 添加页面加载完成事件
    window.addEventListener('load', function() {
        console.log('页面所有资源加载完成');
    });
}

/**
 * 更新页面标题
 */
function updatePageTitle() {
    // 如果有目标用户ID，需要从API获取用户信息来设置标题
    if (window.targetUserId) {
        // 标题将在用户数据加载完成后更新
        document.title = '个人资料 - BlogN2';
    } else {
        // 使用当前登录用户信息
        const userInfo = localStorage.getItem('user_info');
        if (userInfo) {
            try {
                const user = JSON.parse(userInfo);
                document.title = `${user.name}的个人资料 - BlogN2`;
            } catch (error) {
                console.error('更新页面标题失败:', error);
            }
        }
    }
}

/**
 * 格式化日期时间
 * @param {string} dateString - 日期字符串
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '未设置';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.error('日期格式化失败:', error);
        return '格式错误';
    }
}

/**
 * 获取用户身份文本
 * @param {number} state - 用户状态码
 * @returns {string} 身份文本
 */
function getUserStateText(state) {
    switch (state) {
        case 10: return '管理员';
        case 1: return '普通用户';
        case 0: return '已冻结';
        default: return '未知';
    }
}

/**
 * 显示错误消息
 * @param {string} message - 错误消息
 */
function showError(message) {
    console.error('页面错误:', message);
    
    // 可以在这里添加全局错误提示UI
    // 例如：显示一个toast通知
}

/**
 * 显示成功消息
 * @param {string} message - 成功消息
 */
function showSuccess(message) {
    console.log('页面成功:', message);
    
    // 可以在这里添加全局成功提示UI
    // 例如：显示一个toast通知
}
