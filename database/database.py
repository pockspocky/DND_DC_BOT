"""
数据库管理器
处理数据库连接、初始化和基本操作
"""
import os
import asyncio
import aiosqlite
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from .models import DatabaseModels

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_path: str = "dnd_bot.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """连接到数据库"""
        async with self._lock:
            if self.connection is None:
                self.connection = await aiosqlite.connect(self.db_path)
                self.connection.row_factory = aiosqlite.Row
                logger.info(f"已连接到数据库: {self.db_path}")
    
    async def disconnect(self) -> None:
        """断开数据库连接"""
        async with self._lock:
            if self.connection:
                await self.connection.close()
                self.connection = None
                logger.info("已断开数据库连接")
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果游标
        """
        if not self.connection:
            await self.connect()
        
        try:
            cursor = await self.connection.execute(query, params)
            await self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"执行SQL查询失败: {e}")
            logger.error(f"查询语句: {query}")
            logger.error(f"参数: {params}")
            raise
    
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
        """
        查询单条记录
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果或None
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchone()
    
    async def fetchall(self, query: str, params: tuple = ()) -> List[aiosqlite.Row]:
        """
        查询所有记录
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchall()
    
    async def fetchmany(self, query: str, size: int, params: tuple = ()) -> List[aiosqlite.Row]:
        """
        查询指定数量的记录
        
        Args:
            query: SQL查询语句
            size: 记录数量
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchmany(size)
    
    async def initialize_database(self) -> None:
        """初始化数据库结构"""
        logger.info("正在初始化数据库结构...")
        
        try:
            # 创建所有表
            tables = DatabaseModels.get_create_tables_sql()
            for table_name, create_sql in tables.items():
                await self.execute(create_sql)
                logger.info(f"已创建表: {table_name}")
            
            # 创建索引
            indexes = DatabaseModels.get_indexes_sql()
            for index_sql in indexes:
                await self.execute(index_sql)
            
            logger.info("数据库结构初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def check_database_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            result = await self.fetchone("SELECT 1")
            return result is not None
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False
    
    # 用户相关操作
    async def create_or_update_user(self, discord_id: int, username: str, 
                                   discriminator: str = None, avatar_url: str = None) -> int:
        """
        创建或更新用户
        
        Args:
            discord_id: Discord用户ID
            username: 用户名
            discriminator: 用户标识符
            avatar_url: 头像URL
            
        Returns:
            用户数据库ID
        """
        # 检查用户是否存在
        user = await self.fetchone(
            "SELECT id FROM users WHERE discord_id = ?", 
            (discord_id,)
        )
        
        if user:
            # 更新现有用户
            await self.execute(
                """UPDATE users 
                   SET username = ?, discriminator = ?, avatar_url = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE discord_id = ?""",
                (username, discriminator, avatar_url, discord_id)
            )
            return user['id']
        else:
            # 创建新用户
            cursor = await self.execute(
                """INSERT INTO users (discord_id, username, discriminator, avatar_url)
                   VALUES (?, ?, ?, ?)""",
                (discord_id, username, discriminator, avatar_url)
            )
            return cursor.lastrowid
    
    async def get_user_by_discord_id(self, discord_id: int) -> Optional[aiosqlite.Row]:
        """根据Discord ID获取用户"""
        return await self.fetchone(
            "SELECT * FROM users WHERE discord_id = ? AND is_active = TRUE",
            (discord_id,)
        )
    
    # 服务器相关操作
    async def create_or_update_guild(self, discord_id: int, name: str) -> int:
        """
        创建或更新服务器
        
        Args:
            discord_id: Discord服务器ID
            name: 服务器名称
            
        Returns:
            服务器数据库ID
        """
        # 检查服务器是否存在
        guild = await self.fetchone(
            "SELECT id FROM guilds WHERE discord_id = ?", 
            (discord_id,)
        )
        
        if guild:
            # 更新现有服务器
            await self.execute(
                """UPDATE guilds 
                   SET name = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE discord_id = ?""",
                (name, discord_id)
            )
            return guild['id']
        else:
            # 创建新服务器
            cursor = await self.execute(
                """INSERT INTO guilds (discord_id, name)
                   VALUES (?, ?)""",
                (discord_id, name)
            )
            return cursor.lastrowid
    
    async def get_guild_by_discord_id(self, discord_id: int) -> Optional[aiosqlite.Row]:
        """根据Discord ID获取服务器"""
        return await self.fetchone(
            "SELECT * FROM guilds WHERE discord_id = ? AND is_active = TRUE",
            (discord_id,)
        )
    
    # 角色相关操作
    async def create_character(self, user_id: int, guild_id: int, name: str, 
                              race: str, char_class: str, level: int = 1) -> int:
        """
        创建角色
        
        Args:
            user_id: 用户数据库ID
            guild_id: 服务器数据库ID
            name: 角色名称
            race: 种族
            char_class: 职业
            level: 等级
            
        Returns:
            角色数据库ID
        """
        cursor = await self.execute(
            """INSERT INTO characters (user_id, guild_id, name, race, class, level)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, guild_id, name, race, char_class, level)
        )
        character_id = cursor.lastrowid
        
        # 创建默认属性
        await self.execute(
            """INSERT INTO character_stats (character_id) VALUES (?)""",
            (character_id,)
        )
        
        return character_id
    
    async def get_characters_by_user(self, user_id: int, guild_id: int) -> List[aiosqlite.Row]:
        """获取用户的角色列表"""
        return await self.fetchall(
            """SELECT * FROM characters 
               WHERE user_id = ? AND guild_id = ? AND is_active = TRUE
               ORDER BY created_at DESC""",
            (user_id, guild_id)
        )
    
    # 骰子历史相关操作
    async def log_dice_roll(self, user_id: int, guild_id: int, channel_id: int,
                           dice_expression: str, result: int, details: str = None,
                           roll_type: str = 'normal', character_id: int = None) -> int:
        """
        记录骰子投掷历史
        
        Args:
            user_id: 用户数据库ID
            guild_id: 服务器数据库ID
            channel_id: 频道ID
            dice_expression: 骰子表达式
            result: 结果
            details: 详细信息
            roll_type: 投掷类型
            character_id: 角色ID
            
        Returns:
            记录ID
        """
        cursor = await self.execute(
            """INSERT INTO dice_history 
               (user_id, guild_id, channel_id, dice_expression, result, details, roll_type, character_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, guild_id, channel_id, dice_expression, result, details, roll_type, character_id)
        )
        
        # 更新用户总投掷次数
        await self.execute(
            """UPDATE users SET total_rolls = total_rolls + 1, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (user_id,)
        )
        
        return cursor.lastrowid
    
    # 实用工具方法
    async def get_database_stats(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        stats = {}
        
        tables = [
            'users', 'guilds', 'characters', 'character_stats', 'character_skills',
            'equipment', 'character_equipment', 'combat_sessions', 'combat_participants',
            'status_effects', 'dice_history', 'spells', 'monsters', 'items', 'achievements'
        ]
        
        for table in tables:
            result = await self.fetchone(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = result['count'] if result else 0
        
        return stats
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """清理旧数据"""
        cursor = await self.execute(
            """DELETE FROM dice_history 
               WHERE created_at < datetime('now', '-{} days')""".format(days)
        )
        
        return cursor.rowcount

# 全局数据库管理器实例
db_manager = DatabaseManager() 