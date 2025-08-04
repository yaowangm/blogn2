#!/usr/bin/env python3
"""
最终缓存性能测试脚本
验证缓存系统的性能提升
通过检查日志文件中的SQL查询次数来确认缓存是否生效
"""

import asyncio
import aiohttp
import time
import statistics
import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_endpoint_cache(endpoint: str, log_file: str):
    """测试单个端点的缓存行为"""
    print(f"\n📊 测试端点: {endpoint}")
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
                # 调试：显示最近的SQL查询
                lines = content.split('\n')
                sql_lines = [line for line in lines if 'INFO sqlalchemy.engine.Engine SELECT' in line]
                if sql_lines:
                    print(f"   最近的SQL查询: {sql_lines[-1][:100]}...")
        
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
                # 调试：显示最近的SQL查询
                lines = content.split('\n')
                sql_lines = [line for line in lines if 'INFO sqlalchemy.engine.Engine SELECT' in line]
                if sql_lines:
                    print(f"   最近的SQL查询: {sql_lines[-1][:100]}...")
        
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
    
    results = []
    
    for endpoint in endpoints:
        result = await test_endpoint_cache(endpoint, log_file)
        results.append(result)
    
    # 生成报告
    effective_caches = [r for r in results if r["cache_effective"]]
    avg_improvement = statistics.mean([r["improvement"] for r in results]) if results else 0
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "summary": {
            "total_endpoints": len(results),
            "effective_caches": len(effective_caches),
            "avg_improvement": avg_improvement,
            "max_improvement": max([r["improvement"] for r in results]) if results else 0,
            "min_improvement": min([r["improvement"] for r in results]) if results else 0
        },
        "results": results
    }
    
    with open("final_cache_performance_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 性能报告已保存到: final_cache_performance_report.json")
    
    # 总结
    print("\n🎉 测试总结:")
    print(f"   测试端点数: {len(results)}")
    print(f"   缓存生效端点数: {len(effective_caches)}")
    print(f"   平均性能提升: {avg_improvement:.2f}%")
    
    if len(effective_caches) == len(results):
        print("   ✅ 所有端点的缓存都正常工作")
    elif len(effective_caches) > 0:
        print("   📊 部分端点的缓存正常工作")
    else:
        print("   ❌ 所有端点的缓存都未生效")

async def main():
    """主函数"""
    print("🔧 最终缓存性能测试")
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