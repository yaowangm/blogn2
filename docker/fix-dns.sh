#!/bin/bash
# 修复 DNS 配置以访问 Docker 镜像源

echo "🔧 修复 DNS 配置"
echo "================================"

# 备份原配置
if [ -f /etc/resolv.conf ]; then
    sudo cp /etc/resolv.conf /etc/resolv.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份原 DNS 配置"
fi

# 创建新的 DNS 配置（使用公共 DNS）
echo ""
echo "配置 DNS 服务器..."
sudo tee /etc/resolv.conf > /dev/null <<EOF
# DNS 配置（用于访问 Docker 镜像源）
nameserver 114.114.114.114
nameserver 8.8.8.8
nameserver 223.5.5.5
EOF

echo "✅ DNS 配置已更新"
echo ""
echo "测试 DNS 解析..."
nslookup docker.mirrors.ustc.edu.cn 2>&1 | head -5

echo ""
echo "💡 注意：WSL 可能会自动覆盖此配置"
echo "   如果配置被重置，可以："
echo "   1. 在 /etc/wsl.conf 中禁用自动生成"
echo "   2. 或每次启动后重新运行此脚本"


