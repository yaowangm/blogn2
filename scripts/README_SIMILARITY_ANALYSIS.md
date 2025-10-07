# 文章相似度分析工具

这个工具用于分析关键词与文章的相似度，支持计算关键词与文章标题、内容段落以及整体相似度。

## 功能特性

- 🔍 **多维度相似度分析**：计算关键词与标题、每个内容段、整体内容的相似度
- 🤖 **使用sentence-transformers**：基于BERT的多语言模型进行向量化
- 📊 **详细统计信息**：提供最高、最低、平均相似度等统计指标
- 📁 **结果导出**：支持将分析结果导出为JSON格式
- 🎯 **灵活的文章选择**：支持单个或多个文章ID分析
- 📈 **段落排序**：段落按相似度从大到小排序显示
- 🔍 **关键词标记**：自动标记包含关键词的段落

## 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖（如果尚未安装）
pip install sentence-transformers sqlmodel python-dotenv
```

## 使用方法

### 基本用法

```bash
python scripts/analyze_similarity.py "关键词" "{文章ID列表}"
```

### 参数说明

- `关键词`: 要分析的关键词（用引号包围）
- `文章ID列表`: 文章ID列表，格式为 `{1,2,3,4,5}`
- `--output, -o`: 可选，输出JSON文件的路径
- `--database-url`: 可选，数据库连接URL（默认使用环境变量）

### 使用示例

#### 1. 分析单个文章

```bash
python scripts/analyze_similarity.py "爱因斯坦" "{8282}"
```

#### 2. 分析多个文章并保存结果

```bash
python scripts/analyze_similarity.py "爱因斯坦" "{298,688,1611,1994,3022,6853,6876,7350,7899,8119,8282}" --output einstein_analysis.json
```

#### 3. 分析编程相关文章

```bash
python scripts/analyze_similarity.py "编程" "{99,165,197,212}" --output programming_analysis.json
```

#### 4. 使用示例脚本

```bash
# 运行预设的示例分析
./scripts/run_similarity_analysis.sh
```

## 输出结果

### 控制台输出

脚本会在控制台显示：
- 每篇文章的标题相似度
- 每个内容段的相似度
- 整体相似度
- 统计摘要
- 按相似度排序的文章列表

### JSON输出

如果指定了输出文件，会生成包含以下信息的JSON文件：

```json
{
  "keyword": "爱因斯坦",
  "article_ids": [8282],
  "total_articles": 1,
  "articles": [
    {
      "article_id": 8282,
      "title": "文章标题",
      "author": "作者",
      "keyword": "爱因斯坦",
      "similarities": {
        "title": {
          "similarity": 0.1234,
          "text": "文章标题"
        },
        "segment_0": {
          "similarity": 0.5678,
          "text": "内容段落..."
        },
        "overall": {
          "similarity": 0.5678,
          "method": "max_segment_similarity"
        }
      }
    }
  ],
  "statistics": {
    "max_similarity": 0.5678,
    "min_similarity": 0.1234,
    "avg_similarity": 0.3456,
    "articles_above_0.5": 1,
    "articles_above_0.3": 1
  }
}
```

## 相似度计算方法

1. **标题相似度**：关键词向量与文章标题向量的余弦相似度
2. **段落相似度**：关键词向量与每个内容段向量的余弦相似度
3. **整体相似度**：所有段落相似度中的最大值

## 环境配置

确保设置了正确的数据库连接：

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/blogn"
```

或者在 `.env` 文件中配置：

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/blogn
```

## 注意事项

- 首次运行时会下载sentence-transformers模型，可能需要一些时间
- 确保数据库中有相应的文章数据和向量数据
- 文章ID必须是有效的数字
- 相似度值范围在0-1之间，越接近1表示越相似

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查网络连接
   - 确保有足够的磁盘空间

2. **数据库连接失败**
   - 检查DATABASE_URL配置
   - 确保数据库服务正在运行

3. **文章未找到**
   - 检查文章ID是否正确
   - 确保文章状态为1（已发布）

4. **内存不足**
   - 减少同时分析的文章数量
   - 考虑分批处理

## 技术细节

- 使用模型：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- 向量维度：384
- 相似度计算：余弦相似度
- 数据库：PostgreSQL with pgvector extension
- 使用项目现有的BERTVectorizationService，避免重复下载模型

## 修复说明

### v1.2 新功能
- 段落按相似度从大到小排序显示
- 自动标记包含关键词的段落（显示🔍标记）
- 显示每篇文章的段落相似度排名（前10名）
- 优化了输出格式，更易阅读

### v1.1 修复内容
- 修复了数据库连接问题（异步/同步URL转换）
- 使用项目现有的向量化服务，避免重复下载模型
- 优化了错误处理和异常信息

### 常见问题解决
1. **数据库连接错误**：脚本会自动将异步URL转换为同步URL
2. **模型加载问题**：使用项目现有的BERTVectorizationService
3. **内存不足**：减少同时分析的文章数量
