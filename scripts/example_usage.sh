#!/bin/bash
# 向量化脚本使用示例

echo "=== 向量化脚本使用示例 ==="

# 1. 测试环境
echo "1. 测试环境..."
python scripts/test_vectorization.py

echo -e "\n2. 基本使用示例..."

# 2. 清空向量表并重新开始（简化版本）
echo "清空向量表并重新开始（简化版本）:"
echo "python scripts/simple_vectorization.py --clear-tables"

# 3. 从中断点恢复（简化版本）
echo -e "\n从中断点恢复（简化版本）:"
echo "python scripts/simple_vectorization.py --resume"

# 4. 多进程版本
echo -e "\n多进程版本（8个进程）:"
echo "python scripts/batch_vectorization.py --processes 8 --clear-tables"

# 5. 只处理文章
echo -e "\n只处理文章:"
echo "python scripts/simple_vectorization.py --articles-only"

# 6. 只处理评论
echo -e "\n只处理评论:"
echo "python scripts/simple_vectorization.py --comments-only"

echo -e "\n=== 注意事项 ==="
echo "1. 首次运行会下载BERT模型，需要网络连接"
echo "2. 建议先使用简化版本测试"
echo "3. 大数据量建议使用多进程版本"
echo "4. 可以随时使用Ctrl+C中断，使用--resume恢复"
echo "5. 查看日志文件了解详细进度"

echo -e "\n=== 日志文件 ==="
echo "- simple_vectorization.log (简化版本)"
echo "- batch_vectorization.log (多进程版本)"
