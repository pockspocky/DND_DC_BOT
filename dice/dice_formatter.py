"""
Dice Result Formatter
Formats dice results for display with visual indicators
"""
from typing import Dict, Any, List
from dice.ast_nodes import DiceRollResult, EvaluationResult, DieResult


class DiceFormatter:
    """Formats dice results for display"""
    
    @staticmethod
    def format_result(result: EvaluationResult) -> str:
        """
        Format evaluation result as a readable string
        
        Args:
            result: EvaluationResult to format
            
        Returns:
            Formatted string with dice breakdown
        """
        if result.is_success_count:
            return DiceFormatter._format_success_count(result)
        else:
            return DiceFormatter._format_normal_roll(result)
    
    @staticmethod
    def _format_normal_roll(result: EvaluationResult) -> str:
        """Format a normal dice roll"""
        parts = []
        
        # Add expression
        parts.append(f"**Roll:** {result.expression}")
        
        # Add dice breakdowns
        if result.dice_results:
            for dice_result in result.dice_results:
                breakdown = DiceFormatter._format_dice_breakdown(dice_result)
                parts.append(f"**Dice:** {breakdown}")
        
        # Add final result
        parts.append(f"**Result:** {result.final_value}")
        
        return "\n".join(parts)
    
    @staticmethod
    def _format_success_count(result: EvaluationResult) -> str:
        """Format a success counting roll"""
        parts = []
        
        # Add expression
        parts.append(f"**Roll:** {result.expression}")
        
        # Add dice breakdown
        if result.dice_results:
            dice_result = result.dice_results[0]
            dice_list = DiceFormatter._format_dice_list(dice_result.rolls)
            parts.append(f"**Dice:** {dice_list}")
        
        # Add success count
        parts.append(f"**Successes:** {result.success_count}")
        
        return "\n".join(parts)
    
    @staticmethod
    def _format_dice_breakdown(dice_result: DiceRollResult) -> str:
        """
        Format a dice roll result with visual indicators
        
        Returns:
            String like "[6, 5, ~~3~~, 2] = 13"
        """
        # Sort if needed
        rolls = dice_result.rolls.copy()
        if dice_result.dice_node.sort_ascending:
            rolls.sort(key=lambda r: r.final_value)
        elif dice_result.dice_node.sort_descending:
            rolls.sort(key=lambda r: r.final_value, reverse=True)
        
        # Format each die
        dice_list = DiceFormatter._format_dice_list(rolls)
        
        # Add total
        return f"{dice_list} = {dice_result.total}"
    
    @staticmethod
    def _format_dice_list(rolls: List[DieResult]) -> str:
        """Format a list of dice results with visual indicators"""
        formatted_dice = []
        
        for roll in rolls:
            formatted_dice.append(str(roll))  # Uses DieResult.__str__
        
        return f"[{', '.join(formatted_dice)}]"
    
    @staticmethod
    def format_embed(result: EvaluationResult, user_name: str) -> Dict[str, Any]:
        """
        Format result as Discord embed
        
        Args:
            result: EvaluationResult to format
            user_name: Name of the user who rolled
            
        Returns:
            Discord embed dictionary
        """
        # Determine color
        color = DiceFormatter._get_embed_color(result)
        
        # Build embed
        embed = {
            "title": f"🎲 {user_name}'s Roll",
            "color": color,
            "fields": []
        }
        
        # Add expression field
        embed["fields"].append({
            "name": "Expression",
            "value": f"`{result.expression}`",
            "inline": True
        })
        
        # Add result field
        if result.is_success_count:
            embed["fields"].append({
                "name": "Successes",
                "value": f"**{result.success_count}**",
                "inline": True
            })
        else:
            embed["fields"].append({
                "name": "Result",
                "value": f"**{result.final_value}**",
                "inline": True
            })
        
        # Add dice breakdown
        if result.dice_results:
            for i, dice_result in enumerate(result.dice_results):
                breakdown = DiceFormatter._format_dice_breakdown(dice_result)
                field_name = f"Dice {i+1}" if len(result.dice_results) > 1 else "Dice"
                embed["fields"].append({
                    "name": field_name,
                    "value": breakdown,
                    "inline": False
                })
        
        return embed
    
    @staticmethod
    def _get_embed_color(result: EvaluationResult) -> int:
        """
        Determine embed color based on result
        
        Returns:
            Integer color code
        """
        # Check for critical success (natural 20 on d20)
        if result.has_critical_success():
            return 0xFFD700  # Gold
        
        # Check for critical failure (natural 1 on d20)
        if result.has_critical_failure():
            return 0xFF0000  # Red
        
        # Check for success counting
        if result.is_success_count:
            return 0x9932CC  # Purple
        
        # Default green
        return 0x00FF00
