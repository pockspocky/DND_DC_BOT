#!/bin/bash
# Discord机器人启动脚本
# 解决代理连接问题

echo "🚀 启动Discord机器人..."

# 设置代理环境变量
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890

echo "代理设置:"
echo "  HTTP_PROXY=$HTTP_PROXY"
echo "  HTTPS_PROXY=$HTTPS_PROXY"
echo "  ALL_PROXY=$ALL_PROXY"

# 验证代理连接
echo "验证代理连接..."
curl -s --connect-timeout 5 --proxy $HTTP_PROXY https://discord.com/api/v10/gateway >/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 代理连接正常"
    echo "启动机器人..."
    python3 main.py
else
    echo "❌ 代理连接失败"
    echo "请检查代理服务是否正常运行"
    echo "确保代理软件在 127.0.0.1:7890 端口运行"
fi
