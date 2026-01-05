#!/bin/bash
set -e

# Docker 启动脚本
# 用于在容器启动时执行必要的检查和初始化

echo "🚀 BlogN2 容器启动中..."

# 加载配置文件（如果 BLOGN_CONFIG_FILE 环境变量已设置）
if [ -n "$BLOGN_CONFIG_FILE" ] && [ -f "$BLOGN_CONFIG_FILE" ]; then
    echo "📄 从配置文件加载环境变量: $BLOGN_CONFIG_FILE"
    # 使用 Python 加载 .env 文件并导出环境变量到当前 shell
    eval "$(python3 << 'PYTHON_EOF'
import os
from pathlib import Path
from dotenv import load_dotenv

config_file = os.getenv("BLOGN_CONFIG_FILE")
if config_file and Path(config_file).exists():
    # 加载配置文件（override=False 表示不覆盖已存在的环境变量）
    load_dotenv(config_file, override=False)
    # 导出所有环境变量到 shell（只导出应用相关的变量）
    for key, value in os.environ.items():
        if any(key.startswith(prefix) for prefix in [
            "DATABASE_", "CACHE_", "MODEL_", "APP_", "SECRET_", 
            "DEBUG", "BASE_URL", "UPLOAD_", "AVATAR_"
        ]):
            # 转义单引号
            value_escaped = value.replace("'", "'\"'\"'")
            print(f"export {key}='{value_escaped}'")
PYTHON_EOF
)"
else
    if [ -n "$BLOGN_CONFIG_FILE" ]; then
        echo "⚠️  警告: 配置文件不存在: $BLOGN_CONFIG_FILE"
    else
        echo "⚠️  警告: BLOGN_CONFIG_FILE 未设置，使用环境变量或默认配置"
    fi
fi

# 检查必要的环境变量
if [ -z "$DATABASE_URL" ]; then
    echo "❌ 错误: DATABASE_URL 环境变量未设置"
    echo "   请确保："
    echo "   1. BLOGN_CONFIG_FILE 环境变量指向正确的配置文件路径（容器内路径）"
    echo "   2. 配置文件包含 DATABASE_URL 配置项"
    echo "   3. 配置文件已通过 volume 挂载到容器内"
    if [ -n "$BLOGN_CONFIG_FILE" ]; then
        echo "   4. 当前配置的配置文件路径: $BLOGN_CONFIG_FILE"
        if [ -f "$BLOGN_CONFIG_FILE" ]; then
            echo "   5. 配置文件存在，但可能缺少 DATABASE_URL 配置项"
        else
            echo "   5. 配置文件不存在，请检查 volume 挂载配置"
        fi
    fi
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
# 只对可写目录设置权限（模型缓存目录可能是只读挂载）
chmod -R 755 /app/uploads /app/avatars 2>/dev/null || true
chmod -R 755 "${MODEL_CACHE_DIR}" 2>/dev/null || true

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

# 安全地显示数据库连接信息（隐藏密码）
if [ -n "$DATABASE_URL" ]; then
    # 提取协议、用户名、主机和端口，隐藏密码
    DB_DISPLAY=$(echo "$DATABASE_URL" | sed -E 's|://([^:]+):([^@]+)@|://\1:***@|')
    echo "  - 数据库: ${DB_DISPLAY}"
else
    echo "  - 数据库: 未配置"
fi

echo "  - Redis: ${CACHE_REDIS_HOST:-localhost}:${CACHE_REDIS_PORT:-6379}"

# 显示缓存启用状态
if [ -n "$CACHE_ENABLE_CACHE" ]; then
    if [ "$CACHE_ENABLE_CACHE" = "true" ] || [ "$CACHE_ENABLE_CACHE" = "1" ]; then
        CACHE_STATUS="已启用"
    else
        CACHE_STATUS="已禁用"
    fi
else
    CACHE_STATUS="已启用（默认）"
fi
echo "  - 缓存: ${CACHE_STATUS}"

echo "  - 模型设备: ${MODEL_DEVICE:-cpu}"
echo "  - 模型缓存目录: ${MODEL_CACHE_DIR:-/app/.cache/models}"
echo "  - 上传目录: ${UPLOAD_DIR:-/app/uploads}"
echo "  - 头像目录: ${AVATAR_DIR:-/app/avatars}"

# 执行传入的命令
echo "🚀 启动应用..."

# 如果命令是 uvicorn，添加日志级别参数
if [ "$1" = "uvicorn" ]; then
    # 设置日志级别（默认 warning，只显示错误和警告）
    LOG_LEVEL=${LOG_LEVEL:-warning}
    # 将日志级别转换为小写
    LOG_LEVEL=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')
    # 执行 uvicorn 命令，添加日志级别参数
    # 注意：应用启动成功消息会在应用代码中通过 logger.warning() 输出
    exec uvicorn "$2" --host 0.0.0.0 --port 8000 --workers 1 --log-level "$LOG_LEVEL" "${@:3}"
else
    # 其他命令直接执行
    exec "$@"
fi

