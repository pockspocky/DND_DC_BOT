"""
骰子表达式解析器
解析和验证各种D&D骰子表达式
"""
import re
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
from enum import Enum

class DiceType(Enum):
    """骰子类型枚举"""
    NORMAL = "normal"
    ADVANTAGE = "advantage" 
    DISADVANTAGE = "disadvantage"
    CRITICAL = "critical"

@dataclass
class DiceRoll:
    """单次骰子投掷结果"""
    value: int
    dice_size: int
    is_max: bool = False
    is_min: bool = False
    kept: bool = True
    
    def __str__(self):
        if not self.kept:
            return f"~~{self.value}~~"
        elif self.is_max:
            return f"**{self.value}**"
        elif self.is_min:
            return f"*{self.value}*"
        else:
            return str(self.value)

@dataclass
class DiceResult:
    """骰子投掷完整结果"""
    expression: str
    total: int
    rolls: List[DiceRoll]
    modifier: int = 0
    dice_type: DiceType = DiceType.NORMAL
    details: str = ""
    
    def format_result(self) -> str:
        """格式化显示结果"""
        if not self.rolls:
            return f"{self.expression} = {self.total}"
        
        # 格式化骰子结果
        roll_strs = [str(roll) for roll in self.rolls]
        rolls_display = f"[{', '.join(roll_strs)}]"
        
        # 构建完整表达式
        if self.modifier != 0:
            modifier_str = f" {'+' if self.modifier > 0 else ''}{self.modifier}"
            expression = f"{rolls_display}{modifier_str}"
        else:
            expression = rolls_display
            
        return f"{self.expression} = {expression} = **{self.total}**"

class DiceParser:
    """骰子表达式解析器"""
    
    # 骰子表达式正则模式
    DICE_PATTERN = re.compile(
        r'^(?P<count>\d+)?d(?P<size>\d+)(?P<modifiers>[kldh\+\-\d\s]*)?$',
        re.IGNORECASE
    )
    
    # 修正值模式
    MODIFIER_PATTERN = re.compile(r'([+\-])(\d+)')
    
    # 保留/丢弃模式
    KEEP_DROP_PATTERN = re.compile(r'([kd])([hl]?)(\d+)', re.IGNORECASE)
    
    # 标准D&D骰子尺寸
    VALID_DICE_SIZES = {4, 6, 8, 10, 12, 20, 100}
    
    @classmethod
    def parse(cls, expression: str) -> Optional['DiceExpression']:
        """
        解析骰子表达式
        
        支持的格式：
        - d20, 1d20, 3d6
        - 1d20+5, 2d6-1
        - 2d20kh1 (保留最高1个)
        - 4d6dl1 (丢弃最低1个)
        - adv, dis (优势/劣势)
        """
        if not expression:
            return None
            
        expression = expression.strip().lower()
        
        # 处理特殊关键字（优势/劣势）
        if expression.startswith('adv') or expression.startswith('advantage'):
            # 提取修正值
            modifier = 0
            if expression.startswith('adv'):
                modifier_str = expression[3:]
            else:
                modifier_str = expression[9:]  # 'advantage' 长度为9
            
            # 解析修正值
            if modifier_str:
                for sign, value in cls.MODIFIER_PATTERN.findall(modifier_str):
                    modifier += int(value) if sign == '+' else -int(value)
            
            return DiceExpression(2, 20, modifier=modifier, dice_type=DiceType.ADVANTAGE,
                                keep_highest=1, original=expression)
                                
        elif expression.startswith('dis') or expression.startswith('disadvantage'):
            # 提取修正值
            modifier = 0
            if expression.startswith('dis'):
                modifier_str = expression[3:]
            else:
                modifier_str = expression[12:]  # 'disadvantage' 长度为12
            
            # 解析修正值
            if modifier_str:
                for sign, value in cls.MODIFIER_PATTERN.findall(modifier_str):
                    modifier += int(value) if sign == '+' else -int(value)
            
            return DiceExpression(2, 20, modifier=modifier, dice_type=DiceType.DISADVANTAGE,
                                keep_lowest=1, original=expression)
        
        # 尝试匹配标准骰子表达式
        match = cls.DICE_PATTERN.match(expression)
        if not match:
            return None
            
        count = int(match.group('count') or 1)
        size = int(match.group('size'))
        modifiers_str = match.group('modifiers') or ''
        
        # 验证骰子数量和尺寸
        if count <= 0 or count > 100:  # 限制骰子数量
            return None
        if size not in cls.VALID_DICE_SIZES:
            return None
            
        # 解析修正值
        modifier = 0
        for sign, value in cls.MODIFIER_PATTERN.findall(modifiers_str):
            modifier += int(value) if sign == '+' else -int(value)
            
        # 解析保留/丢弃规则
        keep_highest = None
        keep_lowest = None
        drop_highest = None
        drop_lowest = None
        
        for match in cls.KEEP_DROP_PATTERN.finditer(modifiers_str):
            action = match.group(1).lower()  # k or d
            high_low = match.group(2).lower()  # h, l, or empty
            number = int(match.group(3))
            
            if action == 'k':  # keep
                if high_low == 'h' or high_low == '':
                    keep_highest = number
                elif high_low == 'l':
                    keep_lowest = number
            elif action == 'd':  # drop
                if high_low == 'l' or high_low == '':
                    drop_lowest = number
                elif high_low == 'h':
                    drop_highest = number
        
        return DiceExpression(
            count=count,
            size=size,
            modifier=modifier,
            keep_highest=keep_highest,
            keep_lowest=keep_lowest,
            drop_highest=drop_highest,
            drop_lowest=drop_lowest,
            original=expression
        )
    
    @classmethod
    def validate_expression(cls, expression: str) -> Tuple[bool, str]:
        """验证骰子表达式是否有效"""
        result = cls.parse(expression)
        if result is None:
            return False, "无效的骰子表达式格式"
        return True, "表达式有效"

@dataclass
class DiceExpression:
    """解析后的骰子表达式"""
    count: int
    size: int
    modifier: int = 0
    keep_highest: Optional[int] = None
    keep_lowest: Optional[int] = None
    drop_highest: Optional[int] = None
    drop_lowest: Optional[int] = None
    dice_type: DiceType = DiceType.NORMAL
    original: str = ""
    
    def __post_init__(self):
        """后处理验证"""
        # 确保保留/丢弃的数量不超过骰子总数
        if self.keep_highest and self.keep_highest > self.count:
            self.keep_highest = self.count
        if self.keep_lowest and self.keep_lowest > self.count:
            self.keep_lowest = self.count
        if self.drop_highest and self.drop_highest >= self.count:
            self.drop_highest = self.count - 1
        if self.drop_lowest and self.drop_lowest >= self.count:
            self.drop_lowest = self.count - 1
    
    def roll(self) -> DiceResult:
        """执行骰子投掷"""
        # 生成所有骰子结果
        rolls = []
        for _ in range(self.count):
            value = random.randint(1, self.size)
            roll = DiceRoll(
                value=value,
                dice_size=self.size,
                is_max=(value == self.size),
                is_min=(value == 1)
            )
            rolls.append(roll)
        
        # 应用保留/丢弃规则
        self._apply_keep_drop_rules(rolls)
        
        # 计算总和
        total = sum(roll.value for roll in rolls if roll.kept) + self.modifier
        
        # 生成详细信息
        details = self._generate_details(rolls)
        
        return DiceResult(
            expression=self.original,
            total=total,
            rolls=rolls,
            modifier=self.modifier,
            dice_type=self.dice_type,
            details=details
        )
    
    def _apply_keep_drop_rules(self, rolls: List[DiceRoll]) -> None:
        """应用保留/丢弃规则"""
        if not any([self.keep_highest, self.keep_lowest, 
                   self.drop_highest, self.drop_lowest]):
            return
            
        # 按值排序（保持原始索引）
        indexed_rolls = list(enumerate(rolls))
        
        if self.keep_highest:
            # 保留最高的N个
            indexed_rolls.sort(key=lambda x: x[1].value, reverse=True)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i < self.keep_highest
                
        elif self.keep_lowest:
            # 保留最低的N个
            indexed_rolls.sort(key=lambda x: x[1].value)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i < self.keep_lowest
                
        elif self.drop_highest:
            # 丢弃最高的N个
            indexed_rolls.sort(key=lambda x: x[1].value, reverse=True)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i >= self.drop_highest
                
        elif self.drop_lowest:
            # 丢弃最低的N个
            indexed_rolls.sort(key=lambda x: x[1].value)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i >= self.drop_lowest
    
    def _generate_details(self, rolls: List[DiceRoll]) -> str:
        """生成详细信息字符串"""
        details = []
        
        if self.dice_type == DiceType.ADVANTAGE:
            details.append("优势骰")
        elif self.dice_type == DiceType.DISADVANTAGE:
            details.append("劣势骰")
            
        if any(not roll.kept for roll in rolls):
            kept_count = sum(1 for roll in rolls if roll.kept)
            details.append(f"保留{kept_count}个结果")
            
        return " | ".join(details) 