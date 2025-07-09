# 使用Python 3.11官方镜像（包含现代OpenSSL）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHON_VERSION=3.11
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    openssl \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 升级pip和安装Python构建工具
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制需求文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 设置权限
RUN chmod +x start_bot_with_proxy.sh || true
RUN chmod +x start_bot_ssl_fix.sh || true
RUN chmod +x start_bot_background.sh || true

# 创建非root用户
RUN groupadd -r botuser && useradd -r -g botuser botuser
RUN chown -R botuser:botuser /app
USER botuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sqlite3; sqlite3.connect('dnd_bot.db').close()" || exit 1

# 暴露端口（如果需要）
EXPOSE 8080

# 启动命令
CMD ["python3", "main.py"] 