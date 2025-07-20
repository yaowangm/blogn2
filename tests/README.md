# BlogN2 测试文档

## 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest配置和fixtures
├── test_controllers.py      # 控制器层测试
├── test_services.py         # 服务层测试
├── test_repositories.py     # 仓库层测试
├── test_integration.py      # 集成测试
├── run_tests.py             # 测试运行脚本
└── README.md               # 测试说明文档
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- **控制器测试**: 测试API端点的请求处理和响应
- **服务测试**: 测试业务逻辑层
- **仓库测试**: 测试数据访问层

### 2. 集成测试 (Integration Tests)
- **API集成测试**: 测试完整的API流程
- **数据库集成测试**: 测试与数据库的交互
- **错误处理测试**: 测试各种错误情况

## 运行测试

### 安装测试依赖
```bash
pip install -r requirements.txt
```

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定类型的测试
```bash
# 运行单元测试
pytest tests/ -m unit -v

# 运行集成测试
pytest tests/ -m integration -v

# 运行控制器测试
pytest tests/test_controllers.py -v

# 运行服务测试
pytest tests/test_services.py -v

# 运行仓库测试
pytest tests/test_repositories.py -v
```

### 运行覆盖率测试
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

### 使用测试脚本
```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定测试
python tests/run_tests.py unit
python tests/run_tests.py integration
python tests/run_tests.py controllers

# 运行覆盖率测试
python tests/run_tests.py coverage
```

## 测试配置

### pytest.ini
- 配置测试发现规则
- 设置异步测试模式
- 定义测试标记

### conftest.py
- 提供测试fixtures
- 配置测试数据库
- 设置测试客户端

## 测试数据库

测试使用SQLite内存数据库，确保：
- 测试之间数据隔离
- 测试运行快速
- 不需要外部数据库依赖

## 测试标记

- `@pytest.mark.asyncio`: 标记异步测试
- `@pytest.mark.integration`: 标记集成测试
- `@pytest.mark.unit`: 标记单元测试
- `@pytest.mark.slow`: 标记慢速测试

## 最佳实践

1. **测试命名**: 使用描述性的测试名称
2. **测试隔离**: 每个测试应该独立运行
3. **Mock使用**: 适当使用mock来隔离依赖
4. **断言清晰**: 使用明确的断言语句
5. **错误测试**: 测试正常情况和错误情况
6. **覆盖率**: 保持高测试覆盖率

## 持续集成

测试可以集成到CI/CD流程中：
```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=src --cov-report=xml
```

## 故障排除

### 常见问题

1. **导入错误**: 确保项目根目录在Python路径中
2. **数据库连接**: 检查测试数据库配置
3. **异步测试**: 确保正确使用async/await
4. **依赖问题**: 确保所有测试依赖已安装

### 调试技巧

1. 使用 `-s` 参数查看print输出
2. 使用 `--pdb` 在失败时进入调试器
3. 使用 `-x` 在第一个失败时停止
4. 使用 `--lf` 只运行上次失败的测试 