#!/bin/bash

echo "🚀 启动DND Discord Bot (后台运行)..."

# 检查并杀死现有进程
echo "🔍 检查现有进程..."
EXISTING_PID=$(ps aux | grep "python3 main.py" | grep -v grep | awk '{print $2}')
if [ -n "$EXISTING_PID" ]; then
    echo "🔧 发现现有进程 PID: $EXISTING_PID，正在终止..."
    kill -9 $EXISTING_PID
    sleep 2
fi

# SSL证书验证配置
export PYTHONHTTPSVERIFY=0
export SSL_VERIFY=false
export CURL_CA_BUNDLE=""
export REQUESTS_CA_BUNDLE=""

# 代理配置
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890

echo "✅ 环境变量已设置"

# 创建日志文件
LOG_FILE="bot_$(date +%Y%m%d_%H%M%S).log"
echo "📝 日志文件: $LOG_FILE"

# 后台启动机器人
echo "🚀 启动机器人..."
nohup python3 main.py > $LOG_FILE 2>&1 &

# 获取进程ID
PYTHON_PID=$!
echo "✅ 机器人已启动，PID: $PYTHON_PID"

# 等待一会儿检查启动状态
echo "⏳ 等待启动..."
sleep 5

# 检查进程是否还在运行
if ps -p $PYTHON_PID > /dev/null; then
    echo "✅ 机器人运行正常"
    echo "📝 查看日志: tail -f $LOG_FILE"
    echo "🔧 停止机器人: kill $PYTHON_PID"
else
    echo "❌ 机器人启动失败，查看日志: cat $LOG_FILE"
    exit 1
fi

# 显示最新日志
echo ""
echo "📊 最新日志:"
echo "=" * 50
tail -20 $LOG_FILE

echo ""
echo "🎯 机器人运行中，使用以下命令:"
echo "   查看日志: tail -f $LOG_FILE"
echo "   停止机器人: kill $PYTHON_PID"
echo "   检查进程: ps -p $PYTHON_PID" 