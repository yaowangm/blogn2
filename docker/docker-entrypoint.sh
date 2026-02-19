#!/bin/bash
set -e

# Docker 启动脚本
# 用于在容器启动时执行必要的检查和初始化
# 密码重置邮件通过 SMTP 连接宿主机 sendmail（配置 SMTP_HOST=localhost 且使用 host 网络）

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
        # 检查是否匹配前缀或完全匹配特定变量
        if any(key.startswith(prefix) for prefix in [
            "DATABASE_", "CACHE_", "MODEL_", "APP_", "SECRET_", 
            "DEBUG", "BASE_URL", "UPLOAD_", "AVATAR_", "SMTP_", "MAIL_", "RESET_LINK"
        ]) or key in ["LOG_LEVEL"]:
            # 转义单引号
            value_escaped = value.replace("'", "'\"'\"'")
            print(f"export {key}='{value_escaped}'")
PYTHON_EOF
)"
    if [ -n "$DATABASE_URL" ]; then
        echo "✅ 已从配置文件加载 DATABASE_URL 等变量"
    else
        echo "⚠️  配置文件已读取，但未包含 DATABASE_URL，请检查文件格式与键名"
    fi
else
    if [ -n "$BLOGN_CONFIG_FILE" ]; then
        echo "⚠️  警告: 配置文件不存在: $BLOGN_CONFIG_FILE"
    else
        echo "⚠️  警告: BLOGN_CONFIG_FILE 未设置，使用环境变量或默认配置"
    fi
fi

# --- BERT 模型路径：若当前路径无 config.json，从挂载的 HF hub 解析到 snapshots/<revision> ---
if [ -z "$MODEL_PREFER_LOCAL" ]; then
    export MODEL_PREFER_LOCAL=true
fi
# 从 hub 目录（含 snapshots/）中取第一个含 config.json 的 snapshot 路径
_resolve_snapshot() {
    local hub_dir="$1"
    [ -d "$hub_dir/snapshots" ] || return 1
    local snap
    snap=$(ls -1d "$hub_dir/snapshots/"*/ 2>/dev/null | head -1)
    [ -n "$snap" ] && [ -f "${snap}config.json" ] && echo "${snap%/}" && return 0
    return 1
}
if [ -z "$MODEL_MODEL_PATH" ] || [ ! -f "$MODEL_MODEL_PATH/config.json" ]; then
    SNAPSHOT_PATH=""
    for HUB_DIR in "/app/.cache/models/bert-model-hub" "/app/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"; do
        SNAPSHOT_PATH=$(_resolve_snapshot "$HUB_DIR") || true
        if [ -n "$SNAPSHOT_PATH" ]; then
            export MODEL_MODEL_PATH="$SNAPSHOT_PATH"
            echo "从 hub 解析到 snapshot: $MODEL_MODEL_PATH"
            break
        fi
    done
    [ -z "$MODEL_MODEL_PATH" ] && export MODEL_MODEL_PATH=/app/.cache/models/bert-model
fi
echo "MODEL_MODEL_PATH=$MODEL_MODEL_PATH"
if [ -f "$MODEL_MODEL_PATH/config.json" ]; then
    echo "模型目录有效（含 config.json）"
elif [ -d "$MODEL_MODEL_PATH" ]; then
    echo "⚠️  模型目录无 config.json，请挂载 HF hub 到 /app/.cache/models/bert-model-hub 或挂载 snapshot 到 $MODEL_MODEL_PATH"
else
    echo "⚠️  模型目录不存在，请检查 docker-compose volumes 挂载"
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
    # 使用 Python 安全地隐藏密码（处理密码中包含 @ 的情况）
    DB_DISPLAY=$(python3 << 'PYTHON_EOF'
from urllib.parse import urlparse, urlunparse
import sys

url = sys.stdin.read().strip()
try:
    # 解析 URL
    parsed = urlparse(url)
    
    # 如果有用户名
    if parsed.username:
        # 如果有密码，隐藏密码；如果没有密码，只显示用户名
        if parsed.password:
            # 构建新的 netloc（只包含用户名，密码用 *** 替换）
            if parsed.port:
                new_netloc = f'{parsed.username}:***@{parsed.hostname}:{parsed.port}'
            else:
                new_netloc = f'{parsed.username}:***@{parsed.hostname}'
        else:
            # 没有密码，只显示用户名
            if parsed.port:
                new_netloc = f'{parsed.username}@{parsed.hostname}:{parsed.port}'
            else:
                new_netloc = f'{parsed.username}@{parsed.hostname}'
        
        # 重新构建 URL
        new_parsed = parsed._replace(netloc=new_netloc)
        print(urlunparse(new_parsed))
    else:
        print(url)
except Exception:
    # 如果解析失败，使用简单的正则表达式作为后备
    # 注意：这种方法可能无法正确处理密码中包含 @ 的情况
    # 但作为后备方案，总比不隐藏密码好
    import re
    # 匹配最后一个 @ 之前的内容（假设密码中的 @ 应该被 URL 编码为 %40）
    result = re.sub(r'://([^:]+):[^@]*@', r'://\1:***@', url)
    print(result)
PYTHON_EOF
    <<< "$DATABASE_URL")
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

# 容器内若使用宿主机路径（如 /home/...），该路径在容器中不存在，会导致 /upload/、/avatar/ 返回 404
case "${UPLOAD_DIR:-/app/uploads}" in /home/*|/Users/*) echo "⚠️  上传目录为宿主机路径，容器内无法访问，图片会 404。请改为 UPLOAD_DIR=/app/uploads 并用 -v 挂载宿主机目录";; esac
case "${AVATAR_DIR:-/app/avatars}" in /home/*|/Users/*) echo "⚠️  头像目录为宿主机路径，容器内无法访问。请改为 AVATAR_DIR=/app/avatars 并用 -v 挂载宿主机目录";; esac

# 执行传入的命令
echo "🚀 启动应用..."

# 如果命令是 uvicorn，添加日志级别参数（如果未指定）
if [ "$1" = "uvicorn" ]; then
    # 设置日志级别（默认 warning，只显示错误和警告）
    LOG_LEVEL=${LOG_LEVEL:-warning}
    # 将日志级别转换为小写
    LOG_LEVEL=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')
    
    # 检查是否已经指定了 --log-level 参数
    HAS_LOG_LEVEL=false
    for arg in "${@:2}"; do
        if [ "$arg" = "--log-level" ] || [ "${arg%%=*}" = "--log-level" ]; then
            HAS_LOG_LEVEL=true
            break
        fi
    done
    
    # 显式传入 MODEL_*，确保 uvicorn 子进程使用 entrypoint 解析后的路径
    if [ "$HAS_LOG_LEVEL" = false ]; then
        exec env MODEL_MODEL_PATH="$MODEL_MODEL_PATH" MODEL_PREFER_LOCAL="${MODEL_PREFER_LOCAL:-true}" uvicorn "${@:2}" --log-level "$LOG_LEVEL"
    else
        exec env MODEL_MODEL_PATH="$MODEL_MODEL_PATH" MODEL_PREFER_LOCAL="${MODEL_PREFER_LOCAL:-true}" uvicorn "${@:2}"
    fi
else
    exec "$@"
fi

