#!/usr/bin/env python3
"""
BERT向量化基础功能测试

快速验证BERT向量化功能是否正常工作，不依赖数据库。
用于在部署前快速检查功能状态。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_vectorization_service_import():
    """测试向量化服务导入"""
    try:
        from src.services.vectorization_service import BERTVectorizationService
        print("✅ BERTVectorizationService 导入成功")
        return True
    except Exception as e:
        print(f"❌ BERTVectorizationService 导入失败: {e}")
        return False

async def test_vectorization_service_creation():
    """测试向量化服务创建"""
    try:
        from src.services.vectorization_service import BERTVectorizationService
        
        service = BERTVectorizationService()
        print("✅ BERTVectorizationService 创建成功")
        
        # 测试单例模式
        service2 = BERTVectorizationService()
        assert service is service2, "单例模式测试失败"
        print("✅ 单例模式测试通过")
        
        return True
    except Exception as e:
        print(f"❌ BERTVectorizationService 创建失败: {e}")
        return False

async def test_text_preprocessing():
    """测试文本预处理功能"""
    try:
        from src.services.vectorization_service import BERTVectorizationService
        
        service = BERTVectorizationService()
        
        # 测试各种文本预处理
        test_cases = [
            ("<p>HTML标签</p>", "HTML标签"),
            ("  多余空格  ", "多余空格"),
            ("", ""),
            ("a" * 3000, "a" * 2000),  # 超长文本截断
        ]
        
        for input_text, expected in test_cases:
            result = service._preprocess_text(input_text)
            assert result == expected, f"预处理失败: '{input_text}' -> '{result}' (期望: '{expected}')"
        
        print("✅ 文本预处理测试通过")
        return True
    except Exception as e:
        print(f"❌ 文本预处理测试失败: {e}")
        return False

async def test_vector_conversion():
    """测试向量转换功能"""
    try:
        from src.services.vectorization_service import BERTVectorizationService
        import numpy as np
        
        service = BERTVectorizationService()
        
        # 测试向量转JSON
        test_vector = np.array([1.0, 2.0, 3.0])
        json_str = service.vector_to_json(test_vector)
        assert json_str == "[1.0, 2.0, 3.0]", f"向量转JSON失败: {json_str}"
        
        # 测试JSON转向量
        converted_vector = service.json_to_vector(json_str)
        assert np.array_equal(converted_vector, test_vector), "JSON转向量失败"
        
        # 测试无效JSON处理
        invalid_vector = service.json_to_vector("invalid json")
        assert isinstance(invalid_vector, np.ndarray), "无效JSON处理失败"
        assert invalid_vector.shape == (384,), "无效JSON返回向量维度错误"
        
        print("✅ 向量转换测试通过")
        return True
    except Exception as e:
        print(f"❌ 向量转换测试失败: {e}")
        return False

async def test_update_service_import():
    """测试更新服务导入"""
    try:
        from src.services.vectorization_update_service import VectorizationUpdateService
        print("✅ VectorizationUpdateService 导入成功")
        return True
    except Exception as e:
        print(f"❌ VectorizationUpdateService 导入失败: {e}")
        return False

async def test_search_service_import():
    """测试搜索服务导入"""
    try:
        from src.services.search_service import HierarchicalSearchService
        print("✅ HierarchicalSearchService 导入成功")
        return True
    except Exception as e:
        print(f"❌ HierarchicalSearchService 导入失败: {e}")
        return False

async def test_search_service_creation():
    """测试搜索服务创建"""
    try:
        from src.services.search_service import HierarchicalSearchService
        from unittest.mock import AsyncMock
        
        # 创建模拟对象
        mock_vectorization_service = AsyncMock()
        mock_session = AsyncMock()
        
        # 创建搜索服务
        search_service = HierarchicalSearchService(mock_vectorization_service, mock_session)
        
        # 测试动态阈值计算
        threshold = search_service.calculate_dynamic_threshold("测试查询", "[]")
        assert 0.1 <= threshold <= 0.9, f"动态阈值计算失败: {threshold}"
        
        print("✅ 搜索服务创建和基本功能测试通过")
        return True
    except Exception as e:
        print(f"❌ 搜索服务测试失败: {e}")
        return False

async def test_database_models_import():
    """测试数据库模型导入"""
    try:
        from src.models.user import User
        from src.models.project_item import ProjectItem
        from src.models.post import Post
        print("✅ 数据库模型导入成功")
        return True
    except Exception as e:
        print(f"❌ 数据库模型导入失败: {e}")
        return False

async def main():
    """运行所有基础测试"""
    print("🚀 开始BERT向量化基础功能测试")
    print("=" * 50)
    
    tests = [
        ("服务导入测试", test_vectorization_service_import),
        ("服务创建测试", test_vectorization_service_creation),
        ("文本预处理测试", test_text_preprocessing),
        ("向量转换测试", test_vector_conversion),
        ("更新服务导入测试", test_update_service_import),
        ("搜索服务导入测试", test_search_service_import),
        ("搜索服务创建测试", test_search_service_creation),
        ("数据库模型导入测试", test_database_models_import),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 运行: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print("\n🎉 所有基础测试通过！BERT向量化功能准备就绪。")
        return True
    else:
        print(f"\n❌ 有 {failed} 个测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
