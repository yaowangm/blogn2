#!/bin/bash
set -e

# Docker 启动脚本
# 用于在容器启动时执行必要的检查和初始化

echo "🚀 BlogN2 容器启动中..."

# 检查必要的环境变量
if [ -z "$DATABASE_URL" ]; then
    echo "❌ 错误: DATABASE_URL 环境变量未设置"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  警告: SECRET_KEY 环境变量未设置，使用默认值（生产环境不安全）"
    export SECRET_KEY="default-secret-key-change-in-production"
fi

# 创建必要的目录
# 模型缓存目录根据环境变量 MODEL_CACHE_DIR 创建（默认为 /app/.cache/models）
MODEL_CACHE_DIR=${MODEL_CACHE_DIR:-/app/.cache/models}
mkdir -p /app/uploads /app/avatars "${MODEL_CACHE_DIR}"
chmod -R 755 /app/uploads /app/avatars "${MODEL_CACHE_DIR}"

# 等待数据库连接（可选，如果数据库在同一网络）
if [ -n "$WAIT_FOR_DB" ] && [ "$WAIT_FOR_DB" = "true" ]; then
    echo "⏳ 等待数据库连接..."
    until python -c "
import sys
import os
from urllib.parse import urlparse
import time

database_url = os.getenv('DATABASE_URL', '')
if not database_url:
    sys.exit(1)

# 提取数据库连接信息
parsed = urlparse(database_url.replace('postgresql+asyncpg://', 'postgresql://'))
host = parsed.hostname
port = parsed.port or 5432

# 简单的端口检查
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((host, port))
sock.close()
sys.exit(0 if result == 0 else 1)
" 2>/dev/null; do
        echo "等待数据库 $DATABASE_URL ..."
        sleep 2
    done
    echo "✅ 数据库连接可用"
fi

# 等待Redis连接（可选）
if [ -n "$WAIT_FOR_REDIS" ] && [ "$WAIT_FOR_REDIS" = "true" ]; then
    echo "⏳ 等待Redis连接..."
    until python -c "
import sys
import os
import socket

host = os.getenv('CACHE_REDIS_HOST', 'localhost')
port = int(os.getenv('CACHE_REDIS_PORT', '6379'))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((host, port))
sock.close()
sys.exit(0 if result == 0 else 1)
" 2>/dev/null; do
        echo "等待Redis $CACHE_REDIS_HOST:$CACHE_REDIS_PORT ..."
        sleep 2
    done
    echo "✅ Redis连接可用"
fi

# 显示配置信息（不显示敏感信息）
echo "📋 配置信息:"
echo "  - 应用环境: ${APP_ENV:-production}"
echo "  - 数据库: ${DATABASE_URL%%@*}@***"
echo "  - Redis: ${CACHE_REDIS_HOST:-localhost}:${CACHE_REDIS_PORT:-6379}"
echo "  - 模型设备: ${MODEL_DEVICE:-cpu}"
echo "  - 模型缓存目录: ${MODEL_CACHE_DIR:-/app/.cache/models}"
echo "  - 上传目录: ${UPLOAD_DIR:-/app/uploads}"
echo "  - 头像目录: ${AVATAR_DIR:-/app/avatars}"

# 执行传入的命令
echo "🚀 启动应用..."
exec "$@"

