#!/bin/bash
# Docker 登录问题诊断脚本
# 在容器内运行此脚本来诊断登录问题

echo "🔍 Docker 登录问题诊断"
echo "=================================="
echo ""

# 检查 Python 版本
echo "1. Python 环境："
python3 --version
echo ""

# 检查关键依赖版本
echo "2. 关键依赖版本："
python3 << 'PYTHON_EOF'
import sys

packages = ['passlib', 'bcrypt', 'fastapi', 'sqlmodel']
for pkg in packages:
    try:
        if pkg == 'passlib':
            import passlib
            print(f"   {pkg}: {passlib.__version__}")
        elif pkg == 'bcrypt':
            import bcrypt
            # bcrypt 可能没有 __version__，尝试其他方法
            try:
                print(f"   {pkg}: {bcrypt.__version__}")
            except:
                try:
                    import pkg_resources
                    version = pkg_resources.get_distribution('bcrypt').version
                    print(f"   {pkg}: {version}")
                except:
                    print(f"   {pkg}: 已安装（版本未知）")
        elif pkg == 'fastapi':
            import fastapi
            print(f"   {pkg}: {fastapi.__version__}")
        elif pkg == 'sqlmodel':
            import sqlmodel
            print(f"   {pkg}: {sqlmodel.__version__}")
    except ImportError as e:
        print(f"   {pkg}: ❌ 未安装 - {e}")
    except Exception as e:
        print(f"   {pkg}: ⚠️  检查失败 - {e}")

# 检查 bcrypt 和 passlib 兼容性
print("\n3. bcrypt 和 passlib 兼容性检查：")
try:
    from passlib.context import CryptContext
    import bcrypt
    
    # 尝试创建 CryptContext
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        print("   ✅ CryptContext 创建成功")
        
        # 尝试哈希一个测试密码
        test_password = "test123"
        try:
            md5_hash = __import__('hashlib').md5(test_password.encode()).hexdigest()
            hashed = pwd_context.hash(md5_hash)
            print("   ✅ 密码哈希功能正常")
            
            # 尝试验证
            if pwd_context.verify(md5_hash, hashed):
                print("   ✅ 密码验证功能正常")
            else:
                print("   ❌ 密码验证失败")
        except Exception as e:
            print(f"   ❌ 密码哈希/验证失败: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"   ❌ CryptContext 创建失败: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

PYTHON_EOF

echo ""
echo "4. 检查 bcrypt 版本兼容性问题："
python3 << 'PYTHON_EOF'
try:
    import bcrypt
    # 检查是否有 __about__ 属性（新版本没有）
    if hasattr(bcrypt, '__about__'):
        print("   ✅ bcrypt 有 __about__ 属性（旧版本）")
        try:
            version = bcrypt.__about__.__version__
            print(f"   bcrypt 版本: {version}")
        except:
            print("   ⚠️  无法读取版本信息")
    else:
        print("   ⚠️  bcrypt 没有 __about__ 属性（可能是新版本，与 passlib 1.7.4 不兼容）")
        print("   建议：固定 bcrypt 版本到 4.0.1")
        
        # 尝试通过其他方式获取版本
        try:
            import pkg_resources
            version = pkg_resources.get_distribution('bcrypt').version
            print(f"   bcrypt 实际版本: {version}")
            if version.startswith('4.1') or version.startswith('5.'):
                print("   ❌ 版本不兼容！需要降级到 4.0.1")
        except:
            pass
except ImportError:
    print("   ❌ bcrypt 未安装")
except Exception as e:
    print(f"   ❌ 检查失败: {e}")
PYTHON_EOF

echo ""
echo "5. 测试密码验证逻辑："
python3 << 'PYTHON_EOF'
import hashlib
from passlib.context import CryptContext

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # 测试密码
    test_password = "test123"
    md5_hash = hashlib.md5(test_password.encode()).hexdigest()
    
    # 创建哈希（模拟注册）
    print("   创建测试密码哈希...")
    stored_hash = pwd_context.hash(md5_hash)
    print(f"   ✅ 哈希创建成功: {stored_hash[:20]}...")
    
    # 验证密码（模拟登录）
    print("   验证密码...")
    result1 = pwd_context.verify(md5_hash, stored_hash)
    print(f"   测试1 - MD5+bcrypt验证: {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 测试直接bcrypt（旧格式）
    direct_hash = pwd_context.hash(test_password)
    result2 = pwd_context.verify(test_password, direct_hash)
    print(f"   测试2 - 直接bcrypt验证: {'✅ 成功' if result2 else '❌ 失败'}")
    
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF

echo ""
echo "=================================="
echo "诊断完成"
echo ""
echo "如果发现 bcrypt 版本不兼容问题，请："
echo "1. 在 requirements-prod.txt 中添加: bcrypt==4.0.1"
echo "2. 重新构建 Docker 镜像"
