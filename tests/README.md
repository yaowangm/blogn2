# BlogN2 测试文档

## 概述

本项目包含完整的单元测试和集成测试套件，确保代码质量和功能正确性。

## 测试结构

```
tests/
├── __init__.py                    # 测试包初始化
├── conftest.py                    # Pytest配置和夹具
├── run_tests.py                   # 测试运行脚本
├── README.md                      # 本文件
├── unit/                          # 单元测试
│   ├── test_user_controller.py    # 用户控制器测试
│   ├── test_blog_controller.py    # 博客控制器测试
│   ├── test_metadata_controller.py # 元数据控制器测试
│   ├── test_user_service.py       # 用户服务测试
│   ├── test_blog_service.py       # 博客服务测试
│   ├── test_metadata_service.py   # 元数据服务测试
│   ├── test_base_service.py       # 基础服务测试
│   ├── test_user_repository.py    # 用户仓库测试
│   ├── test_post_repository.py    # 帖子仓库测试
│   ├── test_project_repository.py # 项目仓库测试
│   ├── test_project_item_repository.py # 项目项仓库测试
│   ├── test_database.py           # 数据库测试
│   ├── test_dependencies.py       # 依赖注入测试
│   └── test_main.py               # 主应用测试
└── integration/                   # 集成测试
    ├── test_api_endpoints.py      # API端点测试（Mock版本）
    ├── test_api_endpoints_with_real_db.py # API端点测试（真实数据库版本）
    ├── test_basic_endpoints.py    # 基础端点测试（快速验证）
    └── test_bert_vectorization_with_real_db.py # BERT 向量化集成测试（真实数据库）
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- **位置**: `tests/unit/`
- **目的**: 测试独立的函数、类和方法
- **特点**: 
  - 使用模拟对象隔离依赖
  - 快速执行
  - 高覆盖率

### 2. 集成测试 (Integration Tests)
- **位置**: `tests/integration/`
- **目的**: 测试组件间的交互
- **特点**:
  - 测试API端点
  - 验证端到端功能
  - 使用真实数据库

#### 集成测试类型
- **Mock版本** (`test_api_endpoints.py`): 使用Mock服务，快速验证API逻辑
- **真实数据库版本** (`test_api_endpoints_with_real_db.py`): 使用真实数据库，完整验证业务流程
- **基础端点测试** (`test_basic_endpoints.py`): 快速验证基本功能，不创建测试数据

## 运行测试

### 使用测试脚本（推荐）

```bash
# 运行所有测试
python tests/run_tests.py all

# 运行单元测试
python tests/run_tests.py unit

# 运行集成测试
python tests/run_tests.py integration

# 运行基础端点测试（快速验证）
python tests/run_tests.py basic

# 运行测试并生成覆盖率报告
python tests/run_tests.py coverage

# 运行代码检查
python tests/run_tests.py lint

# 清理测试文件
python tests/run_tests.py clean
```

### 使用pytest直接运行

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_user_controller.py

# 运行特定测试类
pytest tests/unit/test_user_controller.py::TestUserController

# 运行特定测试方法
pytest tests/unit/test_user_controller.py::TestUserController::test_get_user_summary_success

# 运行带标记的测试
pytest -m unit
pytest -m integration

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 测试配置

### pytest.ini
- 配置测试发现规则
- 设置异步测试模式
- 配置覆盖率报告
- 定义测试标记

### conftest.py
- 提供全局测试夹具
- 配置测试数据库
- 设置模拟对象
- 管理测试环境

## 测试夹具 (Fixtures)

### 数据库相关
- `test_engine`: 测试数据库引擎
- `test_session`: 测试数据库会话
- `mock_db_session`: 模拟数据库会话

### 服务相关
- `mock_async_session`: 模拟异步会话
- `test_client`: FastAPI测试客户端

### 数据相关
- `sample_user_data`: 示例用户数据
- `sample_blog_data`: 示例博客数据
- `sample_metadata`: 示例元数据

## 测试标记

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.api`: API测试

## 覆盖率报告

运行覆盖率测试后，会生成以下报告：

- **控制台报告**: 显示未覆盖的代码行
- **HTML报告**: `htmlcov/index.html` - 详细的覆盖率报告
- **XML报告**: `coverage.xml` - 用于CI/CD集成

## 最佳实践

### 1. 测试命名
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

### 2. 测试结构
```python
def test_function_name_scenario():
    """测试描述"""
    # Arrange - 准备测试数据
    # Act - 执行被测试的代码
    # Assert - 验证结果
```

### 3. 模拟对象
- 使用 `AsyncMock` 模拟异步方法
- 使用 `MagicMock` 模拟同步方法
- 验证方法调用和参数

### 4. 异常测试
```python
with pytest.raises(ExpectedException) as exc_info:
    # 执行可能抛出异常的代码
assert "expected message" in str(exc_info.value)
```

## 持续集成

测试可以集成到CI/CD流程中：

```yaml
# GitHub Actions 示例
- name: Run tests
  run: |
    python tests/run_tests.py all
    
- name: Generate coverage report
  run: |
    python tests/run_tests.py coverage
```

## 故障排除

### 常见问题

1. **导入错误**
   - 确保在项目根目录运行测试
   - 检查 `PYTHONPATH` 设置

2. **数据库连接错误**
   - 集成测试（含 BERT 向量化）使用真实 PostgreSQL，需配置 `DATABASE_URL`
   - 确保测试环境变量正确设置

3. **异步测试失败**
   - 使用 `@pytest.mark.asyncio` 装饰器
   - 确保正确使用 `await`

### 调试技巧

```bash
# 详细输出
pytest -v

# 显示本地变量
pytest -l

# 在第一个失败处停止
pytest -x

# 显示最慢的测试
pytest --durations=10
```

## 贡献指南

1. 为新功能编写测试
2. 确保测试覆盖率不低于80%
3. 运行所有测试确保通过
4. 更新测试文档

## 联系方式

如有测试相关问题，请查看项目文档或提交Issue。 