#!/bin/bash
# Docker 部署检查脚本
# 用于验证 Docker 部署配置是否正确

set -e

echo "🔍 BlogN2 Docker 部署检查"
echo "================================"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi
echo "✅ Docker 已安装: $(docker --version)"

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi
echo "✅ Docker Compose 已安装"

# 检查必要文件
echo ""
echo "📁 检查必要文件:"
# 在 docker 目录中的文件
docker_files=("Dockerfile" "docker-compose.yml" "docker-entrypoint.sh" "env.docker.example")
for file in "${docker_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ docker/$file"
    else
        echo "  ❌ docker/$file 不存在"
        exit 1
    fi
done
# 在项目根目录的文件
if [ -f "../.dockerignore" ]; then
    echo "  ✅ .dockerignore (项目根目录)"
else
    echo "  ⚠️  .dockerignore 不在项目根目录（可选）"
fi

# 检查 .env 文件（在项目根目录或 docker 目录中）
echo ""
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    
    # 检查关键环境变量
    echo ""
    echo "🔑 检查关键环境变量:"
    
    if grep -q "DATABASE_URL=" .env && ! grep -q "DATABASE_URL=postgresql+asyncpg://.*@.*:.*/" .env; then
        echo "  ⚠️  DATABASE_URL 需要配置"
    else
        echo "  ✅ DATABASE_URL 已配置"
    fi
    
    if grep -q "CACHE_REDIS_HOST=" .env; then
        echo "  ✅ CACHE_REDIS_HOST 已配置"
    else
        echo "  ⚠️  CACHE_REDIS_HOST 需要配置"
    fi
    
    if grep -q "SECRET_KEY=" .env && ! grep -q "SECRET_KEY=your-super-secret" .env; then
        echo "  ✅ SECRET_KEY 已配置"
    else
        echo "  ⚠️  SECRET_KEY 需要修改（生产环境）"
    fi
elif [ -f "../.env" ]; then
    echo "✅ .env 文件存在于项目根目录"
else
    echo "⚠️  .env 文件不存在，请从 env.docker.example 复制"
    echo "   运行: cp docker/env.docker.example .env"
fi

# 检查目录（在项目根目录中）
echo ""
echo "📂 检查必要目录:"
dirs=("uploads" "avatars")
for dir in "${dirs[@]}"; do
    if [ -d "../$dir" ]; then
        echo "  ✅ ../$dir/"
    else
        echo "  ⚠️  ../$dir/ 不存在，将自动创建"
        mkdir -p "../$dir"
        chmod 755 "../$dir"
    fi
done

# 检查 docker-entrypoint.sh 权限
echo ""
if [ -x "docker-entrypoint.sh" ]; then
    echo "✅ docker-entrypoint.sh 有执行权限"
else
    echo "⚠️  docker-entrypoint.sh 没有执行权限，正在修复..."
    chmod +x docker-entrypoint.sh
    echo "✅ 已修复"
fi

# 检查 Docker Compose 配置
echo ""
echo "🐳 检查 Docker Compose 配置:"
if docker-compose config &> /dev/null || docker compose config &> /dev/null; then
    echo "  ✅ docker-compose.yml 配置有效"
else
    echo "  ❌ docker-compose.yml 配置有误"
    exit 1
fi

echo ""
echo "================================"
echo "✅ 检查完成！"
echo ""
echo "下一步："
echo "  1. 确保 .env 文件配置正确（在项目根目录）"
echo "  2. 在 docker 目录中运行: docker-compose build"
echo "  3. 在 docker 目录中运行: docker-compose up -d"
echo "  4. 查看日志: docker-compose logs -f"

