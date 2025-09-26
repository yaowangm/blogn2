#!/bin/bash
# 相似度分析脚本使用示例

# 激活虚拟环境
source ../venv/bin/activate

# 设置数据库连接（如果需要）
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/blogn"

echo "🔍 文章相似度分析工具"
echo "========================"

# 示例1: 分析"爱因斯坦"与指定文章的相似度
echo "示例1: 分析'爱因斯坦'与文章8282的相似度"
python analyze_similarity.py "爱因斯坦" "{8282}"

echo -e "\n" 

# 示例2: 分析"爱因斯坦"与多篇文章的相似度
echo "示例2: 分析'爱因斯坦'与多篇文章的相似度"
python analyze_similarity.py "爱因斯坦" "{298,688,1611,1994,3022,6853,6876,7350,7899,8119,8282}" --output einstein_analysis.json

echo -e "\n"

# 示例3: 分析"亚历山大"与指定文章的相似度
echo "示例3: 分析'亚历山大'与文章8282的相似度"
python analyze_similarity.py "亚历山大" "{8282}"

echo -e "\n"

# 示例4: 分析其他关键词
echo "示例4: 分析'编程'与多篇文章的相似度"
python analyze_similarity.py "编程" "{99,165,197,212}" --output programming_analysis.json

echo "✅ 分析完成！"
