# 通过 Apache + HTTPS 访问 blogn2（bloggern.com）

本文说明在已有 Apache2 的宿主机上，如何通过 HTTP/HTTPS 访问 Docker 中监听 8000 端口的 blogn2，域名以 `bloggern.com` 为例。

---

## 一、Apache 反向代理配置

### 1.1 启用代理模块

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel
sudo systemctl reload apache2
```

若 blogn2 内无 WebSocket，可不启用 `proxy_wstunnel`。

### 1.2 新建站点配置

在 `/etc/apache2/sites-available/` 下新建 `bloggern.conf`。

**仅 HTTP 示例：**

```apache
<VirtualHost *:80>
    ServerName bloggern.com
    # 若需 www：ServerAlias www.bloggern.com

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    ErrorLog ${APACHE_LOG_DIR}/bloggern_error.log
    CustomLog ${APACHE_LOG_DIR}/bloggern_access.log combined
</VirtualHost>
```

**若有 WebSocket**（按 blogn2 实际路径调整）：

```apache
# ProxyPass /ws ws://127.0.0.1:8000/ws
# ProxyPassReverse /ws ws://127.0.0.1:8000/ws
```

### 1.3 启用并重载

```bash
sudo a2ensite bloggern.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

### 1.4 配置 HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d bloggern.com
```

按提示选择“将 HTTP 重定向到 HTTPS”后，certbot 会为 `bloggern.com` 申请证书并自动生成 443 的 VirtualHost，代理到本机 8000。

### 1.5 应用侧“对外地址”配置

若 blogn2 会生成绝对链接（如重置密码邮件中的链接），需在应用或环境变量中配置对外协议与域名，例如：

- `BASE_URL=https://bloggern.com`
- 或由 Apache 传递 `X-Forwarded-Proto`、`X-Forwarded-Host`，应用读取后生成正确 URL。

否则重定向或邮件中的链接可能指向 `http://localhost:8000/...`。

### 1.6 子路径发布（可选）

若不以根路径 `/` 发布，而是例如 `/blog`：

```apache
ProxyPass /blog http://127.0.0.1:8000/
ProxyPassReverse /blog http://127.0.0.1:8000/
```

此时 blogn2 需配置应用根路径为 `/blog`（若支持），否则静态资源与重定向会出错。

### 1.7 安全与网络

- 仅通过 Apache 访问时，Docker 可将 8000 只绑定到本机：`-p 127.0.0.1:8000:8000`，外网不直接暴露 8000。
- Docker 与 Apache 在同一台机时，用 `127.0.0.1:8000` 即可；若 Docker 在另一台机器，将地址改为该机内网 IP。

---

## 二、Certbot 是怎样工作的

### 2.1 角色

- **Let's Encrypt**：免费、自动化的证书颁发机构（CA）。
- **Certbot**：与 Let's Encrypt 通信，自动完成“证明域名控制权 → 领取证书 → 安装到本机（如 Apache）”的客户端。

### 2.2 如何证明“你控制 bloggern.com”

Let's Encrypt 只会在验证你控制该域名后签发证书，常见两种方式：

**HTTP-01 挑战（最常用）**

- Let's Encrypt 给出一个随机 token。
- 你需在 `http://bloggern.com/.well-known/acme-challenge/<token>` 上提供该 token 的内容。
- Certbot 会在本机临时提供该 URL（写文件由 Apache 提供，或 standalone 模式临时监听 80）。
- Let's Encrypt 访问该 URL，校验通过即签发证书。

**DNS-01 挑战**

- 在域名 DNS 中按要求添加一条 TXT 记录。
- 适合 80 端口无法从公网访问、但能改 DNS 的场景。

### 2.3 一次完整流程（HTTP-01 + Apache）

1. 执行：`certbot --apache -d bloggern.com`。
2. Certbot 向 Let's Encrypt 的 ACME 服务器申请证书。
3. Let's Encrypt 返回 HTTP-01 挑战：在 `http://bloggern.com/.well-known/acme-challenge/<token>` 提供指定内容。
4. Certbot 在本机提供该 URL（写文件并配置 Apache，或 standalone 监听 80）。
5. Let's Encrypt 访问该 URL，校验通过后签发证书并返回给 Certbot。
6. Certbot 将证书和私钥写入本机（如 `/etc/letsencrypt/live/bloggern.com/`），并修改 Apache 的 443 VirtualHost（`SSLCertificateFile`、`SSLCertificateKeyFile` 等），可选添加 80→443 重定向。
7. Certbot 触发 Apache 重载，之后 `https://bloggern.com` 即使用新证书。

### 2.4 续期

- Let's Encrypt 证书约 90 天有效。
- Certbot 会安装 systemd timer 或 cron，定期执行 `certbot renew`，在到期前自动续期并重载 Apache。

### 2.5 小结

| 步骤     | 执行方        | 内容说明                                   |
|----------|---------------|--------------------------------------------|
| 申请     | Certbot       | 向 Let's Encrypt 申请 bloggern.com 证书     |
| 挑战     | Let's Encrypt | 要求通过 HTTP 或 DNS 证明域名控制权         |
| 响应挑战 | Certbot       | 在本机提供 URL 内容或配置 DNS              |
| 验证     | Let's Encrypt | 访问 URL / 查 DNS，通过则签发证书          |
| 安装     | Certbot       | 保存证书并配置 Apache，重载服务            |
| 续期     | Certbot       | 定时执行 `certbot renew` 自动续期          |

---

## 三、推荐使用哪个版本的 Certbot

### 3.1 建议

使用**当前稳定版**，并通过**官方源或 Snap** 安装，以便获得安全更新和兼容性。

### 3.2 安装方式

**系统包管理器（Ubuntu/Debian）**

```bash
sudo apt install certbot python3-certbot-apache
```

要跟紧最新版，可添加官方 PPA：

```bash
sudo add-apt-repository ppa:certbot/certbot
sudo apt update && sudo apt install certbot python3-certbot-apache
```

**Snap（官方推荐）**

Let's Encrypt 文档当前推荐用 Snap，便于自动更新到最新稳定版：

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
# Apache 插件等：sudo snap install certbot-apache
```

### 3.3 不推荐

- 长期锁定过旧版本号，可能缺少安全补丁或新特性。
- 用 `pip install certbot` 装到系统 Python，易与系统包冲突；优先用系统包或 Snap。

### 3.4 总结

- **版本**：不指定具体数字，用“当前稳定版”即可。
- **安装**：有 Snap 则优先 Snap；否则用发行版或 PPA 的 `certbot` + `python3-certbot-apache`。
