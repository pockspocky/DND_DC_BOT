"""
Database Model Definitions
Contains all table structures needed for the D&D bot
"""
import asyncio
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

class DatabaseModels:
    """Database model class, defines all table structures"""
    
    @staticmethod
    def get_create_tables_sql() -> Dict[str, str]:
        """Get SQL statements for creating all tables"""
        
        return {
            # Users table
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    discord_id INTEGER UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    discriminator TEXT,
                    avatar_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    total_rolls INTEGER DEFAULT 0,
                    total_characters INTEGER DEFAULT 0
                )
            """,
            
            # Guild configuration table
            "guilds": """
                CREATE TABLE IF NOT EXISTS guilds (
                    id INTEGER PRIMARY KEY,
                    discord_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    prefix TEXT DEFAULT '!',
                    language TEXT DEFAULT 'zh-CN',
                    timezone TEXT DEFAULT 'UTC+8',
                    dice_channel_id INTEGER,
                    combat_channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """,
            
            # Characters table
            "characters": """
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    race TEXT NOT NULL,
                    class TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    background TEXT,
                    alignment TEXT,
                    experience INTEGER DEFAULT 0,
                    max_hp INTEGER DEFAULT 10,
                    current_hp INTEGER DEFAULT 10,
                    temp_hp INTEGER DEFAULT 0,
                    armor_class INTEGER DEFAULT 10,
                    proficiency_bonus INTEGER DEFAULT 2,
                    speed INTEGER DEFAULT 30,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(id)
                )
            """,
            
            # Character stats table
            "character_stats": """
                CREATE TABLE IF NOT EXISTS character_stats (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    strength INTEGER DEFAULT 10,
                    dexterity INTEGER DEFAULT 10,
                    constitution INTEGER DEFAULT 10,
                    intelligence INTEGER DEFAULT 10,
                    wisdom INTEGER DEFAULT 10,
                    charisma INTEGER DEFAULT 10,
                    str_modifier INTEGER DEFAULT 0,
                    dex_modifier INTEGER DEFAULT 0,
                    con_modifier INTEGER DEFAULT 0,
                    int_modifier INTEGER DEFAULT 0,
                    wis_modifier INTEGER DEFAULT 0,
                    cha_modifier INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """,
            
            # Character skills table
            "character_skills": """
                CREATE TABLE IF NOT EXISTS character_skills (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    skill_name TEXT NOT NULL,
                    proficient BOOLEAN DEFAULT FALSE,
                    expertise BOOLEAN DEFAULT FALSE,
                    bonus_modifier INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """,
            
            # Equipment table
            "equipment": """
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    subtype TEXT,
                    rarity TEXT DEFAULT 'common',
                    description TEXT,
                    weight REAL DEFAULT 0,
                    cost_cp INTEGER DEFAULT 0,
                    ac_bonus INTEGER DEFAULT 0,
                    damage_dice TEXT,
                    damage_type TEXT,
                    properties TEXT,
                    requires_attunement BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            # Character equipment relationship table
            "character_equipment": """
                CREATE TABLE IF NOT EXISTS character_equipment (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER NOT NULL,
                    equipment_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    equipped BOOLEAN DEFAULT FALSE,
                    attuned BOOLEAN DEFAULT FALSE,
                    custom_properties TEXT,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters(id),
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
                )
            """,
            
            # Combat sessions table
            "combat_sessions": """
                CREATE TABLE IF NOT EXISTS combat_sessions (
                    id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    dm_user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    current_turn INTEGER DEFAULT 0,
                    current_round INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id),
                    FOREIGN KEY (dm_user_id) REFERENCES users(id)
                )
            """,
            
            # Combat participants table
            "combat_participants": """
                CREATE TABLE IF NOT EXISTS combat_participants (
                    id INTEGER PRIMARY KEY,
                    combat_session_id INTEGER NOT NULL,
                    character_id INTEGER,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    initiative INTEGER NOT NULL,
                    current_hp INTEGER NOT NULL,
                    max_hp INTEGER NOT NULL,
                    armor_class INTEGER DEFAULT 10,
                    is_npc BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    position_in_turn INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (combat_session_id) REFERENCES combat_sessions(id),
                    FOREIGN KEY (character_id) REFERENCES characters(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """,
            
            # Status effects table
            "status_effects": """
                CREATE TABLE IF NOT EXISTS status_effects (
                    id INTEGER PRIMARY KEY,
                    participant_id INTEGER NOT NULL,
                    effect_name TEXT NOT NULL,
                    effect_description TEXT,
                    duration INTEGER DEFAULT -1,
                    remaining_duration INTEGER DEFAULT -1,
                    effect_type TEXT DEFAULT 'buff',
                    created_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (participant_id) REFERENCES combat_participants(id),
                    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
                )
            """,
            
            # Dice history table
            "dice_history": """
                CREATE TABLE IF NOT EXISTS dice_history (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    dice_expression TEXT NOT NULL,
                    result INTEGER NOT NULL,
                    details TEXT,
                    roll_type TEXT DEFAULT 'normal',
                    character_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(id),
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """,
            
            # Spells data table
            "spells": """
                CREATE TABLE IF NOT EXISTS spells (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    school TEXT NOT NULL,
                    casting_time TEXT NOT NULL,
                    range TEXT NOT NULL,
                    components TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    description TEXT NOT NULL,
                    at_higher_levels TEXT,
                    classes TEXT NOT NULL,
                    source TEXT DEFAULT 'PHB',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            # Monsters data table
            "monsters": """
                CREATE TABLE IF NOT EXISTS monsters (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    size TEXT NOT NULL,
                    type TEXT NOT NULL,
                    alignment TEXT NOT NULL,
                    armor_class INTEGER NOT NULL,
                    hit_points INTEGER NOT NULL,
                    hit_dice TEXT NOT NULL,
                    speed TEXT NOT NULL,
                    strength INTEGER NOT NULL,
                    dexterity INTEGER NOT NULL,
                    constitution INTEGER NOT NULL,
                    intelligence INTEGER NOT NULL,
                    wisdom INTEGER NOT NULL,
                    charisma INTEGER NOT NULL,
                    saving_throws TEXT,
                    skills TEXT,
                    damage_resistances TEXT,
                    damage_immunities TEXT,
                    condition_immunities TEXT,
                    senses TEXT,
                    languages TEXT,
                    challenge_rating TEXT NOT NULL,
                    experience_points INTEGER NOT NULL,
                    abilities TEXT,
                    actions TEXT,
                    legendary_actions TEXT,
                    lair_actions TEXT,
                    source TEXT DEFAULT 'MM',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            # Items data table
            "items": """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    subtype TEXT,
                    rarity TEXT DEFAULT 'common',
                    description TEXT NOT NULL,
                    weight REAL DEFAULT 0,
                    cost_cp INTEGER DEFAULT 0,
                    properties TEXT,
                    requires_attunement BOOLEAN DEFAULT FALSE,
                    source TEXT DEFAULT 'PHB',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            # Combat logs table
            "combat_logs": """
                CREATE TABLE IF NOT EXISTS combat_logs (
                    id INTEGER PRIMARY KEY,
                    combat_session_id INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    turn_order INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    actor_name TEXT NOT NULL,
                    target_name TEXT,
                    action_description TEXT NOT NULL,
                    dice_expression TEXT,
                    dice_result TEXT,
                    damage_dealt INTEGER DEFAULT 0,
                    healing_dealt INTEGER DEFAULT 0,
                    hp_before INTEGER,
                    hp_after INTEGER,
                    is_critical BOOLEAN DEFAULT FALSE,
                    is_death BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (combat_session_id) REFERENCES combat_sessions(id)
                )
            """,
            
            # User achievements table
            "achievements": """
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    achievement_name TEXT NOT NULL,
                    achievement_description TEXT,
                    progress INTEGER DEFAULT 0,
                    target INTEGER DEFAULT 1,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
        }
    
    @staticmethod
    def get_indexes_sql() -> List[str]:
        """Get SQL statements for all indexes"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id)",
            "CREATE INDEX IF NOT EXISTS idx_guilds_discord_id ON guilds(discord_id)",
            "CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_characters_guild_id ON characters(guild_id)",
            "CREATE INDEX IF NOT EXISTS idx_character_stats_character_id ON character_stats(character_id)",
            "CREATE INDEX IF NOT EXISTS idx_character_skills_character_id ON character_skills(character_id)",
            "CREATE INDEX IF NOT EXISTS idx_character_equipment_character_id ON character_equipment(character_id)",
            "CREATE INDEX IF NOT EXISTS idx_combat_sessions_guild_id ON combat_sessions(guild_id)",
            "CREATE INDEX IF NOT EXISTS idx_combat_participants_session_id ON combat_participants(combat_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_status_effects_participant_id ON status_effects(participant_id)",
            "CREATE INDEX IF NOT EXISTS idx_combat_logs_session_id ON combat_logs(combat_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_combat_logs_round ON combat_logs(round_number)",
            "CREATE INDEX IF NOT EXISTS idx_dice_history_user_id ON dice_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_dice_history_guild_id ON dice_history(guild_id)",
            "CREATE INDEX IF NOT EXISTS idx_spells_name ON spells(name)",
            "CREATE INDEX IF NOT EXISTS idx_spells_level ON spells(level)",
            "CREATE INDEX IF NOT EXISTS idx_monsters_name ON monsters(name)",
            "CREATE INDEX IF NOT EXISTS idx_monsters_cr ON monsters(challenge_rating)",
            "CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)",
            "CREATE INDEX IF NOT EXISTS idx_items_type ON items(type)",
            "CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)"
        ] 