#!/bin/bash

echo "🔧 启动DND Discord Bot (SSL修复版)..."

# SSL证书验证配置
export PYTHONHTTPSVERIFY=0
export SSL_VERIFY=false
export CURL_CA_BUNDLE=""
export REQUESTS_CA_BUNDLE=""

# 代理配置
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890

echo "🔧 SSL设置:"
echo "  PYTHONHTTPSVERIFY=0"
echo "  SSL_VERIFY=false"
echo ""

echo "🌐 代理设置:"
echo "  HTTP_PROXY=$HTTP_PROXY"
echo "  HTTPS_PROXY=$HTTPS_PROXY"
echo "  ALL_PROXY=$ALL_PROXY"
echo ""

# 检查Python SSL模块
echo "🔍 检查Python SSL支持..."
python3 -c "import ssl; print(f'SSL版本: {ssl.OPENSSL_VERSION}')" 2>/dev/null || echo "⚠️ SSL模块检查失败"

echo ""

# 尝试清理可能的SSL缓存
echo "🧹 清理SSL缓存..."
rm -rf ~/.cache/pip/selfcheck.json 2>/dev/null
rm -rf /tmp/pip-* 2>/dev/null

echo ""

echo "🚀 启动机器人..."
echo ""

# 启动机器人
python3 main.py

echo ""
echo "🔧 机器人已停止运行" 