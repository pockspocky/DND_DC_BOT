"""
AST Node Types for Advanced Dice Roller
Defines the Abstract Syntax Tree structure for parsed dice expressions
"""
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum


class NodeType(Enum):
    """Types of AST nodes"""
    CONSTANT = "constant"
    DICE = "dice"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    SUCCESS_COUNT = "success_count"


class ComparisonOp(Enum):
    """Comparison operators for success counting"""
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    GREATER = ">"
    LESS = "<"
    EQUAL = "="


class ASTNode:
    """Base class for AST nodes"""
    node_type: NodeType


@dataclass
class ConstantNode(ASTNode):
    """Represents a constant integer value"""
    value: int
    node_type: NodeType = field(default=NodeType.CONSTANT, init=False)


@dataclass
class DiceNode(ASTNode):
    """
    Represents a dice term with optional operators
    
    Operators are applied in this order:
    1. Roll dice
    2. Apply rerolls (r/ro)
    3. Apply min/max clamping
    4. Apply keep/drop (kh/kl/dh/dl)
    5. Apply sorting (s/sd) - visual only
    """
    count: int
    size: int
    reroll: Optional[int] = None
    reroll_once: bool = True  # True for 'r', False for 'ro'
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    keep_highest: Optional[int] = None
    keep_lowest: Optional[int] = None
    drop_highest: Optional[int] = None
    drop_lowest: Optional[int] = None
    sort_ascending: bool = False
    sort_descending: bool = False
    node_type: NodeType = field(default=NodeType.DICE, init=False)


@dataclass
class SuccessCountNode(ASTNode):
    """Represents success counting on a dice pool"""
    dice: DiceNode
    comparison: ComparisonOp
    threshold: int
    node_type: NodeType = field(default=NodeType.SUCCESS_COUNT, init=False)


@dataclass
class BinaryOpNode(ASTNode):
    """Represents binary arithmetic operations"""
    operator: Literal["+", "-", "*", "/", "//"]
    left: ASTNode
    right: ASTNode
    node_type: NodeType = field(default=NodeType.BINARY_OP, init=False)


@dataclass
class UnaryOpNode(ASTNode):
    """Represents unary operations (negation, positive)"""
    operator: Literal["-", "+"]
    operand: ASTNode
    node_type: NodeType = field(default=NodeType.UNARY_OP, init=False)


# Result data structures

@dataclass
class DieResult:
    """
    Single die result with metadata
    
    Tracks the complete lifecycle of a die roll including
    rerolls, clamping, and keep/drop status
    """
    original_value: int  # Initial roll value
    final_value: int     # Value after rerolls and clamping
    kept: bool = True    # Whether this die contributes to the sum
    rerolled: bool = False  # Whether this die was rerolled
    clamped: bool = False   # Whether this die was clamped (min/max)
    is_max: bool = False    # Whether final value equals die size
    is_min: bool = False    # Whether final value equals 1
    
    def __str__(self) -> str:
        """Format die result for display"""
        value_str = str(self.final_value)
        
        # Mark special values
        if self.is_max:
            value_str = f"**{value_str}**"  # Bold for max
        elif self.is_min:
            value_str = f"*{value_str}*"    # Italic for min
        
        # Mark clamped dice
        if self.clamped and self.original_value != self.final_value:
            value_str = f"{value_str}↑" if self.final_value > self.original_value else f"{value_str}↓"
        
        # Strikethrough dropped dice
        if not self.kept:
            value_str = f"~~{value_str}~~"
        
        return value_str


@dataclass
class DiceRollResult:
    """Result of rolling a dice term"""
    dice_node: DiceNode
    rolls: List[DieResult]
    total: int  # Sum of kept dice only
    
    def get_kept_rolls(self) -> List[DieResult]:
        """Get only the dice that were kept"""
        return [roll for roll in self.rolls if roll.kept]
    
    def get_dropped_rolls(self) -> List[DieResult]:
        """Get only the dice that were dropped"""
        return [roll for roll in self.rolls if not roll.kept]


@dataclass
class EvaluationResult:
    """Complete evaluation result for a dice expression"""
    expression: str  # Original expression string
    ast: ASTNode     # Parsed AST
    final_value: int # Final numeric result
    dice_results: List[DiceRollResult] = field(default_factory=list)
    is_success_count: bool = False
    success_count: Optional[int] = None
    
    def has_critical_success(self) -> bool:
        """Check if any d20 rolled a natural 20"""
        for dice_result in self.dice_results:
            if dice_result.dice_node.size == 20:
                for roll in dice_result.get_kept_rolls():
                    if roll.final_value == 20 and not roll.clamped:
                        return True
        return False
    
    def has_critical_failure(self) -> bool:
        """Check if any d20 rolled a natural 1"""
        for dice_result in self.dice_results:
            if dice_result.dice_node.size == 20:
                for roll in dice_result.get_kept_rolls():
                    if roll.final_value == 1 and not roll.clamped:
                        return True
        return False
