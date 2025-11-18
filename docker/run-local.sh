#!/bin/bash
# 使用本地 Python 环境运行 BlogN2（不容器化）

set -e

echo "🚀 BlogN2 本地运行脚本"
echo "================================"

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本: $PYTHON_VERSION"

# 检查必要文件
if [ ! -f "../.env" ]; then
    echo "⚠️  .env 文件不存在，从模板创建..."
    cp env.docker.example ../.env
    echo "✅ 请编辑 ../.env 文件配置数据库和 Redis"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "../venv" ]; then
    echo "📦 创建虚拟环境..."
    cd ..
    python3 -m venv venv
    source venv/bin/activate
    echo "📥 安装依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    cd docker
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
cd ..
source venv/bin/activate

# 检查依赖
echo ""
echo "🔍 检查依赖..."
python3 -c "import fastapi, uvicorn, sqlmodel" 2>/dev/null || {
    echo "⚠️  缺少依赖，正在安装..."
    pip install -r requirements.txt
}

# 创建必要目录
mkdir -p uploads avatars
chmod 755 uploads avatars

# 显示配置信息
echo ""
echo "📋 配置信息:"
echo "  - 数据库: $(grep DATABASE_URL .env | cut -d'=' -f2 | sed 's/:[^:]*@/:***@/')"
echo "  - Redis: $(grep CACHE_REDIS_HOST .env | cut -d'=' -f2):$(grep CACHE_REDIS_PORT .env | cut -d'=' -f2)"
echo "  - 工作目录: $(pwd)"

# 启动应用
echo ""
echo "🚀 启动应用..."
echo "📍 访问地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止应用"
echo ""

python3 run.py


