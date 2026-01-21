#!/bin/bash
set -e

# Docker 启动脚本
# 用于在容器启动时执行必要的检查和初始化

echo "🚀 BlogN2 容器启动中..."

# 加载配置文件（如果 BLOGN_CONFIG_FILE 环境变量已设置）
if [ -n "$BLOGN_CONFIG_FILE" ] && [ -f "$BLOGN_CONFIG_FILE" ]; then
    echo "📄 从配置文件加载环境变量: $BLOGN_CONFIG_FILE"
    # 使用 Python 加载 .env 文件并导出环境变量到当前 shell
    # 注意：使用 override=True 确保配置文件中的值覆盖已存在的环境变量
    eval "$(python3 << 'PYTHON_EOF'
import os
from pathlib import Path
from dotenv import load_dotenv

config_file = os.getenv("BLOGN_CONFIG_FILE")
if config_file and Path(config_file).exists():
    # 加载配置文件（override=True 确保配置文件中的值覆盖已存在的环境变量）
    load_dotenv(config_file, override=True)
    # 导出所有环境变量到 shell（只导出应用相关的变量）
    for key, value in os.environ.items():
        # 检查是否匹配前缀或完全匹配特定变量
        if any(key.startswith(prefix) for prefix in [
            "DATABASE_", "CACHE_", "MODEL_", "APP_", "SECRET_", 
            "DEBUG", "BASE_URL", "UPLOAD_", "AVATAR_"
        ]) or key in ["LOG_LEVEL"]:
            # MODEL_ 前缀已经包含 MODEL_ENABLE_MODEL，无需额外处理
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
if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "" ]; then
    echo "❌ 错误: DATABASE_URL 环境变量未设置或为空"
    echo "   请确保："
    echo "   1. BLOGN_CONFIG_FILE 环境变量指向正确的配置文件路径（容器内路径）"
    echo "   2. 配置文件包含 DATABASE_URL 配置项"
    echo "   3. 配置文件已通过 volume 挂载到容器内"
    if [ -n "$BLOGN_CONFIG_FILE" ]; then
        echo "   4. 当前配置的配置文件路径: $BLOGN_CONFIG_FILE"
        if [ -f "$BLOGN_CONFIG_FILE" ]; then
            echo "   5. 配置文件存在，但可能缺少 DATABASE_URL 配置项"
            echo "   6. 检查配置文件内容（前20行）："
            head -20 "$BLOGN_CONFIG_FILE" | grep -i "DATABASE" || echo "      未找到 DATABASE_URL 配置"
        else
            echo "   5. 配置文件不存在，请检查 volume 挂载配置"
        fi
    fi
    echo ""
    echo "   调试信息："
    echo "   - BLOGN_CONFIG_FILE: ${BLOGN_CONFIG_FILE:-未设置}"
    echo "   - DATABASE_URL 长度: ${#DATABASE_URL}"
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

# 显示模型启用状态
if [ -n "$MODEL_ENABLE_MODEL" ]; then
    if [ "$MODEL_ENABLE_MODEL" = "true" ] || [ "$MODEL_ENABLE_MODEL" = "1" ] || [ "$MODEL_ENABLE_MODEL" = "yes" ]; then
        MODEL_STATUS="已启用"
    else
        MODEL_STATUS="已禁用"
    fi
else
    MODEL_STATUS="已启用（默认）"
fi
echo "  - BERT模型: ${MODEL_STATUS}"
echo "  - 模型设备: ${MODEL_DEVICE:-cpu}"
echo "  - 模型缓存目录: ${MODEL_CACHE_DIR:-/app/.cache/models}"
echo "  - 上传目录: ${UPLOAD_DIR:-/app/uploads}"
echo "  - 头像目录: ${AVATAR_DIR:-/app/avatars}"

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
    
    # 如果没有指定 --log-level，则添加
    if [ "$HAS_LOG_LEVEL" = false ]; then
        # 执行 uvicorn 命令，添加日志级别参数
        # 注意：应用启动成功消息会在应用代码中通过 logger.warning() 输出
        # 使用 exec 替换当前进程，如果启动失败会直接退出容器
        exec uvicorn "${@:2}" --log-level "$LOG_LEVEL" || {
            echo "❌ 应用启动失败，退出码: $?"
            exit 1
        }
    else
        # 如果已经指定了 --log-level，直接执行，不添加
        exec uvicorn "${@:2}" || {
            echo "❌ 应用启动失败，退出码: $?"
            exit 1
        }
    fi
else
    # 其他命令直接执行
    exec "$@" || {
        echo "❌ 命令执行失败，退出码: $?"
        exit 1
    }
fi

