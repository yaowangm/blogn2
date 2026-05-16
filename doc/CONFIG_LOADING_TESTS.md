# 配置加载测试文档

## 概述

本文档说明新的配置加载逻辑的测试覆盖情况。新的配置加载规则支持通过 `BLOGN_CONFIG_FILE` 环境变量或 `.env` 文件加载配置，并在 Docker 容器中有特殊处理。

## 环境变量模板与 `.env`

- 对外模板为项目根目录 **`.env.example`**（Docker 与本地共用，见 `docker/README-DOCKER.md`）；私有配置写入 **`.env`**（gitignore，不提交）。
- 本地 **`.env` 的活动键名**须与 **`.env.example` 的活动键名**完全一致（值可不同）。
- **`BLOGN_ALLOW_DANGEROUS_TEST_SQL_CLEANUP`** 仅出现在 `.env.example` 的注释中，用于说明 `tests/conftest.py` 在显式设为 `1` 时的危险 SQL 清理行为；**不要**将其作为 `.env` 的活动配置项。

## 测试文件结构

```
tests/
├── unit/
│   ├── test_config_loading.py      # 配置加载核心逻辑测试
│   └── test_config_utils.py        # 配置工具函数测试
├── integration/
│   └── test_config_integration.py  # 配置集成测试
scripts/
└── test_config_loading.py          # 手动测试脚本
```

## 测试场景覆盖

### 1. 本地开发环境测试

#### 场景 1.1: 使用 BLOGN_CONFIG_FILE 环境变量
- **测试文件**: `test_config_loading.py::TestLoadConfigFileLocal::test_load_config_file_with_blogn_config_file`
- **验证点**:
  - 配置文件路径正确返回
  - 配置文件中的环境变量已加载
  - 环境变量值正确

#### 场景 1.2: 使用当前目录的 .env 文件
- **测试文件**: `test_config_loading.py::TestLoadConfigFileLocal::test_load_config_file_with_env_file`
- **验证点**:
  - 当未设置 `BLOGN_CONFIG_FILE` 时，自动查找 `.env` 文件
  - `.env` 文件中的配置正确加载

#### 场景 1.3: 使用默认配置
- **测试文件**: `test_config_loading.py::TestLoadConfigFileLocal::test_load_config_file_with_defaults`
- **验证点**:
  - 当没有配置文件时，返回 `None`
  - 使用代码中的默认配置值

### 2. Docker 容器环境测试

#### 场景 2.1: Docker 容器中使用 BLOGN_CONFIG_FILE
- **测试文件**: `test_config_loading.py::TestLoadConfigFileDocker::test_load_config_file_in_docker_with_config`
- **验证点**:
  - 在 Docker 容器中正确加载指定的配置文件
  - 配置值正确

#### 场景 2.2: Docker 容器中未配置 BLOGN_CONFIG_FILE
- **测试文件**: `test_config_loading.py::TestLoadConfigFileDocker::test_load_config_file_in_docker_without_config`
- **验证点**:
  - 返回 `None`（使用默认配置）
  - 日志中输出警告信息

### 3. 错误处理测试

#### 场景 3.1: 配置文件不存在
- **测试文件**: `test_config_loading.py::TestConfigFileErrors::test_load_config_file_not_exists`
- **验证点**:
  - 返回 `None`
  - 日志中输出警告信息

#### 场景 3.2: 配置文件加载失败
- **测试文件**: `test_config_loading.py::TestConfigFileErrors::test_load_config_file_load_error`
- **验证点**:
  - 异常处理正确
  - 错误信息记录到日志

### 4. 缓存机制测试

#### 场景 4.1: 配置文件缓存
- **测试文件**: `test_config_loading.py::TestConfigFileCaching::test_load_config_file_caching`
- **验证点**:
  - 多次调用 `load_config_file()` 返回相同结果
  - 不会重复加载配置文件

### 5. 环境变量优先级测试

#### 场景 5.1: 环境变量优先于配置文件
- **测试文件**: `test_config_loading.py::TestEnvironmentVariablePriority::test_env_var_overrides_config_file`
- **验证点**:
  - 环境变量值优先于配置文件中的值
  - `override=False` 确保环境变量不被覆盖

### 6. Docker 容器检测测试

#### 场景 6.1: 通过 /.dockerenv 文件检测
- **测试文件**: `test_config_utils.py::TestIsDockerContainer::test_is_docker_container_with_dockerenv`
- **验证点**:
  - 正确检测 Docker 容器环境

#### 场景 6.2: 通过环境变量检测
- **测试文件**: `test_config_utils.py::TestIsDockerContainer::test_is_docker_container_with_env_var`
- **验证点**:
  - `DOCKER_CONTAINER` 环境变量的不同值都能正确识别

#### 场景 6.3: 通过 cgroup 文件检测
- **测试文件**: `test_config_utils.py::TestIsDockerContainer::test_is_docker_container_with_cgroup`
- **验证点**:
  - 通过 `/proc/1/cgroup` 文件内容检测容器环境

### 7. 集成测试

#### 场景 7.1: 所有配置模块使用相同配置文件
- **测试文件**: `test_config_integration.py::TestConfigIntegration::test_config_modules_use_same_config_file`
- **验证点**:
  - `app.py`、`cache.py`、`model.py` 都使用相同的配置文件
  - 配置信息中显示正确的配置文件路径

#### 场景 7.2: 配置模块使用默认配置
- **测试文件**: `test_config_integration.py::TestConfigIntegration::test_config_with_defaults`
- **验证点**:
  - 所有配置模块正确使用默认配置
  - 配置来源显示为 "defaults"

## 运行测试

### 使用 pytest 运行单元测试

```bash
# 运行所有配置加载测试
pytest tests/unit/test_config_loading.py -v

# 运行配置工具函数测试
pytest tests/unit/test_config_utils.py -v

# 运行集成测试
pytest tests/integration/test_config_integration.py -v

# 运行所有配置相关测试
pytest tests/unit/test_config_loading.py tests/unit/test_config_utils.py tests/integration/test_config_integration.py -v
```

### 使用手动测试脚本

```bash
# 运行手动测试脚本（需要安装 python-dotenv）
python scripts/test_config_loading.py
```

手动测试脚本会测试以下场景：
1. 使用 `BLOGN_CONFIG_FILE` 环境变量
2. 使用当前目录的 `.env` 文件
3. 使用默认配置
4. Docker 容器环境
5. Docker 容器中未配置 `BLOGN_CONFIG_FILE`
6. 获取配置文件路径
7. 所有配置模块的配置信息

## 测试覆盖率目标

- **单元测试覆盖率**: 90%+
- **集成测试覆盖率**: 主要场景覆盖
- **边界情况**: 所有错误处理路径

## 测试注意事项

1. **全局变量重置**: 每个测试都会重置 `_config_file_path` 全局变量，确保测试隔离
2. **环境变量清理**: 测试前后会清理相关环境变量
3. **临时文件**: 使用 `tmp_path` fixture 创建临时配置文件
4. **Docker 环境模拟**: 使用 `DOCKER_CONTAINER` 环境变量或 mock 函数模拟 Docker 环境

## 已知限制

1. 某些测试需要实际的文件系统操作，在 CI/CD 环境中可能需要特殊处理
2. Docker 容器检测的部分测试依赖于实际环境，可能需要 mock
3. 环境变量的优先级测试需要确保测试环境干净

## 后续改进

1. 添加性能测试，验证配置加载的性能
2. 添加并发测试，验证多线程环境下的配置加载
3. 添加配置文件格式验证测试
4. 添加配置文件热重载测试（如果实现）
