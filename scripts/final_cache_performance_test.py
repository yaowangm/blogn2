#!/usr/bin/env python3
"""
最终缓存性能测试脚本
验证缓存系统的性能提升
通过检查日志文件中的SQL查询次数来确认缓存是否生效
自动开启/关闭缓存并比较结果
"""

import asyncio
import aiohttp
import time
import statistics
import json
import subprocess
import sys
import os
import re
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def modify_env_cache_setting(enable_cache: bool):
    """修改.env文件中的缓存设置"""
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"❌ .env文件不存在: {env_file}")
        return False
    
    try:
        # 读取当前.env文件内容
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换CACHE_ENABLE_CACHE设置
        pattern = r'^CACHE_ENABLE_CACHE\s*=\s*.*$'
        replacement = f'CACHE_ENABLE_CACHE = {"true" if enable_cache else "false"}'
        
        if re.search(pattern, content, re.MULTILINE):
            # 如果设置已存在，替换它
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            # 如果设置不存在，添加到文件末尾
            new_content = content.rstrip() + f'\n{replacement}\n'
        
        # 写回文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已{'启用' if enable_cache else '禁用'}缓存设置")
        return True
        
    except Exception as e:
        print(f"❌ 修改.env文件失败: {e}")
        return False

def restart_service():
    """重启blogn2服务"""
    try:
        print("🔄 重启blogn2服务...")
        result = subprocess.run(['sudo', 'blogn2-service', 'restart'], 
                              capture_output=True, text=True, check=True)
        print("✅ 服务重启成功")
        
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(5)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 重启服务失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 重启服务时发生错误: {e}")
        return False

async def wait_for_service_ready():
    """等待服务就绪"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/health", timeout=5) as response:
                    if response.status == 200:
                        print("✅ 服务已就绪")
                        return True
        except:
            pass
        
        if attempt < max_attempts - 1:
            print(f"⏳ 等待服务就绪... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    
    print("❌ 服务启动超时")
    return False

async def test_endpoint_cache(endpoint: str, log_file: str, cache_enabled: bool):
    """测试单个端点的缓存行为"""
    cache_status = "启用" if cache_enabled else "禁用"
    print(f"\n📊 测试端点: {endpoint} (缓存{cache_status})")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 第一次请求（缓存未命中）
        print("🔍 第一次请求（缓存未命中）:")
        start = time.time()
        async with session.get(f"http://localhost:8000{endpoint}") as response:
            data1 = await response.text()
        first_time = (time.time() - start) * 1000
        print(f"   响应时间: {first_time:.2f}ms")
        
        # 检查日志中的SQL查询
        await asyncio.sleep(1)
        sql_count = 0
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
                sql_count = content.count('INFO sqlalchemy.engine.Engine SELECT')
                print(f"   日志中的SQL查询次数: {sql_count}")
        
        # 第二次请求（缓存命中）
        print("\n🔍 第二次请求（缓存命中）:")
        start = time.time()
        async with session.get(f"http://localhost:8000{endpoint}") as response:
            data2 = await response.text()
        second_time = (time.time() - start) * 1000
        print(f"   响应时间: {second_time:.2f}ms")
        
        # 检查日志中的SQL查询
        await asyncio.sleep(1)
        sql_count2 = 0
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
                sql_count2 = content.count('INFO sqlalchemy.engine.Engine SELECT')
                print(f"   日志中的SQL查询次数: {sql_count2}")
        
        # 解析响应数据
        try:
            result1 = json.loads(data1)
            result2 = json.loads(data2)
            data_same = result1 == result2
            print(f"   响应数据相同: {data_same}")
        except json.JSONDecodeError as e:
            print(f"   解析响应数据失败: {e}")
            data_same = False
        
        # 分析缓存行为
        cache_effective = False
        if sql_count > 0 and sql_count2 == sql_count:
            cache_effective = True
            print("   ✅ 缓存生效：只有第一次查询数据库")
        elif sql_count > 0 and sql_count2 > sql_count:
            print("   ❌ 缓存未生效：每次都查询数据库")
        elif sql_count == 0 and sql_count2 == 0:
            print("   ⚠️  无法确定缓存行为：没有检测到SQL查询")
        else:
            print("   ⚠️  无法确定缓存行为：SQL查询次数异常")
        
        # 计算性能提升
        improvement = 0
        if first_time > 0:
            improvement = ((first_time - second_time) / first_time) * 100
        
        print(f"\n📈 性能分析:")
        print(f"   响应时间提升: {improvement:.2f}%")
        
        if cache_effective and improvement > 0:
            print("   ✅ 缓存有效且性能提升")
        elif cache_effective:
            print("   📊 缓存有效但性能提升不明显")
        else:
            print("   ❌ 缓存未生效")
        
        return {
            "endpoint": endpoint,
            "cache_enabled": cache_enabled,
            "first_time": first_time,
            "second_time": second_time,
            "first_sql_count": sql_count,
            "second_sql_count": sql_count2,
            "improvement": improvement,
            "cache_effective": cache_effective,
            "data_same": data_same
        }

async def test_cache_performance():
    """测试缓存性能"""
    print("🚀 缓存性能测试")
    print("=" * 60)
    
    # 清理Redis缓存
    print("🧹 清理Redis缓存...")
    try:
        subprocess.run(['redis-cli', 'FLUSHALL'], check=True)
        print("✅ Redis缓存已清理")
    except subprocess.CalledProcessError as e:
        print(f"❌ 清理Redis缓存失败: {e}")
        print("⚠️  继续测试，但结果可能不准确")
    except FileNotFoundError:
        print("❌ redis-cli 未找到，请确保Redis已安装")
        print("⚠️  继续测试，但结果可能不准确")
    
    # 清理日志文件
    log_file = "/var/log/blogn2.log"
    if os.path.exists(log_file):
        try:
            subprocess.run(['sudo', 'truncate', '-s', '0', log_file], check=True)
            print("✅ 已清理日志文件")
        except subprocess.CalledProcessError as e:
            print(f"❌ 清理日志文件失败: {e}")
            print("⚠️  继续测试，但可能无法准确统计SQL查询")
    else:
        print("❌ 日志文件不存在: /var/log/blogn2.log")
        print("⚠️  无法统计SQL查询次数，将仅基于响应时间判断")
    
    # 测试端点
    endpoints = [
        "/api/metadata/",
        "/api/users/summary",
        "/api/blogs/recent",
    ]
    
    all_results = []
    
    # 测试缓存关闭的情况
    print("\n🔴 测试缓存关闭的情况")
    print("=" * 40)
    
    # 禁用缓存
    if not modify_env_cache_setting(False):
        print("❌ 无法禁用缓存，跳过测试")
        return
    
    # 重启服务
    if not restart_service():
        print("❌ 服务重启失败，无法继续测试")
        return
    
    # 等待服务就绪
    if not await wait_for_service_ready():
        print("❌ 服务未就绪，无法继续测试")
        return
    
    # 清理日志文件
    if os.path.exists(log_file):
        try:
            subprocess.run(['sudo', 'truncate', '-s', '0', log_file], check=True)
            print("✅ 已清理日志文件")
        except subprocess.CalledProcessError:
            pass
    
    # 测试缓存关闭时的性能
    cache_off_results = []
    for endpoint in endpoints:
        result = await test_endpoint_cache(endpoint, log_file, False)
        cache_off_results.append(result)
        all_results.append(result)
    
    # 测试缓存开启的情况
    print("\n🟢 测试缓存开启的情况")
    print("=" * 40)
    
    # 启用缓存
    if not modify_env_cache_setting(True):
        print("❌ 无法启用缓存，跳过测试")
        return
    
    # 重启服务
    if not restart_service():
        print("❌ 服务重启失败，无法继续测试")
        return
    
    # 等待服务就绪
    if not await wait_for_service_ready():
        print("❌ 服务未就绪，无法继续测试")
        return
    
    # 清理日志文件
    if os.path.exists(log_file):
        try:
            subprocess.run(['sudo', 'truncate', '-s', '0', log_file], check=True)
            print("✅ 已清理日志文件")
        except subprocess.CalledProcessError:
            pass
    
    # 测试缓存开启时的性能
    cache_on_results = []
    for endpoint in endpoints:
        result = await test_endpoint_cache(endpoint, log_file, True)
        cache_on_results.append(result)
        all_results.append(result)
    
    # 比较结果
    print("\n📊 缓存开启/关闭对比分析")
    print("=" * 50)
    
    for i, endpoint in enumerate(endpoints):
        off_result = cache_off_results[i]
        on_result = cache_on_results[i]
        
        print(f"\n🔍 端点: {endpoint}")
        print(f"   缓存关闭 - SQL查询: {off_result['first_sql_count']} -> {off_result['second_sql_count']}")
        print(f"   缓存开启 - SQL查询: {on_result['first_sql_count']} -> {on_result['second_sql_count']}")
        
        if off_result['second_sql_count'] > off_result['first_sql_count'] and on_result['second_sql_count'] == on_result['first_sql_count']:
            print("   ✅ 缓存正常工作：关闭时每次都查询，开启时第二次不查询")
        elif off_result['second_sql_count'] > off_result['first_sql_count'] and on_result['second_sql_count'] > on_result['first_sql_count']:
            print("   ❌ 缓存未生效：开启和关闭时都每次都查询")
        elif off_result['second_sql_count'] == off_result['first_sql_count'] and on_result['second_sql_count'] == on_result['first_sql_count']:
            print("   ⚠️  无法确定：两种情况都没有检测到SQL查询变化")
        else:
            print("   ⚠️  结果异常：需要进一步分析")
    
    # 生成报告
    effective_caches_off = [r for r in cache_off_results if r["cache_effective"]]
    effective_caches_on = [r for r in cache_on_results if r["cache_effective"]]
    
    avg_improvement_off = statistics.mean([r["improvement"] for r in cache_off_results]) if cache_off_results else 0
    avg_improvement_on = statistics.mean([r["improvement"] for r in cache_on_results]) if cache_on_results else 0
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "summary": {
            "total_endpoints": len(endpoints),
            "cache_off": {
                "effective_caches": len(effective_caches_off),
                "avg_improvement": avg_improvement_off
            },
            "cache_on": {
                "effective_caches": len(effective_caches_on),
                "avg_improvement": avg_improvement_on
            }
        },
        "cache_off_results": cache_off_results,
        "cache_on_results": cache_on_results,
        "comparison": {
            "cache_working": len(effective_caches_on) > len(effective_caches_off),
            "performance_improvement": avg_improvement_on > avg_improvement_off
        }
    }
    
    with open("final_cache_performance_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 性能报告已保存到: final_cache_performance_report.json")
    
    # 总结
    print("\n🎉 测试总结:")
    print(f"   测试端点数: {len(endpoints)}")
    print(f"   缓存关闭时生效端点数: {len(effective_caches_off)}")
    print(f"   缓存开启时生效端点数: {len(effective_caches_on)}")
    print(f"   缓存关闭时平均性能提升: {avg_improvement_off:.2f}%")
    print(f"   缓存开启时平均性能提升: {avg_improvement_on:.2f}%")
    
    if len(effective_caches_on) > len(effective_caches_off):
        print("   ✅ 缓存系统正常工作")
    elif len(effective_caches_on) == len(effective_caches_off):
        print("   ⚠️  缓存系统可能存在问题")
    else:
        print("   ❌ 缓存系统异常")

async def main():
    """主函数"""
    print("🔧 自动缓存性能测试")
    print("=" * 60)
    
    # 检查API服务器
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=5) as response:
                if response.status != 200:
                    print("❌ API服务器未正常运行")
                    return
    except Exception as e:
        print(f"❌ 无法连接到API服务器: {e}")
        return
    
    print("✅ API服务器运行正常")
    
    await test_cache_performance()
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 