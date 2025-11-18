# 配置 Docker 镜像源步骤

由于需要 sudo 权限，请手动执行以下命令：

## 步骤 1: 创建 Docker 配置目录

```bash
sudo mkdir -p /etc/docker
```

## 步骤 2: 创建配置文件

```bash
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
```

## 步骤 3: 验证配置文件

```bash
sudo cat /etc/docker/daemon.json
```

应该看到 JSON 格式的配置内容。

## 步骤 4: 重启 Docker daemon

```bash
# 停止当前运行的 dockerd
sudo kill $(pgrep dockerd)

# 重新启动（使用启动脚本）
cd /home/wy/blogn2/docker
./start-docker-wsl.sh
```

## 步骤 5: 验证镜像源是否生效

```bash
docker info | grep -A 10 "Registry Mirrors"
```

应该能看到配置的镜像源地址。

## 完成

配置完成后，可以继续执行部署：

```bash
cd /home/wy/blogn2/docker
./deploy.sh
```


