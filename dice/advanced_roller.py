"""
Advanced Dice Roller Facade
High-level interface for the advanced dice rolling system
"""
import logging
from typing import Optional, Dict
from dice.expression_parser import parse, validate
from dice.dice_evaluator import DiceEvaluator
from dice.dice_formatter import DiceFormatter
from dice.ast_nodes import EvaluationResult
from dice.exceptions import DiceError, ParseError, ValidationError, EvaluationError
import json

logger = logging.getLogger(__name__)


class AdvancedDiceRoller:
    """
    High-level facade for advanced dice rolling
    
    Coordinates parsing, evaluation, and formatting
    """
    
    def __init__(self):
        self.evaluator = DiceEvaluator()
        self.formatter = DiceFormatter()
        self.last_results: Dict[int, EvaluationResult] = {}
    
    async def roll(self, expression: str, user_id: int, guild_id: int,
                   channel_id: int) -> EvaluationResult:
        """
        Roll dice from an expression
        
        Args:
            expression: Dice expression string
            user_id: Discord user ID
            guild_id: Discord guild ID
            channel_id: Discord channel ID
            
        Returns:
            EvaluationResult
            
        Raises:
            ParseError: If expression is invalid
            ValidationError: If expression exceeds limits
            EvaluationError: If evaluation fails
        """
        try:
            # Parse expression
            ast = parse(expression)
            
            # Evaluate
            result = self.evaluator.evaluate(ast, expression)
            
            # Cache result
            self.last_results[user_id] = result
            
            # Save to database (if available)
            try:
                await self._save_to_history(result, user_id, guild_id, channel_id)
            except Exception as e:
                logger.warning(f"Failed to save roll history: {e}")
            
            return result
            
        except (ParseError, ValidationError, EvaluationError) as e:
            logger.error(f"Roll failed for expression '{expression}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error rolling '{expression}': {e}")
            raise EvaluationError(f"Unexpected error: {str(e)}")
    
    def format_result(self, result: EvaluationResult) -> str:
        """Format result as string"""
        return self.formatter.format_result(result)
    
    def format_embed(self, result: EvaluationResult, user_name: str) -> dict:
        """Format result as Discord embed"""
        return self.formatter.format_embed(result, user_name)
    
    def get_last_result(self, user_id: int) -> Optional[EvaluationResult]:
        """Get user's last roll result"""
        return self.last_results.get(user_id)
    
    async def _save_to_history(self, result: EvaluationResult, user_id: int,
                               guild_id: int, channel_id: int) -> None:
        """
        Save roll to database
        
        Args:
            result: EvaluationResult to save
            user_id: Discord user ID
            guild_id: Discord guild ID
            channel_id: Discord channel ID
        """
        try:
            # Import database manager
            from database import db_manager
            
            # Get database user and guild
            db_user = await db_manager.get_user_by_discord_id(user_id)
            db_guild = await db_manager.get_guild_by_discord_id(guild_id)
            
            if not db_user or not db_guild:
                logger.warning(f"Cannot find user or guild: user={user_id}, guild={guild_id}")
                return
            
            # Build details JSON
            details = {
                "dice_results": [
                    {
                        "count": dr.dice_node.count,
                        "size": dr.dice_node.size,
                        "rolls": [
                            {
                                "original": r.original_value,
                                "final": r.final_value,
                                "kept": r.kept,
                                "rerolled": r.rerolled,
                                "clamped": r.clamped,
                                "is_max": r.is_max,
                                "is_min": r.is_min
                            }
                            for r in dr.rolls
                        ],
                        "total": dr.total
                    }
                    for dr in result.dice_results
                ],
                "is_success_count": result.is_success_count,
                "success_count": result.success_count
            }
            
            # Determine roll type
            roll_type = "success_count" if result.is_success_count else "normal"
            
            # Save to database
            await db_manager.log_dice_roll(
                user_id=db_user['id'],
                guild_id=db_guild['id'],
                channel_id=channel_id,
                dice_expression=result.expression,
                result=result.final_value,
                details=json.dumps(details),
                roll_type=roll_type
            )
            
        except ImportError:
            # Database not available (testing environment)
            pass
        except Exception as e:
            logger.error(f"Failed to save roll history: {e}")
            raise


# Global instance
advanced_roller = AdvancedDiceRoller()
