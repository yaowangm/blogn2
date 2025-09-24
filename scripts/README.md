# 存量数据向量化脚本

本目录包含用于将现有数据批量向量化的脚本，用于填充向量表。

## 脚本说明

### 1. batch_vectorization.py - 多进程版本（推荐）
支持多进程并行处理，适合大数据量场景。已修复并发连接问题。

**功能特性：**
- 多进程并行处理（默认4个进程）
- 每个进程使用独立的数据库连接，避免并发冲突
- 进度显示和统计（每5条记录更新一次）
- 中断恢复支持
- 清空向量表选项

**使用方法：**
```bash
# 基本使用（4个进程）
python scripts/batch_vectorization.py

# 指定进程数量
python scripts/batch_vectorization.py --processes 8

# 清空向量表后重新开始
python scripts/batch_vectorization.py --clear-tables

# 从中断点恢复
python scripts/batch_vectorization.py --resume

# 只处理文章
python scripts/batch_vectorization.py --articles-only

# 只处理评论
python scripts/batch_vectorization.py --comments-only
```

**注意：** 多进程版本现在使用独立的数据库连接，解决了之前的并发冲突问题。

### 2. safe_vectorization.py - 安全版本
避免多进程并发问题，使用单进程顺序处理，最稳定可靠。

**功能特性：**
- 单进程顺序处理，避免并发问题
- 进度显示和统计（每5条记录更新一次）
- 中断恢复支持
- 清空向量表选项
- 完善的错误处理和事务管理

**使用方法：**
```bash
# 基本使用
python scripts/safe_vectorization.py

# 清空向量表后重新开始
python scripts/safe_vectorization.py --clear-tables

# 从中断点恢复
python scripts/safe_vectorization.py --resume

# 只处理文章
python scripts/safe_vectorization.py --articles-only

# 只处理评论
python scripts/safe_vectorization.py --comments-only
```

### 3. simple_vectorization.py - 简化版本
单进程处理，适合小数据量或调试场景。

**功能特性：**
- 单进程顺序处理
- 进度显示和统计（每5条记录更新一次）
- 中断恢复支持
- 清空向量表选项

**使用方法：**
```bash
# 基本使用
python scripts/simple_vectorization.py

# 清空向量表后重新开始
python scripts/simple_vectorization.py --clear-tables

# 从中断点恢复
python scripts/simple_vectorization.py --resume

# 只处理文章
python scripts/simple_vectorization.py --articles-only

# 只处理评论
python scripts/simple_vectorization.py --comments-only
```

## 参数说明

### 通用参数
- `--clear-tables`: 在向量化前清空所有向量表
- `--resume`: 从中断点恢复运行（自动检测已处理的记录）
- `--articles-only`: 只向量化文章数据
- `--comments-only`: 只向量化评论数据

### 多进程版本特有参数
- `--processes N`: 指定进程数量（默认4）

## 中断恢复机制

脚本支持中断恢复功能：

1. **自动检测恢复点**：
   - 文章：检查 `article_vectors` 表中的最大 `projectitem_id`
   - 评论：检查 `comment_vectors` 表中的最大 `post_id`

2. **恢复运行**：
   - 使用 `--resume` 参数
   - 脚本会自动跳过已处理的记录

3. **安全中断**：
   - 使用 `Ctrl+C` 可以安全中断
   - 已处理的记录不会丢失

## 进度显示

脚本会显示详细的进度信息：

```
文章向量化进度 - 已完成: 50/100 (50.0%) - 当前ID: 12345 - 用时: 120.5秒
```

包含信息：
- 数据类型（文章/评论）
- 完成数量/总数量
- 完成百分比
- 当前处理的ID
- 已使用时间

## 日志文件

脚本运行时会生成日志文件：
- `batch_vectorization.log` - 多进程版本日志
- `simple_vectorization.log` - 简化版本日志

## 注意事项

1. **数据库连接**：确保数据库连接正常
2. **模型加载**：首次运行会下载BERT模型
3. **内存使用**：多进程版本会占用更多内存
4. **中断恢复**：建议使用 `--resume` 参数恢复中断的任务

## 性能建议

- **小数据量**（<1000条）：使用简化版本
- **大数据量**（>1000条）：使用多进程版本
- **进程数量**：建议设置为CPU核心数的1-2倍
- **内存限制**：每个进程约占用1-2GB内存

## 故障排除

1. **模型加载失败**：检查网络连接和磁盘空间
2. **数据库连接失败**：检查数据库配置
3. **内存不足**：减少进程数量或使用简化版本
4. **权限问题**：确保有数据库写入权限
