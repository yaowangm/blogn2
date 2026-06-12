/**
 * 为动态加载的 /static/ 资源追加与页面一致的 ?v= 版本号。
 * window.__BLOGN_STATIC_VERSION__ 由服务端在 <head> 内注入。
 */
(function () {
    const version = window.__BLOGN_STATIC_VERSION__ || '';

    function appendVersion(path) {
        if (!path || !path.startsWith('/static/') || !version || path.includes('v=')) {
            return path;
        }
        const separator = path.includes('?') ? '&' : '?';
        return `${path}${separator}v=${encodeURIComponent(version)}`;
    }

    window.BlognStatic = {
        version,
        url: appendVersion,
    };
})();
