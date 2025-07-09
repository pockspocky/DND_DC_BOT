# Docker 部署指南

> **完美解决SSL连接问题的推荐部署方式**

## 🐳 为什么选择Docker？

Docker部署能够完美解决以下问题：
- ✅ **SSL连接问题**: 使用现代OpenSSL版本
- ✅ **环境一致性**: 避免本地环境差异
- ✅ **依赖管理**: 自动处理所有依赖
- ✅ **一键部署**: 简化部署流程
- ✅ **服务管理**: 自动重启和健康检查

## 📋 前置要求

### 系统要求
- macOS 10.15+ / Windows 10+ / Linux
- Docker 20.10+
- Docker Compose 1.29+

### 安装Docker
**macOS/Windows**: 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

**Linux (Ubuntu)**:
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🚀 快速部署

### 1. 获取项目
```bash
git clone https://github.com/yourusername/DND_DC_BOT.git
cd DND_DC_BOT
```

### 2. 配置环境变量
```bash
# 复制配置模板
cp docker.env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

**必填配置**:
```env
DISCORD_TOKEN=your_actual_discord_bot_token_here
```

**可选配置**:
```env
PROXY_URL=http://127.0.0.1:7890  # 如果需要代理
PREFIX=!                         # 命令前缀
LOG_LEVEL=INFO                   # 日志级别
```

### 3. 配置Docker代理（如果需要）
如果您的网络环境需要代理才能访问外网：

**macOS/Windows**: 
1. 打开 Docker Desktop
2. 设置 → Resources → Proxies
3. 启用代理并填写代理地址

**Linux**:
```bash
# 创建Docker代理配置
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"
EOF

# 重启Docker服务
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 4. 一键部署
```bash
chmod +x deploy-docker.sh
./deploy-docker.sh
```

## 🔧 服务管理

### 查看状态
```bash
./deploy-docker.sh --status
# 或者
docker-compose ps
```

### 查看日志
```bash
./deploy-docker.sh --logs
# 或者
docker-compose logs -f
```

### 重启服务
```bash
./deploy-docker.sh --restart
# 或者
docker-compose restart
```

### 停止服务
```bash
./deploy-docker.sh --down
# 或者
docker-compose down
```

### 更新机器人
```bash
# 拉取最新代码
git pull

# 重新构建和部署
./deploy-docker.sh
```

## 📊 健康检查

部署脚本会自动进行健康检查：

```bash
# 手动检查容器状态
docker-compose exec dnd-bot python3 -c "
import sqlite3, ssl
print(f'✅ SQLite: 数据库连接正常')
print(f'✅ SSL版本: {ssl.OPENSSL_VERSION}')
print('✅ 容器状态: 运行中')
"
```

## 🛠️ 故障排除

### 常见问题

**1. Docker镜像下载失败**
```
ERROR: failed to resolve source metadata for docker.io/library/python:3.11-slim
```
**解决方案**: 配置Docker代理或更换网络环境

**2. 环境变量未设置**
```
ERROR: 请在.env文件中配置正确的DISCORD_TOKEN
```
**解决方案**: 编辑`.env`文件，设置正确的Discord token

**3. 端口冲突**
```
ERROR: Port 8080 is already in use
```
**解决方案**: 停止占用端口的服务或修改`docker-compose.yml`中的端口配置

**4. 权限问题**
```
ERROR: Permission denied
```
**解决方案**: 确保脚本有执行权限 `chmod +x deploy-docker.sh`

### 调试命令

```bash
# 查看容器日志
docker-compose logs --tail=50

# 进入容器调试
docker-compose exec dnd-bot /bin/bash

# 查看容器资源使用
docker stats

# 清理Docker缓存
docker system prune -a
```

## 🔐 安全建议

1. **保护环境变量文件**
   ```bash
   chmod 600 .env
   ```

2. **定期更新镜像**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

3. **监控日志**
   ```bash
   # 定期检查日志
   ./deploy-docker.sh --logs | grep ERROR
   ```

4. **备份数据**
   ```bash
   # 备份数据库
   cp dnd_bot.db dnd_bot.db.backup
   ```

## 📈 性能优化

### 资源限制
在`docker-compose.yml`中已配置：
- CPU限制: 1核心
- 内存限制: 512MB
- 预留资源: 0.5核心 + 256MB

### 日志管理
- 日志文件最大10MB
- 保留最近3个日志文件
- 自动轮转清理

### 数据持久化
- 数据库文件: `./dnd_bot.db`
- 日志目录: `./logs/`
- 数据目录: `./data/`

## 🎯 部署验证

部署成功后，您应该看到：

1. **容器运行状态**
   ```
   dnd-discord-bot   Up   healthy
   ```

2. **成功日志**
   ```
   INFO - Dungeon's Token#9617 已成功登录!
   INFO - 连接到 1 个服务器
   INFO - 已同步 21 个斜杠命令
   ```

3. **Discord中机器人在线**
   - 机器人显示在线状态
   - 斜杠命令自动补全可用
   - `/ping` 命令响应正常

## 🎉 部署完成

恭喜！您的DND Discord Bot现在运行在Docker容器中，享受：
- 🔐 **安全的SSL连接**
- 🚀 **稳定的服务运行**
- 🛠️ **便捷的服务管理**
- 📊 **完整的监控体系**

如有问题，请查看[故障排除指南](troubleshooting.md)或提交[Issue](https://github.com/yourusername/DND_DC_BOT/issues)。 