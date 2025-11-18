#!/bin/bash
# WSL 环境下启动 Docker daemon 脚本

echo "🔧 在 WSL 环境下启动 Docker daemon"
echo "================================"

# 检查是否已有 dockerd 在运行
if pgrep -x dockerd > /dev/null; then
    echo "✅ Docker daemon 已在运行 (PID: $(pgrep -x dockerd))"
    
    # 测试连接
    if docker ps &>/dev/null; then
        echo "✅ Docker 连接正常"
        exit 0
    else
        echo "⚠️  Docker daemon 运行但无法连接，检查 socket 权限..."
        if [ -S /var/run/docker.sock ]; then
            sudo chmod 666 /var/run/docker.sock
            if docker ps &>/dev/null; then
                echo "✅ 修复权限后连接正常"
                exit 0
            fi
        fi
    fi
fi

echo ""
echo "启动 Docker daemon..."

# 创建必要的目录
sudo mkdir -p /var/run
sudo mkdir -p /var/lib/docker

# 启动 dockerd（后台运行，输出到日志文件）
echo "正在启动 dockerd（这可能需要几秒钟）..."
sudo dockerd > /tmp/dockerd.log 2>&1 &
DOCKERD_PID=$!

# 等待 dockerd 启动
echo "等待 dockerd 启动..."
for i in {1..10}; do
    sleep 1
    if [ -S /var/run/docker.sock ]; then
        echo "✅ Docker socket 已创建"
        break
    fi
    echo "  等待中... ($i/10)"
done

# 设置 socket 权限
if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock
    echo "✅ 已设置 socket 权限"
fi

# 测试连接
sleep 2
if docker ps &>/dev/null; then
    echo "✅ Docker daemon 启动成功！"
    echo "   PID: $DOCKERD_PID"
    echo "   日志: /tmp/dockerd.log"
    echo ""
    echo "📝 提示："
    echo "   - 停止 dockerd: sudo kill $DOCKERD_PID"
    echo "   - 查看日志: tail -f /tmp/dockerd.log"
    exit 0
else
    echo "❌ Docker daemon 启动失败"
    echo "查看日志:"
    tail -20 /tmp/dockerd.log
    echo ""
    echo "💡 如果看到权限错误，尝试："
    echo "   sudo chmod 666 /var/run/docker.sock"
    exit 1
fi


