#!/usr/bin/env python3
"""
网络连接检查脚本
快速诊断Discord连接状态
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

def check_proxy_port():
    """检查代理端口是否被占用"""
    try:
        result = subprocess.run(['lsof', '-i', ':7890'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_discord_connection():
    """检查Discord连接"""
    proxy_url = os.getenv('PROXY_URL', 'http://127.0.0.1:7890')
    
    try:
        result = subprocess.run([
            'curl', '-s', '--connect-timeout', '10',
            '--proxy', proxy_url,
            'https://discord.com/api/v10/gateway'
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except:
        return False

def main():
    """主检查函数"""
    load_dotenv()
    
    print("🔍 Discord连接检查...\n")
    
    # 检查代理端口
    proxy_running = check_proxy_port()
    print(f"代理端口7890: {'✅ 运行中' if proxy_running else '❌ 未使用'}")
    
    if not proxy_running:
        print("⚠️  请启动代理软件（如ClashX）")
        return
    
    # 检查Discord连接
    discord_ok = check_discord_connection()
    print(f"Discord连接: {'✅ 正常' if discord_ok else '❌ 失败'}")
    
    if discord_ok:
        print("\n🎉 连接检查通过！可以启动机器人：")
        print("   ./start_bot_with_proxy.sh")
    else:
        print("\n❌ 连接检查失败！请检查：")
        print("1. 代理软件是否正常运行")
        print("2. 代理设置是否正确")
        print("3. 网络连接是否正常")

if __name__ == "__main__":
    main() 