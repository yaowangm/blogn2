# 模型配置说明

本文档说明如何配置BlogN2系统中的BERT模型路径和相关参数。

## 配置文件

模型配置通过环境变量进行管理，支持以下配置文件：
- `.env` - 实际使用的配置文件（不提交到版本控制）
- `.env.example` - 配置模板文件（提交到版本控制）

## 配置项说明

### 基本配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| 模型名称 | `MODEL_MODEL_NAME` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | BERT模型名称 |
| 本地模型路径 | `MODEL_MODEL_PATH` | `None` | 本地模型文件路径，如果设置则优先使用 |
| 运行设备 | `MODEL_DEVICE` | `auto` | 模型运行设备（auto/cpu/cuda/cuda:0 等）。`auto` 时仅当 CUDA 可用且当前 GPU 架构在 PyTorch 编译支持列表（`torch.cuda.get_arch_list()`）内才使用 cuda，否则自动使用 cpu，避免 "no kernel image" 等运行时错误。 |
| 最大输入长度 | `MODEL_MAX_LENGTH` | `512` | 模型最大输入文本长度 |
| 向量维度 | `MODEL_VECTOR_DIMENSION` | `384` | 输出向量的维度 |

### 加载策略配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| 优先使用本地模型 | `MODEL_PREFER_LOCAL` | `true` | 是否优先使用本地模型文件 |
| 回退到Hugging Face | `MODEL_FALLBACK_TO_HUGGINGFACE` | `true` | 本地模型失败时是否回退到在线下载 |
| 模型缓存目录 | `MODEL_CACHE_DIR` | `None` | 模型缓存目录，None表示使用默认目录 |

## 配置示例

### 使用本地模型

```bash
# 设置本地模型路径
MODEL_MODEL_PATH=/path/to/your/local/model

# 优先使用本地模型
MODEL_PREFER_LOCAL=true

# 本地模型失败时回退到在线下载
MODEL_FALLBACK_TO_HUGGINGFACE=true
```

### 使用在线模型

```bash
# 不设置本地模型路径，使用模型名称
# MODEL_MODEL_PATH=

# 设置模型名称
MODEL_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 设置缓存目录
MODEL_CACHE_DIR=/path/to/cache
```

### 强制使用CPU

```bash
# 强制使用CPU运行模型
MODEL_DEVICE=cpu
```

### 强制使用GPU

```bash
# 强制使用GPU运行模型
MODEL_DEVICE=cuda

# 或指定特定GPU
MODEL_DEVICE=cuda:0
```

## 模型下载

### 自动下载

如果未配置本地模型路径，系统会自动从Hugging Face下载模型到默认缓存目录：
- Linux: `~/.cache/huggingface/transformers/`
- Windows: `%USERPROFILE%\.cache\huggingface\transformers\`

### 手动下载

你也可以手动下载模型到指定目录：

```bash
# 使用huggingface-hub下载
pip install huggingface-hub
python -c "from huggingface_hub import snapshot_download; snapshot_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', local_dir='./models/bert-model')"
```

然后设置环境变量：
```bash
MODEL_MODEL_PATH=./models/bert-model
```

## 性能优化

### 设备选择

- `auto`: 自动选择。先检查 `torch.cuda.is_available()`；若可用，再根据 `torch.cuda.get_device_capability(0)` 与 `torch.cuda.get_arch_list()` 判断当前 GPU 是否在 PyTorch 编译支持的架构列表中，仅在列表中时使用 CUDA，否则使用 CPU，避免 "no kernel image" 等错误。
- `cpu`: 强制使用 CPU，适合内存受限或无需 GPU 的环境。
- `cuda`: 强制使用 GPU（需安装 CUDA 与 PyTorch GPU 版本）。
- `cuda:0`: 使用指定 GPU 设备。

### 内存优化

如果遇到内存不足的问题，可以：

1. 减少最大输入长度：
```bash
MODEL_MAX_LENGTH=256
```

2. 强制使用CPU：
```bash
MODEL_DEVICE=cpu
```

3. 使用更小的模型：
```bash
MODEL_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查网络连接
   - 验证模型名称是否正确
   - 检查本地模型路径是否存在

2. **CUDA 报错 "no kernel image is available for execution on the device"**
   - 表示当前 GPU 架构不在本机 PyTorch 的编译支持列表中。保持 `MODEL_DEVICE=auto` 时应用会自动回退到 CPU；或显式设置 `MODEL_DEVICE=cpu`。

3. **CUDA 内存不足**
   - 设置 `MODEL_DEVICE=cpu`
   - 减少 `MODEL_MAX_LENGTH`

4. **本地模型无法加载**
   - 检查模型路径是否正确
   - 验证模型文件完整性
   - 设置 `MODEL_FALLBACK_TO_HUGGINGFACE=true`

### 调试模式

启用详细日志来诊断问题：

```bash
# 设置日志级别
LOG_LEVEL=DEBUG

# 启用缓存调试
CACHE_CACHE_DEBUG=true
```

## 更新配置

修改配置后需要重启应用才能生效：

```bash
# 重启FastAPI应用
uvicorn src.main:app --reload
```

## 注意事项

1. `.env` 文件包含敏感信息，不要提交到版本控制
2. 模型文件较大，首次下载可能需要较长时间
3. GPU模式需要安装相应的CUDA驱动和PyTorch GPU版本
4. 生产环境建议使用本地模型以提高加载速度
