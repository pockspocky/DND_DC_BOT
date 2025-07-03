#!/usr/bin/env python3
"""
数据库管理工具
提供数据库的初始化、清理、备份等功能
"""
import asyncio
import logging
import sys
import os
import shutil
from datetime import datetime
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

class DatabaseTools:
    """数据库工具类"""
    
    def __init__(self, db_path: str = "dnd_bot.db"):
        self.db_path = db_path
    
    async def initialize_database(self):
        """初始化数据库"""
        try:
            from database.init_db import initialize_database
            await initialize_database()
            print("✅ 数据库初始化完成")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            raise
    
    def backup_database(self):
        """备份数据库"""
        if not os.path.exists(self.db_path):
            print("❌ 数据库文件不存在")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_{timestamp}_{self.db_path}"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ 数据库备份完成: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ 数据库备份失败: {e}")
            return False
    
    def remove_database(self):
        """删除数据库"""
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                print("✅ 数据库文件已删除")
                return True
            except Exception as e:
                print(f"❌ 删除数据库失败: {e}")
                return False
        else:
            print("ℹ️  数据库文件不存在")
            return True
    
    def database_info(self):
        """显示数据库信息"""
        if os.path.exists(self.db_path):
            stat = os.stat(self.db_path)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"📊 数据库信息:")
            print(f"   文件路径: {self.db_path}")
            print(f"   文件大小: {size:,} 字节")
            print(f"   修改时间: {modified}")
        else:
            print("❌ 数据库文件不存在")
    
    async def get_stats(self):
        """获取数据库统计信息"""
        try:
            from database import db_manager
            await db_manager.connect()
            stats = await db_manager.get_database_stats()
            
            print("📈 数据库统计:")
            print(f"   用户数: {stats.get('users', 0)}")
            print(f"   角色数: {stats.get('characters', 0)}")
            print(f"   服务器数: {stats.get('guilds', 0)}")
            print(f"   投掷记录: {stats.get('dice_history', 0)}")
            print(f"   法术数: {stats.get('spells', 0)}")
            print(f"   怪物数: {stats.get('monsters', 0)}")
            print(f"   装备数: {stats.get('equipment', 0)}")
            
            await db_manager.disconnect()
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")

async def main():
    """主函数"""
    tools = DatabaseTools()
    
    print("🔧 D&D Discord Bot 数据库管理工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 初始化数据库")
        print("2. 备份数据库") 
        print("3. 删除数据库")
        print("4. 显示数据库信息")
        print("5. 显示数据库统计")
        print("6. 退出")
        
        try:
            choice = input("\n请输入选择 (1-6): ").strip()
            
            if choice == '1':
                print("\n正在初始化数据库...")
                await tools.initialize_database()
                
            elif choice == '2':
                print("\n正在备份数据库...")
                tools.backup_database()
                
            elif choice == '3':
                confirm = input("⚠️  确定要删除数据库吗? (y/N): ").strip().lower()
                if confirm == 'y':
                    tools.remove_database()
                else:
                    print("取消删除")
                    
            elif choice == '4':
                tools.database_info()
                
            elif choice == '5':
                print("\n正在获取统计信息...")
                await tools.get_stats()
                
            elif choice == '6':
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效的选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 