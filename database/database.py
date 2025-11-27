"""
D&D Bot Database Manager
Simplified async database operation wrapper
"""
import asyncio
import aiosqlite
import logging
from typing import Optional, List, Dict
from .models import DatabaseModels

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Async database manager - handles all database operations"""
    
    def __init__(self, db_path: str = "dnd_bot.db"):
        """Initialize database manager"""
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Connect to database"""
        async with self._lock:
            if self.connection is None:
                self.connection = await aiosqlite.connect(self.db_path)
                self.connection.row_factory = aiosqlite.Row
                logger.info(f"Connected to database: {self.db_path}")
    
    async def disconnect(self) -> None:
        """Disconnect from database"""
        async with self._lock:
            if self.connection:
                await self.connection.close()
                self.connection = None
                logger.info("Disconnected from database")
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute SQL query"""
        if not self.connection:
            await self.connect()
        
        # Ensure connection exists
        if not self.connection:
            raise RuntimeError("Database connection failed")
        
        try:
            cursor = await self.connection.execute(query, params)
            await self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"SQL query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {params}")
            raise
    
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
        """
        Query single record
        
        Args:
            query: SQL query statement
            params: Query parameters
            
        Returns:
            Query result or None
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchone()
    
    async def fetchall(self, query: str, params: tuple = ()) -> List[aiosqlite.Row]:
        """
        Query all records
        
        Args:
            query: SQL query statement
            params: Query parameters
            
        Returns:
            List of query results
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchall()
    
    async def fetchmany(self, query: str, size: int, params: tuple = ()) -> List[aiosqlite.Row]:
        """
        Query specified number of records
        
        Args:
            query: SQL query statement
            size: Number of records
            params: Query parameters
            
        Returns:
            List of query results
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchmany(size)
    
    async def initialize_database(self) -> None:
        """Initialize database structure"""
        logger.info("Initializing database structure...")
        
        try:
            # Create all tables
            tables = DatabaseModels.get_create_tables_sql()
            for table_name, create_sql in tables.items():
                await self.execute(create_sql)
                logger.info(f"Created table: {table_name}")
            
            # Create indexes
            indexes = DatabaseModels.get_indexes_sql()
            for index_sql in indexes:
                await self.execute(index_sql)
            
            logger.info("Database structure initialization complete")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def check_database_health(self) -> bool:
        """Check database health status"""
        try:
            result = await self.fetchone("SELECT 1")
            return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # User-related operations
    async def create_or_update_user(self, discord_id: int, username: str, 
                                   discriminator: str = None, avatar_url: str = None) -> int:
        """
        Create or update user
        
        Args:
            discord_id: Discord user ID
            username: Username
            discriminator: User discriminator
            avatar_url: Avatar URL
            
        Returns:
            User database ID
        """
        # Check if user exists
        user = await self.fetchone(
            "SELECT id FROM users WHERE discord_id = ?", 
            (discord_id,)
        )
        
        if user:
            # Update existing user
            await self.execute(
                """UPDATE users 
                   SET username = ?, discriminator = ?, avatar_url = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE discord_id = ?""",
                (username, discriminator, avatar_url, discord_id)
            )
            return user['id']
        else:
            # Create new user
            cursor = await self.execute(
                """INSERT INTO users (discord_id, username, discriminator, avatar_url)
                   VALUES (?, ?, ?, ?)""",
                (discord_id, username, discriminator, avatar_url)
            )
            return cursor.lastrowid
    
    async def get_user_by_discord_id(self, discord_id: int) -> Optional[aiosqlite.Row]:
        """Get user by Discord ID"""
        return await self.fetchone(
            "SELECT * FROM users WHERE discord_id = ? AND is_active = TRUE",
            (discord_id,)
        )
    
    # Guild-related operations
    async def create_or_update_guild(self, discord_id: int, name: str) -> int:
        """
        Create or update guild
        
        Args:
            discord_id: Discord guild ID
            name: Guild name
            
        Returns:
            Guild database ID
        """
        # Check if guild exists
        guild = await self.fetchone(
            "SELECT id FROM guilds WHERE discord_id = ?", 
            (discord_id,)
        )
        
        if guild:
            # Update existing guild
            await self.execute(
                """UPDATE guilds 
                   SET name = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE discord_id = ?""",
                (name, discord_id)
            )
            return guild['id']
        else:
            # Create new guild
            cursor = await self.execute(
                """INSERT INTO guilds (discord_id, name)
                   VALUES (?, ?)""",
                (discord_id, name)
            )
            return cursor.lastrowid
    
    async def get_guild_by_discord_id(self, discord_id: int) -> Optional[aiosqlite.Row]:
        """Get guild by Discord ID"""
        return await self.fetchone(
            "SELECT * FROM guilds WHERE discord_id = ? AND is_active = TRUE",
            (discord_id,)
        )
    
    # Character-related operations
    async def create_character(self, user_id: int, guild_id: int, name: str, 
                              race: str, char_class: str, level: int = 1) -> int:
        """
        Create character
        
        Args:
            user_id: User database ID
            guild_id: Guild database ID
            name: Character name
            race: Race
            char_class: Class
            level: Level
            
        Returns:
            Character database ID
        """
        cursor = await self.execute(
            """INSERT INTO characters (user_id, guild_id, name, race, class, level)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, guild_id, name, race, char_class, level)
        )
        character_id = cursor.lastrowid
        
        # Create default stats
        await self.execute(
            """INSERT INTO character_stats (character_id) VALUES (?)""",
            (character_id,)
        )
        
        return character_id
    
    async def get_characters_by_user(self, user_id: int, guild_id: int) -> List[aiosqlite.Row]:
        """Get user's character list"""
        return await self.fetchall(
            """SELECT * FROM characters 
               WHERE user_id = ? AND guild_id = ? AND is_active = TRUE
               ORDER BY created_at DESC""",
            (user_id, guild_id)
        )
    
    # Dice history-related operations
    async def log_dice_roll(self, user_id: int, guild_id: int, channel_id: int,
                           dice_expression: str, result: int, details: str = None,
                           roll_type: str = 'normal', character_id: int = None) -> int:
        """
        Log dice roll history
        
        Args:
            user_id: User database ID
            guild_id: Guild database ID
            channel_id: Channel ID
            dice_expression: Dice expression
            result: Result
            details: Details
            roll_type: Roll type
            character_id: Character ID
            
        Returns:
            Record ID
        """
        cursor = await self.execute(
            """INSERT INTO dice_history 
               (user_id, guild_id, channel_id, dice_expression, result, details, roll_type, character_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, guild_id, channel_id, dice_expression, result, details, roll_type, character_id)
        )
        
        # Update user's total roll count
        await self.execute(
            """UPDATE users SET total_rolls = total_rolls + 1, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (user_id,)
        )
        
        return cursor.lastrowid
    
    # Utility methods
    async def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
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
        """Clean up old data"""
        cursor = await self.execute(
            """DELETE FROM dice_history 
               WHERE created_at < datetime('now', '-{} days')""".format(days)
        )
        
        return cursor.rowcount

# Global database manager instance
db_manager = DatabaseManager() 