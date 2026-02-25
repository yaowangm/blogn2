/**
 * 前端密码规则校验（与后端 src/utils/password_validation.py 一致）
 * 8–30 字符、至少大小写+数字、仅可打印 ASCII。
 * 供注册、重置密码、用户列表重置弹窗、个人资料卡等共用。
 * @param {string} pwd - 待校验密码
 * @returns {string|null} 错误信息或 null 表示通过
 */
function passwordRuleError(pwd) {
    if (!pwd) return '密码不能为空';
    if (pwd.length < 8) return '密码至少需要8个字符';
    if (pwd.length > 30) return '密码不能超过30个字符';
    for (var i = 0; i < pwd.length; i++) {
        var c = pwd.charCodeAt(i);
        if (c < 0x20 || c > 0x7E) return '密码只能包含可打印 ASCII 字符（空格到波浪号 ~）';
    }
    if (!/[A-Z]/.test(pwd)) return '密码至少需要包含一个大写字母';
    if (!/[a-z]/.test(pwd)) return '密码至少需要包含一个小写字母';
    if (!/[0-9]/.test(pwd)) return '密码至少需要包含一个数字';
    return null;
}

if (typeof window !== 'undefined') {
    window.passwordRuleError = passwordRuleError;
}
