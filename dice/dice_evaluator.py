"""
Dice Evaluator
Evaluates AST nodes to produce dice roll results
"""
import random
from typing import List, Optional, Callable
from dice.ast_nodes import (
    ASTNode, ConstantNode, DiceNode, SuccessCountNode,
    BinaryOpNode, UnaryOpNode, NodeType, ComparisonOp,
    DieResult, DiceRollResult, EvaluationResult
)
from dice.exceptions import EvaluationError


class DiceEvaluator:
    """
    Evaluates AST nodes to produce results
    
    Supports dependency injection of random source for testing
    """
    
    def __init__(self, random_func: Optional[Callable[[int, int], int]] = None):
        """
        Initialize evaluator
        
        Args:
            random_func: Optional random function for testing (default: random.randint)
        """
        self.random_func = random_func or random.randint
        self.dice_results: List[DiceRollResult] = []
    
    def evaluate(self, node: ASTNode, expression: str) -> EvaluationResult:
        """
        Evaluate an AST node
        
        Args:
            node: Root AST node
            expression: Original expression string
            
        Returns:
            EvaluationResult with final value and dice results
            
        Raises:
            EvaluationError: If evaluation fails
        """
        self.dice_results = []  # Reset for new evaluation
        
        # Check if this is a success count node at the root
        is_success_count = isinstance(node, SuccessCountNode)
        
        # Evaluate the node
        final_value = self._evaluate_node(node)
        
        # Build result
        result = EvaluationResult(
            expression=expression,
            ast=node,
            final_value=final_value,
            dice_results=self.dice_results.copy(),
            is_success_count=is_success_count,
            success_count=final_value if is_success_count else None
        )
        
        return result
    
    def _evaluate_node(self, node: ASTNode) -> int:
        """
        Evaluate a single AST node
        
        Returns:
            Integer result of evaluation
        """
        if isinstance(node, ConstantNode):
            return self._evaluate_constant(node)
        elif isinstance(node, DiceNode):
            dice_result = self._evaluate_dice(node)
            self.dice_results.append(dice_result)
            return dice_result.total
        elif isinstance(node, SuccessCountNode):
            return self._evaluate_success_count(node)
        elif isinstance(node, BinaryOpNode):
            return self._evaluate_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self._evaluate_unary_op(node)
        else:
            raise EvaluationError(f"Unknown node type: {type(node)}")
    
    def _evaluate_constant(self, node: ConstantNode) -> int:
        """Evaluate a constant node"""
        return node.value
    
    def _evaluate_binary_op(self, node: BinaryOpNode) -> int:
        """Evaluate a binary operation node"""
        left_value = self._evaluate_node(node.left)
        right_value = self._evaluate_node(node.right)
        
        if node.operator == "+":
            return left_value + right_value
        elif node.operator == "-":
            return left_value - right_value
        elif node.operator == "*":
            return left_value * right_value
        elif node.operator == "/":
            if right_value == 0:
                raise EvaluationError("Division by zero")
            return int(left_value / right_value)
        elif node.operator == "//":
            if right_value == 0:
                raise EvaluationError("Division by zero")
            return left_value // right_value
        else:
            raise EvaluationError(f"Unknown operator: {node.operator}")
    
    def _evaluate_unary_op(self, node: UnaryOpNode) -> int:
        """Evaluate a unary operation node"""
        operand_value = self._evaluate_node(node.operand)
        
        if node.operator == "-":
            return -operand_value
        elif node.operator == "+":
            return operand_value
        else:
            raise EvaluationError(f"Unknown unary operator: {node.operator}")
    
    def _evaluate_dice(self, node: DiceNode) -> DiceRollResult:
        """
        Evaluate a dice node
        
        Returns:
            DiceRollResult with all rolls and total
        """
        # Roll all dice
        rolls: List[DieResult] = []
        for _ in range(node.count):
            value = self.random_func(1, node.size)
            die_result = DieResult(
                original_value=value,
                final_value=value,
                is_max=(value == node.size),
                is_min=(value == 1)
            )
            rolls.append(die_result)
        
        # Apply operators in order:
        # 1. Rerolls
        if node.reroll is not None:
            self._apply_rerolls(rolls, node.reroll, node.reroll_once, node.size)
        
        # 2. Min/max clamping
        if node.min_value is not None or node.max_value is not None:
            self._apply_clamping(rolls, node.min_value, node.max_value, node.size)
        
        # 3. Keep/drop
        self._apply_keep_drop(rolls, node)
        
        # 4. Sorting (visual only, handled in formatter)
        
        # Calculate total
        total = sum(roll.final_value for roll in rolls if roll.kept)
        
        return DiceRollResult(
            dice_node=node,
            rolls=rolls,
            total=total
        )
    
    def _apply_rerolls(self, rolls: List[DieResult], reroll_value: int, 
                       reroll_once: bool, die_size: int) -> None:
        """
        Apply reroll operators to dice
        
        Args:
            rolls: List of die results to modify
            reroll_value: Value to reroll
            reroll_once: If True, reroll once (r). If False, reroll repeatedly (ro)
            die_size: Size of the die for validation
        """
        MAX_REROLL_ITERATIONS = 100
        
        for roll in rolls:
            if roll.final_value == reroll_value:
                roll.rerolled = True
                iterations = 0
                
                if reroll_once:
                    # Reroll once (r operator)
                    new_value = self.random_func(1, die_size)
                    roll.final_value = new_value
                    roll.is_max = (new_value == die_size)
                    roll.is_min = (new_value == 1)
                else:
                    # Reroll repeatedly until not reroll_value (ro operator)
                    while roll.final_value == reroll_value and iterations < MAX_REROLL_ITERATIONS:
                        new_value = self.random_func(1, die_size)
                        roll.final_value = new_value
                        roll.is_max = (new_value == die_size)
                        roll.is_min = (new_value == 1)
                        iterations += 1
                    
                    if iterations >= MAX_REROLL_ITERATIONS:
                        raise EvaluationError(
                            f"Reroll limit exceeded ({MAX_REROLL_ITERATIONS} iterations)"
                        )
    
    def _apply_clamping(self, rolls: List[DieResult], min_val: Optional[int],
                        max_val: Optional[int], die_size: int) -> None:
        """
        Apply min/max clamping to dice
        
        Args:
            rolls: List of die results to modify
            min_val: Minimum value (or None)
            max_val: Maximum value (or None)
            die_size: Size of the die for validation
        """
        for roll in rolls:
            original = roll.final_value
            
            if min_val is not None and roll.final_value < min_val:
                roll.final_value = min_val
                roll.clamped = True
            
            if max_val is not None and roll.final_value > max_val:
                roll.final_value = max_val
                roll.clamped = True
            
            # Update is_max and is_min based on clamped value
            if roll.clamped:
                roll.is_max = (roll.final_value == die_size)
                roll.is_min = (roll.final_value == 1)
    
    def _apply_keep_drop(self, rolls: List[DieResult], node: DiceNode) -> None:
        """
        Apply keep/drop operators to dice
        
        Args:
            rolls: List of die results to modify
            node: DiceNode with keep/drop settings
        """
        # If no keep/drop operators, all dice are kept
        if not any([node.keep_highest, node.keep_lowest, 
                   node.drop_highest, node.drop_lowest]):
            return
        
        # Create indexed list for sorting while preserving original order
        indexed_rolls = list(enumerate(rolls))
        
        if node.keep_highest:
            # Keep highest N dice
            indexed_rolls.sort(key=lambda x: x[1].final_value, reverse=True)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i < node.keep_highest
        
        elif node.keep_lowest:
            # Keep lowest N dice
            indexed_rolls.sort(key=lambda x: x[1].final_value)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i < node.keep_lowest
        
        elif node.drop_highest:
            # Drop highest N dice
            indexed_rolls.sort(key=lambda x: x[1].final_value, reverse=True)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i >= node.drop_highest
        
        elif node.drop_lowest:
            # Drop lowest N dice
            indexed_rolls.sort(key=lambda x: x[1].final_value)
            for i, (orig_idx, roll) in enumerate(indexed_rolls):
                roll.kept = i >= node.drop_lowest
    
    def _evaluate_success_count(self, node: SuccessCountNode) -> int:
        """
        Evaluate a success count node
        
        Returns:
            Number of successes
        """
        # Evaluate the dice
        dice_result = self._evaluate_dice(node.dice)
        self.dice_results.append(dice_result)
        
        # Count successes based on comparison
        success_count = 0
        for roll in dice_result.rolls:
            if not roll.kept:
                continue
            
            value = roll.final_value
            threshold = node.threshold
            
            if node.comparison == ComparisonOp.GREATER_EQUAL:
                if value >= threshold:
                    success_count += 1
            elif node.comparison == ComparisonOp.LESS_EQUAL:
                if value <= threshold:
                    success_count += 1
            elif node.comparison == ComparisonOp.GREATER:
                if value > threshold:
                    success_count += 1
            elif node.comparison == ComparisonOp.LESS:
                if value < threshold:
                    success_count += 1
            elif node.comparison == ComparisonOp.EQUAL:
                if value == threshold:
                    success_count += 1
        
        return success_count
