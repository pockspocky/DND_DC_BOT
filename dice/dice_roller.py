"""
骰子滚动器
处理D&D骰子投掷的核心逻辑
"""
import logging
from typing import Optional, List, Dict, Any
from .dice_parser import DiceParser, DiceResult, DiceType
from database import db_manager

logger = logging.getLogger(__name__)

class DiceRoller:
    """骰子滚动器类"""
    
    def __init__(self):
        self.last_results: Dict[int, DiceResult] = {}  # 按用户ID存储最后结果
    
    async def roll_dice(self, expression: str, user_id: int, guild_id: int, 
                       channel_id: int, character_id: Optional[int] = None) -> Optional[DiceResult]:
        """
        投掷骰子
        
        Args:
            expression: 骰子表达式
            user_id: 用户ID
            guild_id: 服务器ID
            channel_id: 频道ID
            character_id: 角色ID（可选）
            
        Returns:
            骰子结果或None（如果解析失败）
        """
        # 解析骰子表达式
        dice_expr = DiceParser.parse(expression)
        if not dice_expr:
            return None
        
        # 执行投掷
        result = dice_expr.roll()
        
        # 保存到历史记录
        await self._save_to_history(result, user_id, guild_id, channel_id, character_id)
        
        # 缓存最后结果
        self.last_results[user_id] = result
        
        return result
    
    async def roll_advantage(self, modifier: int = 0, user_id: int = 0, 
                           guild_id: int = 0, channel_id: int = 0) -> DiceResult:
        """投掷优势骰（2d20取较高）"""
        expression = f"adv{'+' + str(modifier) if modifier > 0 else ('-' + str(abs(modifier)) if modifier < 0 else '')}"
        dice_expr = DiceParser.parse("adv")
        if dice_expr:
            dice_expr.modifier = modifier
            result = dice_expr.roll()
            await self._save_to_history(result, user_id, guild_id, channel_id, roll_type="advantage")
            return result
        return DiceResult("adv", modifier, [], modifier, DiceType.ADVANTAGE)
    
    async def roll_disadvantage(self, modifier: int = 0, user_id: int = 0,
                              guild_id: int = 0, channel_id: int = 0) -> DiceResult:
        """投掷劣势骰（2d20取较低）"""
        expression = f"dis{'+' + str(modifier) if modifier > 0 else ('-' + str(abs(modifier)) if modifier < 0 else '')}"
        dice_expr = DiceParser.parse("dis")
        if dice_expr:
            dice_expr.modifier = modifier
            result = dice_expr.roll()
            await self._save_to_history(result, user_id, guild_id, channel_id, roll_type="disadvantage")
            return result
        return DiceResult("dis", modifier, [], modifier, DiceType.DISADVANTAGE)
    
    def roll_ability_scores(self) -> List[DiceResult]:
        """生成D&D角色的6个属性值（4d6去最低）"""
        results = []
        for i in range(6):
            dice_expr = DiceParser.parse("4d6dl1")
            if dice_expr:
                result = dice_expr.roll()
                results.append(result)
        return results
    
    async def roll_skill_check(self, skill_modifier: int, user_id: int, 
                             guild_id: int, channel_id: int, 
                             advantage: bool = False, disadvantage: bool = False) -> DiceResult:
        """
        技能检定
        
        Args:
            skill_modifier: 技能修正值
            advantage: 是否有优势
            disadvantage: 是否有劣势
        """
        if advantage and disadvantage:
            # 优势和劣势抵消，正常投掷
            advantage = disadvantage = False
        
        if advantage:
            return await self.roll_advantage(skill_modifier, user_id, guild_id, channel_id)
        elif disadvantage:
            return await self.roll_disadvantage(skill_modifier, user_id, guild_id, channel_id)
        else:
            # 正常投掷
            expression = f"1d20{'+' + str(skill_modifier) if skill_modifier > 0 else ('-' + str(abs(skill_modifier)) if skill_modifier < 0 else '')}"
            result = await self.roll_dice(expression, user_id, guild_id, channel_id)
            if result:
                return result
            # fallback if parsing fails
            return DiceResult("1d20", 1 + skill_modifier, [], skill_modifier, DiceType.NORMAL)
    
    async def roll_attack(self, attack_bonus: int, damage_dice: str,
                         user_id: int, guild_id: int, channel_id: int,
                         advantage: bool = False, disadvantage: bool = False) -> Dict[str, DiceResult]:
        """
        攻击检定 + 伤害投掷
        
        Args:
            attack_bonus: 攻击加值
            damage_dice: 伤害骰子表达式
            advantage: 攻击是否有优势
            disadvantage: 攻击是否有劣势
            
        Returns:
            包含'attack'和'damage'的结果字典
        """
        results = {}
        
        # 攻击检定
        attack_expr = f"1d20{'+' + str(attack_bonus) if attack_bonus > 0 else ('-' + str(abs(attack_bonus)) if attack_bonus < 0 else '')}"
        if advantage:
            results['attack'] = await self.roll_advantage(attack_bonus, user_id, guild_id, channel_id)
        elif disadvantage:
            results['attack'] = await self.roll_disadvantage(attack_bonus, user_id, guild_id, channel_id)
        else:
            results['attack'] = await self.roll_dice(attack_expr, user_id, guild_id, channel_id)
        
        # 伤害投掷
        damage_result = await self.roll_dice(damage_dice, user_id, guild_id, channel_id)
        if damage_result:
            results['damage'] = damage_result
        
        return results
    
    async def roll_saving_throw(self, save_modifier: int, user_id: int,
                               guild_id: int, channel_id: int,
                               advantage: bool = False, disadvantage: bool = False) -> DiceResult:
        """
        豁免检定
        
        Args:
            save_modifier: 豁免修正值
            advantage: 是否有优势
            disadvantage: 是否有劣势
        """
        return await self.roll_skill_check(save_modifier, user_id, guild_id, channel_id, advantage, disadvantage)
    
    def get_last_result(self, user_id: int) -> Optional[DiceResult]:
        """获取用户最后一次投掷结果"""
        return self.last_results.get(user_id)
    
    async def _save_to_history(self, result: DiceResult, user_id: int, 
                             guild_id: int, channel_id: int, 
                             character_id: Optional[int] = None,
                             roll_type: str = "normal") -> None:
        """保存投掷历史到数据库"""
        try:
            # 获取数据库中的用户ID和服务器ID
            db_user = await db_manager.get_user_by_discord_id(user_id)
            db_guild = await db_manager.get_guild_by_discord_id(guild_id)
            
            if not db_user or not db_guild:
                logger.warning(f"无法找到用户或服务器记录: user={user_id}, guild={guild_id}")
                return
            
            # 构建详细信息
            details = {
                "rolls": [{"value": roll.value, "kept": roll.kept} for roll in result.rolls],
                "modifier": result.modifier,
                "dice_type": result.dice_type.value,
                "details": result.details
            }
            
            # 只有当character_id不为None时才传递
            if character_id is not None:
                await db_manager.log_dice_roll(
                    user_id=db_user['id'],
                    guild_id=db_guild['id'],
                    channel_id=channel_id,
                    dice_expression=result.expression,
                    result=result.total,
                    details=str(details),
                    roll_type=roll_type,
                    character_id=character_id
                )
            else:
                await db_manager.log_dice_roll(
                    user_id=db_user['id'],
                    guild_id=db_guild['id'],
                    channel_id=channel_id,
                    dice_expression=result.expression,
                    result=result.total,
                    details=str(details),
                    roll_type=roll_type
                )
            
        except Exception as e:
            logger.error(f"保存骰子历史失败: {e}")
    
    @staticmethod
    def format_dice_result_embed(result: DiceResult, user_name: str) -> Dict[str, Any]:
        """格式化骰子结果为Discord嵌入消息格式"""
        # 确定颜色
        color = 0x00ff00  # 绿色默认
        if result.dice_type == DiceType.ADVANTAGE:
            color = 0x0099ff  # 蓝色
        elif result.dice_type == DiceType.DISADVANTAGE:
            color = 0xff9900  # 橙色
        elif any(roll.is_max for roll in result.rolls if roll.kept):
            color = 0xffd700  # 金色（大成功）
        elif any(roll.is_min for roll in result.rolls if roll.kept):
            color = 0xff0000  # 红色（大失败）
        
        # 构建嵌入消息
        embed_data = {
            "title": f"🎲 {user_name} 的骰子投掷",
            "color": color,
            "fields": [
                {
                    "name": "表达式",
                    "value": f"`{result.expression}`",
                    "inline": True
                },
                {
                    "name": "结果",
                    "value": f"**{result.total}**",
                    "inline": True
                }
            ]
        }
        
        # 添加详细结果
        if result.rolls:
            roll_details = result.format_result()
            embed_data["fields"].append({
                "name": "详细结果",
                "value": roll_details,
                "inline": False
            })
        
        # 添加额外信息
        if result.details:
            embed_data["fields"].append({
                "name": "说明",
                "value": result.details,
                "inline": False
            })
        
        return embed_data

# 全局骰子滚动器实例
dice_roller = DiceRoller() 