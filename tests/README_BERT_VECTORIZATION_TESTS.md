# BERT向量化功能测试

本目录包含BERT向量化功能的完整测试套件，覆盖单元测试、集成测试和性能测试。

## 📁 测试文件结构

```
tests/
├── integration/
│   └── test_bert_vectorization_with_real_db.py    # 集成测试（使用真实数据库）
├── unit/
│   └── test_bert_vectorization_services.py        # 单元测试（模拟环境）
├── performance/
│   └── test_bert_vectorization_performance.py     # 性能测试
├── test_bert_vectorization_basic.py               # 基础功能测试
├── run_bert_vectorization_tests.py                # 测试运行脚本
└── README_BERT_VECTORIZATION_TESTS.md             # 本文档
```

## 🚀 快速开始

### 1. 环境准备

确保已安装所有依赖：

```bash
# 安装Python依赖
pip install -r requirements.txt

# 或者安装BERT向量化相关依赖
pip install numpy torch sentence-transformers sqlmodel psycopg2-binary
```

### 2. 数据库配置

确保数据库环境变量已正确设置：

```bash
# 在.env文件中设置
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name
```

### 3. 运行测试

#### 运行所有测试
```bash
python tests/run_bert_vectorization_tests.py
```

#### 运行特定类型的测试
```bash
# 只运行单元测试
python tests/run_bert_vectorization_tests.py --unit

# 只运行集成测试
python tests/run_bert_vectorization_tests.py --integration

# 只运行性能测试
python tests/run_bert_vectorization_tests.py --performance
```

#### 运行基础功能测试
```bash
python tests/test_bert_vectorization_basic.py
```

## 📋 测试类型说明

### 1. 单元测试 (`test_bert_vectorization_services.py`)

**特点：**
- 使用模拟对象，不依赖真实数据库
- 快速执行，适合持续集成
- 测试核心业务逻辑

**测试内容：**
- BERTVectorizationService 基本功能
- 文本预处理和向量转换
- 错误处理和边界条件
- 单例模式验证

**运行时间：** ~30秒

### 2. 集成测试 (`test_bert_vectorization_with_real_db.py`)

**特点：**
- 使用真实PostgreSQL数据库
- 自动清理测试数据
- 验证完整功能流程

**测试内容：**
- 文章向量化完整流程
- 评论向量化完整流程
- 搜索功能验证
- 数据清理功能
- 批量处理功能

**运行时间：** ~2-3分钟

### 3. 性能测试 (`test_bert_vectorization_performance.py`)

**特点：**
- 测量实际性能指标
- 验证性能要求
- 提供性能基准

**测试内容：**
- 单文本向量化速度
- 批量向量化性能
- 内存使用情况
- 并发处理能力
- 搜索性能测试
- 大文本处理性能

**运行时间：** ~5-10分钟

## 🔧 测试配置

### 环境变量

```bash
# 必需的环境变量
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name

# 可选的测试配置
PYTEST_VERBOSE=1          # 详细输出
PYTEST_COVERAGE=1         # 生成覆盖率报告
```

**设备选择**：测试不强制 `MODEL_DEVICE`。当为 `auto` 时，由 `get_model_device()` 根据 `torch.cuda.get_arch_list()` 与当前 GPU 的 compute capability 判断；仅当 GPU 架构在 PyTorch 编译支持列表内才使用 CUDA，否则自动使用 CPU，无需在测试环境单独设置。

### 测试数据管理

- **自动清理：** 所有测试都会自动清理创建的测试数据
- **数据隔离：** 每个测试使用独立的事务，确保数据隔离
- **临时测试库：** pytest 会话使用 `blogn_pytest_<pid>`，结束后自动销毁

## 📊 性能基准

### 向量化性能

| 文本长度 | 处理时间 | 速度 |
|---------|---------|------|
| 短文本 (<100字符) | <0.5秒 | >200字符/秒 |
| 中等文本 (100-1000字符) | <2秒 | >100字符/秒 |
| 长文本 (1000+字符) | <5秒 | >50字符/秒 |

### 搜索性能

| 查询类型 | 响应时间 | 结果数量 |
|---------|---------|---------|
| 简单查询 | <1秒 | 10-50 |
| 复杂查询 | <2秒 | 5-20 |
| 混合搜索 | <3秒 | 10-100 |

### 内存使用

| 操作 | 内存使用 | 说明 |
|------|---------|------|
| 模型加载 | <2GB | BERT模型内存占用 |
| 单次向量化 | <100MB | 临时内存使用 |
| 批量处理 | <500MB | 100个文本批量处理 |

## 🐛 故障排除

### 常见问题

1. **依赖缺失**
   ```
   ModuleNotFoundError: No module named 'numpy'
   ```
   **解决方案：** 安装所需依赖
   ```bash
   pip install numpy torch sentence-transformers
   ```

2. **数据库连接失败**
   ```
   ValueError: DATABASE_URL 环境变量未设置
   ```
   **解决方案：** 检查.env文件中的DATABASE_URL配置

3. **模型加载失败**
   ```
   RuntimeError: 模型加载失败
   ```
   **解决方案：** 检查网络连接，确保可以下载模型

4. **内存不足**
   ```
   MemoryError: 内存不足
   ```
   **解决方案：** 减少批量处理大小或增加系统内存

### 调试模式

启用详细输出进行调试：

```bash
python tests/run_bert_vectorization_tests.py --verbose
```

## 📈 持续集成

### GitHub Actions 配置示例

```yaml
name: BERT Vectorization Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        python tests/run_bert_vectorization_tests.py --unit
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
      run: |
        python tests/run_bert_vectorization_tests.py --integration
```

## 📝 测试报告

### 生成覆盖率报告

```bash
python tests/run_bert_vectorization_tests.py --coverage
```

覆盖率报告将生成在 `htmlcov/index.html`

### 测试结果示例

```
🚀 开始运行BERT向量化测试
============================================================
运行: BERT向量化服务单元测试
命令: python -m pytest tests/unit/test_bert_vectorization_services.py -q --tb=short
✅ 测试通过

============================================================
运行: BERT向量化集成测试
命令: python -m pytest tests/integration/test_bert_vectorization_with_real_db.py -q --tb=short
✅ 测试通过

============================================================
运行: BERT向量化性能测试
命令: python -m pytest tests/performance/test_bert_vectorization_performance.py -q --tb=short -s
✅ 测试通过

============================================================
测试结果总结
============================================================
单元测试: ✅ 通过
集成测试: ✅ 通过
性能测试: ✅ 通过

总计: 3 个测试
通过: 3 个
失败: 0 个

🎉 所有测试通过！
```

## 🤝 贡献指南

### 添加新测试

1. 在相应的测试文件中添加新的测试方法
2. 遵循现有的命名约定：`test_功能描述`
3. 确保测试数据自动清理
4. 添加适当的文档字符串

### 测试最佳实践

1. **独立性：** 每个测试应该独立运行
2. **可重复性：** 测试结果应该一致
3. **快速反馈：** 单元测试应该快速执行
4. **清晰命名：** 测试名称应该清楚描述测试内容
5. **适当断言：** 使用有意义的断言消息

## 📞 支持

如果遇到问题或需要帮助，请：

1. 检查本文档的故障排除部分
2. 查看测试输出中的错误信息
3. 确保所有依赖已正确安装
4. 验证数据库连接配置

---

**注意：** 这些测试使用真实数据库，请确保在测试环境中运行，避免影响生产数据。
