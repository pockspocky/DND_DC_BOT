"""
Database Initialization Script
Used to create database structure and initial data
"""
import asyncio
import logging
import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try relative import, fall back to absolute import if it fails
try:
    from .database import db_manager
except ImportError:
    from database.database import db_manager

# Configure logging (only when run directly)
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize database"""
    try:
        logger.info("Starting database initialization...")
        
        # Connect to database
        await db_manager.connect()
        
        # Initialize database structure
        await db_manager.initialize_database()
        
        # Insert initial data
        await insert_initial_data()
        
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        await db_manager.disconnect()

async def insert_initial_data():
    """Insert initial data"""
    logger.info("Inserting initial data...")
    
    # Insert basic equipment data
    basic_equipment = [
        ("Shortsword", "Weapon", "Simple Melee Weapon", "common", "A simple shortsword", 2.0, 1000, 0, "1d6", "piercing", "Light, Finesse", False),
        ("Longsword", "Weapon", "Martial Melee Weapon", "common", "A standard longsword", 3.0, 1500, 0, "1d8", "slashing", "Versatile", False),
        ("Leather Armor", "Armor", "Light Armor", "common", "Simple leather armor", 10.0, 1000, 11, None, None, None, False),
        ("Chain Mail", "Armor", "Heavy Armor", "common", "Armor made of interlocking metal rings", 20.0, 5000, 16, None, None, None, False),
        ("Shield", "Armor", "Shield", "common", "Wooden shield", 6.0, 1000, 2, None, None, None, False),
    ]
    
    for equipment in basic_equipment:
        try:
            await db_manager.execute(
                """INSERT OR IGNORE INTO equipment 
                   (name, type, subtype, rarity, description, weight, cost_cp, ac_bonus, damage_dice, damage_type, properties, requires_attunement)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                equipment
            )
        except Exception as e:
            logger.warning(f"Failed to insert equipment data: {e}")
    
    # Insert basic spell data
    basic_spells = [
        ("Magic Missile", 1, "Evocation", "1 action", "120 feet", "V,S", "Instantaneous", "You create three glowing darts of magical force.", "When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st.", "Wizard, Sorcerer", "PHB"),
        ("Cure Wounds", 1, "Evocation", "1 action", "Touch", "V,S", "Instantaneous", "A creature you touch regains a number of hit points equal to 1d4 + your spellcasting ability modifier.", "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d4 for each slot level above 1st.", "Cleric, Druid, Paladin, Ranger", "PHB"),
        ("Fireball", 3, "Evocation", "1 action", "150 feet", "V,S,M", "Instantaneous", "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame.", "When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd.", "Wizard, Sorcerer", "PHB"),
        ("Lightning Bolt", 3, "Evocation", "1 action", "Self (100-foot line)", "V,S,M", "Instantaneous", "A stroke of lightning forming a line 100 feet long and 5 feet wide blasts out from you in a direction you choose.", "When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd.", "Wizard, Sorcerer", "PHB"),
    ]
    
    for spell in basic_spells:
        try:
            await db_manager.execute(
                """INSERT OR IGNORE INTO spells 
                   (name, level, school, casting_time, range, components, duration, description, at_higher_levels, classes, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                spell
            )
        except Exception as e:
            logger.warning(f"Failed to insert spell data: {e}")
    
    # Insert basic monster data
    basic_monsters = [
        ("Goblin", "Small", "Humanoid", "Chaotic Evil", 15, 7, "2d6", "30 ft.", 8, 14, 10, 10, 8, 8, None, "Stealth +6", None, None, None, "Darkvision 60 ft.", "Common, Goblin", "1/4", 50, "Nimble Escape", "Scimitar, Shortbow", None, None, "MM"),
        ("Orc", "Medium", "Humanoid", "Chaotic Evil", 13, 15, "2d8+2", "30 ft.", 16, 12, 14, 7, 11, 10, None, "Intimidation +2", None, None, None, "Darkvision 60 ft.", "Common, Orc", "1/2", 100, "Aggressive", "Greataxe, Javelin", None, None, "MM"),
        ("Dire Wolf", "Large", "Beast", "Unaligned", 14, 37, "5d10+15", "50 ft.", 17, 15, 15, 3, 12, 7, None, "Perception +3, Stealth +4", None, None, None, "Keen Hearing and Smell", None, "1", 200, "Pack Tactics", "Bite", None, None, "MM"),
    ]
    
    for monster in basic_monsters:
        try:
            await db_manager.execute(
                """INSERT OR IGNORE INTO monsters 
                   (name, size, type, alignment, armor_class, hit_points, hit_dice, speed, 
                    strength, dexterity, constitution, intelligence, wisdom, charisma,
                    saving_throws, skills, damage_resistances, damage_immunities, condition_immunities,
                    senses, languages, challenge_rating, experience_points, abilities, actions, legendary_actions, lair_actions, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                monster
            )
        except Exception as e:
            logger.warning(f"Failed to insert monster data: {e}")
    
    logger.info("Initial data insertion complete")

if __name__ == "__main__":
    # Run this script directly to initialize the database
    asyncio.run(initialize_database()) 