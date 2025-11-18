#!/bin/bash
# 配置 Docker 镜像源（用于加速拉取）

echo "🔧 配置 Docker 镜像源"
echo "================================"

DOCKER_DAEMON_JSON="/etc/docker/daemon.json"
BACKUP_FILE="/etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)"

# 创建备份
if [ -f "$DOCKER_DAEMON_JSON" ]; then
    echo "备份现有配置..."
    sudo cp "$DOCKER_DAEMON_JSON" "$BACKUP_FILE"
    echo "✅ 备份已保存到: $BACKUP_FILE"
fi

# 配置镜像源
echo ""
echo "配置镜像源..."
sudo mkdir -p /etc/docker

# 使用阿里云镜像源（根据实际情况修改）
sudo tee "$DOCKER_DAEMON_JSON" > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF

echo "✅ 镜像源配置完成"
echo ""
echo "重启 Docker daemon 以应用配置..."
echo "  停止: sudo kill \$(pgrep dockerd)"
echo "  启动: sudo dockerd > /tmp/dockerd.log 2>&1 &"
echo ""
echo "或者使用: ./start-docker-wsl.sh"


