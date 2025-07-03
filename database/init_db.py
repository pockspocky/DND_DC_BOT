"""
数据库初始化脚本
用于创建数据库结构和初始数据
"""
import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试相对导入，如果失败则使用绝对导入
try:
    from .database import db_manager
except ImportError:
    from database.database import db_manager

# 配置日志（仅在直接运行时）
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
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 连接数据库
        await db_manager.connect()
        
        # 初始化数据库结构
        await db_manager.initialize_database()
        
        # 插入初始数据
        await insert_initial_data()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        await db_manager.disconnect()

async def insert_initial_data():
    """插入初始数据"""
    logger.info("正在插入初始数据...")
    
    # 插入基础装备数据
    basic_equipment = [
        ("短剑", "武器", "简单近战武器", "common", "一把简单的短剑", 2.0, 1000, 0, "1d6", "piercing", "轻型,精准", False),
        ("长剑", "武器", "军用近战武器", "common", "一把标准的长剑", 3.0, 1500, 0, "1d8", "slashing", "多用途", False),
        ("皮甲", "防具", "轻甲", "common", "简单的皮质护甲", 10.0, 1000, 11, None, None, None, False),
        ("链甲", "防具", "重甲", "common", "金属链环编织的护甲", 20.0, 5000, 16, None, None, None, False),
        ("盾牌", "防具", "盾牌", "common", "木质盾牌", 6.0, 1000, 2, None, None, None, False),
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
            logger.warning(f"插入装备数据失败: {e}")
    
    # 插入基础法术数据
    basic_spells = [
        ("魔法飞弹", 1, "塑能", "1个动作", "120英尺", "V,S", "瞬间", "你创造三枚闪光的魔法飞弹。", "使用更高环位时，每高一环多一枚飞弹。", "法师,术士", "PHB"),
        ("治疗轻伤", 1, "塑能", "1个动作", "接触", "V,S", "瞬间", "你接触的生物恢复1d4+你的法术调整值点生命值。", "使用更高环位时，每高一环多恢复1d4点生命值。", "牧师,德鲁伊,圣武士,游侠", "PHB"),
        ("火球术", 3, "塑能", "1个动作", "150英尺", "V,S,M", "瞬间", "在你指定的范围内爆炸出一颗火球。", "使用更高环位时，每高一环多造成1d6点伤害。", "法师,术士", "PHB"),
        ("闪电束", 3, "塑能", "1个动作", "自身（100英尺线形）", "V,S,M", "瞬间", "一道闪电从你身前划过。", "使用更高环位时，每高一环多造成1d6点伤害。", "法师,术士", "PHB"),
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
            logger.warning(f"插入法术数据失败: {e}")
    
    # 插入基础怪物数据
    basic_monsters = [
        ("哥布林", "小型", "人型生物", "混乱邪恶", 15, 7, "2d6", "30英尺", 8, 14, 10, 10, 8, 8, None, "潜行+6", None, None, None, "黑暗视觉60英尺", "通用语,哥布林语", "1/4", 50, "灵巧脱逃", "弯刀攻击,短弓攻击", None, None, "MM"),
        ("兽人", "中型", "人型生物", "混乱邪恶", 13, 15, "2d8+2", "30英尺", 16, 12, 14, 7, 11, 10, None, "威吓+2", None, None, None, "黑暗视觉60英尺", "通用语,兽人语", "1/2", 100, "残暴", "巨斧攻击,标枪攻击", None, None, "MM"),
        ("巨狼", "大型", "野兽", "无阵营", 14, 37, "5d10+15", "50英尺", 17, 15, 15, 3, 12, 7, None, "察觉+3,潜行+4", None, None, None, "敏锐听觉和嗅觉", None, "1", 200, "扑击", "撕咬", None, None, "MM"),
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
            logger.warning(f"插入怪物数据失败: {e}")
    
    logger.info("初始数据插入完成")

if __name__ == "__main__":
    # 直接运行此脚本来初始化数据库
    asyncio.run(initialize_database()) 