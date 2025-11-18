#!/bin/bash
# BlogN2 Docker 部署脚本
# 用于在本地部署 BlogN2 应用

set -e

echo "🚀 BlogN2 Docker 部署脚本"
echo "================================"

# 检查 Docker 是否运行
if ! docker ps &>/dev/null; then
    echo "❌ Docker daemon 未运行"
    echo ""
    echo "在 WSL 环境中，请尝试以下方法："
    echo ""
    echo "方法 1: 使用 service 命令（如果可用）"
    echo "  sudo service docker start"
    echo ""
    echo "方法 2: 手动启动 dockerd（后台运行）"
    echo "  sudo dockerd > /dev/null 2>&1 &"
    echo ""
    echo "方法 3: 使用 Docker Desktop for Windows"
    echo "  确保 Windows 上的 Docker Desktop 正在运行"
    echo ""
    echo "方法 4: 检查 Docker socket 权限"
    echo "  sudo chmod 666 /var/run/docker.sock"
    echo "  或添加用户到 docker 组: sudo usermod -aG docker $USER"
    echo ""
    read -p "按 Enter 重试，或 Ctrl+C 退出..."
    
    # 重试检查
    if ! docker ps &>/dev/null; then
        echo "❌ Docker 仍然无法连接，请手动启动 Docker daemon"
        exit 1
    fi
fi
echo "✅ Docker 服务运行正常"

# 检查必要文件
echo ""
echo "📁 检查必要文件..."
if [ ! -f "../.env" ]; then
    echo "⚠️  .env 文件不存在，从模板创建..."
    cp env.docker.example ../.env
    echo "✅ 已创建 .env 文件，请编辑配置："
    echo "   nano ../.env"
    echo ""
    echo "⚠️  请确保配置以下关键项："
    echo "   - DATABASE_URL: PostgreSQL 连接 URL"
    echo "   - CACHE_REDIS_HOST: Redis 主机地址（使用 localhost 或 127.0.0.1）"
    echo "   - SECRET_KEY: JWT 密钥"
    read -p "按 Enter 继续（确保已配置 .env 文件）..."
fi

# 检查上传目录
echo ""
echo "📂 检查必要目录..."
mkdir -p ../uploads ../avatars
chmod 755 ../uploads ../avatars
echo "✅ 上传目录已准备"

# 加载环境变量（处理空值和注释，跳过格式错误的行）
if [ -f "../.env" ]; then
    while IFS= read -r line; do
        # 跳过注释和空行
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        # 只处理格式正确的行（包含 = 且等号前没有空格）
        if [[ "$line" =~ ^[^=]+=[^=]*$ ]] && [[ ! "$line" =~ [[:space:]]=[[:space:]] ]]; then
            export "$line" 2>/dev/null || true
        fi
    done < ../.env
fi

# 检查关键环境变量
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL 未设置"
    exit 1
fi

if [ -z "$CACHE_REDIS_HOST" ]; then
    echo "⚠️  CACHE_REDIS_HOST 未设置，使用默认值 localhost"
    export CACHE_REDIS_HOST=localhost
fi

# 构建镜像
echo ""
echo "🔨 构建 Docker 镜像..."
docker build -f Dockerfile -t blogn2:latest ..

# 停止并删除旧容器（如果存在）
echo ""
echo "🛑 停止旧容器（如果存在）..."
docker stop blogn2-app 2>/dev/null || true
docker rm blogn2-app 2>/dev/null || true

# 启动容器
echo ""
echo "🚀 启动容器..."
docker run -d \
    --name blogn2-app \
    --restart unless-stopped \
    --network host \
    --env-file ../.env \
    -e CACHE_REDIS_HOST=${CACHE_REDIS_HOST:-localhost} \
    -e MODEL_CACHE_DIR=/app/.cache/huggingface \
    -e MODEL_PREFER_LOCAL=true \
    -v "$(pwd)/../uploads:/app/uploads" \
    -v "$(pwd)/../avatars:/app/avatars" \
    -v "$HOME/.cache/huggingface:/app/.cache/huggingface:ro" \
    -v "$HOME/.cache/modelscope:/app/.cache/modelscope:ro" \
    blogn2:latest

# 等待容器启动
echo ""
echo "⏳ 等待容器启动..."
sleep 5

# 检查容器状态
echo ""
echo "📊 容器状态："
docker ps | grep blogn2-app || echo "⚠️  容器未运行"

# 查看日志
echo ""
echo "📋 查看容器日志（最后 20 行）："
docker logs --tail 20 blogn2-app

echo ""
echo "================================"
echo "✅ 部署完成！"
echo ""
echo "📝 常用命令："
echo "  查看日志: docker logs -f blogn2-app"
echo "  停止容器: docker stop blogn2-app"
echo "  启动容器: docker start blogn2-app"
echo "  重启容器: docker restart blogn2-app"
echo "  进入容器: docker exec -it blogn2-app bash"
echo ""
echo "🌐 访问地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"

