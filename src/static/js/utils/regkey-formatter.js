/**
 * 注册码格式化工具
 * 提供注册码格式化的通用功能，可被其他模块引用
 */

/**
 * 格式化注册码，每5个字符后添加"-"作为间隔符
 * 例如：E123B4354D01807B0D5B7EF45 -> E123B-4354D-01807-B0D5B-7EF45
 * 
 * @param {string} regkey - 原始注册码字符串
 * @returns {string} 格式化后的注册码
 */
function formatRegKey(regkey) {
    if (!regkey || typeof regkey !== 'string') return regkey;
    
    // 移除可能存在的现有分隔符
    const cleanRegkey = regkey.replace(/-/g, '');
    
    // 每5个字符分组，用"-"连接
    const formatted = cleanRegkey.match(/.{1,5}/g)?.join('-') || cleanRegkey;
    
    return formatted;
}

/**
 * 移除注册码中的所有分隔符，返回纯字符串
 * 例如：E123B-4354D-01807-B0D5B-7EF45 -> E123B4354D01807B0D5B7EF45
 * 
 * @param {string} formattedRegkey - 格式化后的注册码
 * @returns {string} 纯字符串格式的注册码
 */
function cleanRegKey(formattedRegkey) {
    if (!formattedRegkey || typeof formattedRegkey !== 'string') return formattedRegkey;
    
    return formattedRegkey.replace(/-/g, '');
}

/**
 * 验证注册码格式是否正确
 * 检查是否只包含字母和数字，长度是否合理
 * 
 * @param {string} regkey - 注册码字符串
 * @returns {boolean} 格式是否正确
 */
function validateRegKeyFormat(regkey) {
    if (!regkey || typeof regkey !== 'string') return false;
    
    // 移除分隔符后检查
    const cleanRegkey = cleanRegKey(regkey);
    
    // 检查是否只包含字母和数字
    const validChars = /^[A-Z0-9]+$/i;
    if (!validChars.test(cleanRegkey)) return false;
    
    // 检查长度是否合理（通常16-32位）
    if (cleanRegkey.length < 16 || cleanRegkey.length > 32) return false;
    
    return true;
}

/**
 * 获取注册码的显示长度（包含分隔符）
 * 
 * @param {string} regkey - 注册码字符串
 * @returns {number} 显示长度
 */
function getRegKeyDisplayLength(regkey) {
    if (!regkey || typeof regkey !== 'string') return 0;
    
    const cleanRegkey = cleanRegKey(regkey);
    const groups = Math.ceil(cleanRegkey.length / 5);
    
    // 总长度 = 字符数 + 分隔符数
    return cleanRegkey.length + Math.max(0, groups - 1);
}

// 为了兼容性，也在全局对象上提供这些函数
if (typeof window !== 'undefined') {
    window.RegKeyFormatter = {
        format: formatRegKey,
        clean: cleanRegKey,
        validate: validateRegKeyFormat,
        getDisplayLength: getRegKeyDisplayLength
    };
}
