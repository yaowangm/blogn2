# Docker 登录问题修复

## 问题描述

在 Docker 容器中部署时，登录功能失败，但本地直接运行正常。

## 根本原因

`passlib==1.7.4` 与 `bcrypt` 4.1.2+ 版本不兼容。新版本的 `bcrypt` 移除了 `__about__` 属性，导致 `passlib` 在尝试读取版本信息时失败：

```
AttributeError: module 'bcrypt' has no attribute '__about__'
(trapped) error reading bcrypt version
```

## 解决方案

固定 `bcrypt` 版本到 `4.0.1`，这是与 `passlib 1.7.4` 兼容的最新版本。

### 修改文件

1. **requirements-prod.txt**（Docker 生产环境）
2. **requirements.txt**（开发环境，保持一致性）

添加：
```
bcrypt==4.0.1
```

### 重新构建 Docker 镜像

```bash
# 重新构建镜像
docker build -f docker/Dockerfile -t blogn2-app .

# 停止并删除旧容器
docker stop blogn2-app
docker rm blogn2-app

# 启动新容器
docker run -d \
  --name blogn2-app \
  --restart unless-stopped \
  --network host \
  -e BLOGN_CONFIG_FILE=/app/config.env \
  -v /home/wy/.env:/app/config.env:ro \
  -v /home/wy/pic/blogn_img/upload:/app/uploads \
  -v /home/wy/pic/blogn_img/userlogo:/app/avatars \
  -v /home/wy/.cache/huggingface:/app/.cache/huggingface:ro \
  -v /home/wy/.cache/modelscope:/app/.cache/modelscope:ro \
  blogn2-app
```

## 诊断工具

如果问题仍然存在，可以在容器内运行诊断脚本：

```bash
# 复制诊断脚本到容器
docker cp scripts/diagnose_docker_login.sh blogn2-app:/tmp/

# 在容器内运行
docker exec blogn2-app bash /tmp/diagnose_docker_login.sh
```

诊断脚本会检查：
1. Python 版本
2. 关键依赖版本（passlib, bcrypt 等）
3. bcrypt 和 passlib 兼容性
4. 密码验证功能测试

## 验证修复

修复后，验证登录功能：

1. 检查容器日志，确认没有 bcrypt 相关错误
2. 尝试登录，确认可以正常登录
3. 如果仍有问题，运行诊断脚本查看详细信息

## 相关文件

- `requirements-prod.txt` - Docker 生产环境依赖
- `requirements.txt` - 开发环境依赖
- `scripts/diagnose_docker_login.sh` - 诊断脚本
- `docker/Dockerfile` - Docker 构建文件
