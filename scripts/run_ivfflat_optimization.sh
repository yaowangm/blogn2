#!/bin/bash

# IVFFlat索引优化执行脚本
# 使用方法: bash scripts/run_ivfflat_optimization.sh

echo "🔧 IVFFlat索引优化脚本"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "import sqlalchemy, sqlmodel" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少必要依赖，请先安装: pip install -r requirements.txt"
    exit 1
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
python3 -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from src.database import get_async_session
from sqlalchemy import text

async def test_db():
    try:
        async for session in get_async_session():
            result = await session.execute(text('SELECT 1'))
            print('✅ 数据库连接正常')
            return True
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        return False

asyncio.run(test_db())
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ 数据库连接失败，请检查配置"
    exit 1
fi

# 执行优化脚本
echo "🚀 开始执行IVFFlat索引优化..."
echo "================================"

python3 scripts/optimize_indexes_ivfflat.py

echo "================================"
echo "✅ 脚本执行完成！"
echo "📋 请查看日志文件: ivfflat_optimization.log"
echo "📊 请查看优化报告: scripts/ivfflat_optimization_report_*.md"
