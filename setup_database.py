#!/usr/bin/env python3
"""
数据库设置脚本
用于初始化D&D机器人的数据库
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    print("=" * 50)
    print("🎲 D&D Discord Bot 数据库设置")
    print("=" * 50)
    
    try:
        # 导入数据库管理器
        from database.init_db import initialize_database
        
        # 初始化数据库
        await initialize_database()
        
        print("\n✅ 数据库初始化完成！")
        print("📁 数据库文件位置: dnd_bot.db")
        print("🚀 现在可以运行 'python main.py' 启动机器人")
        
    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("正在初始化数据库...")
    asyncio.run(main()) 