"""
Error handling system
Provides unified exception handling, error classification, and error recovery mechanisms
"""

import discord
from discord.ext import commands
import asyncio
import traceback
import sys
from typing import Dict, Type, Optional, Callable, Any
from enum import Enum
import logging

# Get logger
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor error, does not affect usage
    MEDIUM = "medium"     # Medium error, affects some functionality
    HIGH = "high"         # Severe error, affects core functionality
    CRITICAL = "critical" # Critical error, may cause bot crash

class ErrorCategory(Enum):
    """Error categories"""
    NETWORK = "network"           # Network connection errors
    DATABASE = "database"         # Database operation errors
    DISCORD_API = "discord_api"   # Discord API errors
    PERMISSION = "permission"     # Permission-related errors
    USER_INPUT = "user_input"     # User input errors
    SYSTEM = "system"             # System-level errors
    EXTERNAL_API = "external_api" # External API errors
    VALIDATION = "validation"     # Data validation errors

class BotError(Exception):
    """Bot custom exception base class"""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.user_message = user_message or "Operation failed, please try again later"
        self.error_code = error_code
        self.recoverable = recoverable
        
    def __str__(self):
        return f"[{self.category.value.upper()}] {super().__str__()}"

class NetworkError(BotError):
    """Network-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            category=ErrorCategory.NETWORK,
            user_message="Network connection issue, please try again later",
            **kwargs
        )

class DatabaseError(BotError):
    """Database-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            user_message="Database operation failed, please try again later",
            **kwargs
        )

class ValidationError(BotError):
    """Data validation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message="Invalid input parameters, please check and try again",
            **kwargs
        )

class PermissionError(BotError):
    """Permission-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Insufficient permissions to perform this operation",
            **kwargs
        )

class ErrorHandler:
    """Unified error handler"""
    
    def __init__(self):
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.error_stats: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        
        # Register default error handlers
        self._register_default_handlers()
        
        # Register recovery strategies
        self._register_recovery_strategies()
    
    def _register_default_handlers(self):
        """Register default error handlers"""
        
        # Discord API errors
        self.register_handler(discord.HTTPException, self._handle_discord_http_error)
        self.register_handler(discord.Forbidden, self._handle_discord_forbidden)
        self.register_handler(discord.NotFound, self._handle_discord_not_found)
        
        # Network errors
        self.register_handler(asyncio.TimeoutError, self._handle_timeout_error)
        self.register_handler(ConnectionError, self._handle_connection_error)
        
        # Command errors
        self.register_handler(commands.CommandNotFound, self._handle_command_not_found)
        self.register_handler(commands.MissingRequiredArgument, self._handle_missing_argument)
        self.register_handler(commands.BadArgument, self._handle_bad_argument)
        self.register_handler(commands.CheckFailure, self._handle_check_failure)
        
        # Bot custom errors
        self.register_handler(BotError, self._handle_bot_error)
    
    def _register_recovery_strategies(self):
        """Register error recovery strategies"""
        self.recovery_strategies[ErrorCategory.NETWORK] = self._recover_network_error
        self.recovery_strategies[ErrorCategory.DATABASE] = self._recover_database_error
        self.recovery_strategies[ErrorCategory.DISCORD_API] = self._recover_discord_error
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """Register error handler"""
        self.error_handlers[exception_type] = handler
        logger.debug(f"Registered error handler: {exception_type.__name__}")
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        interaction: Optional[discord.Interaction] = None,
        ctx: Optional[commands.Context] = None
    ) -> bool:
        """
        Handle errors
        
        Args:
            error: The exception that occurred
            context: Error context information
            interaction: Discord interaction object
            ctx: Command context object
            
        Returns:
            Whether the error was successfully handled
        """
        
        # Update error statistics
        error_type = type(error).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        # Log error details
        await self._log_error(error, context, interaction, ctx)
        
        # Find corresponding error handler
        handler = self._find_handler(error)
        
        if handler:
            try:
                success = await handler(error, context, interaction, ctx)
                if success:
                    logger.info(f"Error handled successfully: {error_type}")
                    return True
                else:
                    logger.warning(f"Error handler returned failure: {error_type}")
            except Exception as handler_error:
                logger.error(f"Error handler itself failed: {handler_error}")
        
        # Try recovery strategy
        if isinstance(error, BotError):
            recovery_func = self.recovery_strategies.get(error.category)
            if recovery_func:
                try:
                    recovered = await recovery_func(error, context)
                    if recovered:
                        logger.info(f"Error recovery successful: {error_type}")
                        return True
                except Exception as recovery_error:
                    logger.error(f"Error recovery failed: {recovery_error}")
        
        # Default error handling
        await self._handle_default_error(error, interaction, ctx)
        return False
    
    def _find_handler(self, error: Exception) -> Optional[Callable]:
        """Find appropriate error handler"""
        error_type = type(error)
        
        # Direct match
        if error_type in self.error_handlers:
            return self.error_handlers[error_type]
        
        # Find parent class match
        for exc_type, handler in self.error_handlers.items():
            if isinstance(error, exc_type):
                return handler
        
        return None
    
    async def _log_error(
        self, 
        error: Exception, 
        context: Optional[dict],
        interaction: Optional[discord.Interaction],
        ctx: Optional[commands.Context]
    ):
        """Log error details"""
        
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
        }
        
        # Add context information
        if context:
            error_info.update(context)
        
        # Add Discord-related information
        if interaction:
            error_info.update({
                'user_id': interaction.user.id,
                'guild_id': interaction.guild.id if interaction.guild else None,
                'channel_id': interaction.channel.id if interaction.channel else None,
                'command': interaction.command.name if interaction.command else 'unknown'
            })
        
        if ctx:
            error_info.update({
                'user_id': ctx.author.id,
                'guild_id': ctx.guild.id if ctx.guild else None,
                'channel_id': ctx.channel.id,
                'command': ctx.command.name if ctx.command else 'unknown'
            })
        
        # Choose log level based on error severity
        if isinstance(error, BotError):
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical("Critical error", extra=error_info)
            elif error.severity == ErrorSeverity.HIGH:
                logger.error("High-level error", extra=error_info)
            elif error.severity == ErrorSeverity.MEDIUM:
                logger.warning("Medium error", extra=error_info)
            else:
                logger.info("Minor error", extra=error_info)
        else:
            logger.error("Unclassified error", extra=error_info)
    
    # === Specific error handlers ===
    
    async def _handle_discord_http_error(self, error, context, interaction, ctx):
        """Handle Discord HTTP errors"""
        if error.status == 429:  # Rate limit
            await self._send_error_message(
                "Too many requests, please try again later",
                interaction, ctx, ephemeral=True
            )
        elif error.status >= 500:  # Server error
            await self._send_error_message(
                "Discord server error, please try again later",
                interaction, ctx, ephemeral=True
            )
        else:
            await self._send_error_message(
                "Discord API error, please try again later",
                interaction, ctx, ephemeral=True
            )
        return True
    
    async def _handle_discord_forbidden(self, error, context, interaction, ctx):
        """Handle insufficient permissions error"""
        await self._send_error_message(
            "❌ Insufficient permissions, please check bot permission settings",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_discord_not_found(self, error, context, interaction, ctx):
        """Handle resource not found error"""
        await self._send_error_message(
            "❌ Requested resource not found",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_timeout_error(self, error, context, interaction, ctx):
        """Handle timeout error"""
        await self._send_error_message(
            "❌ Operation timed out, please try again later",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_connection_error(self, error, context, interaction, ctx):
        """Handle connection error"""
        await self._send_error_message(
            "❌ Network connection issue, please try again later",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_command_not_found(self, error, context, interaction, ctx):
        """Handle command not found error"""
        # For slash commands, this error should not occur, so don't send a message
        return True
    
    async def _handle_missing_argument(self, error, context, interaction, ctx):
        """Handle missing argument error"""
        await self._send_error_message(
            f"❌ Missing required parameter: `{error.param.name}`",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_bad_argument(self, error, context, interaction, ctx):
        """Handle bad argument error"""
        await self._send_error_message(
            f"❌ Invalid argument: {str(error)}",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_check_failure(self, error, context, interaction, ctx):
        """Handle check failure error"""
        await self._send_error_message(
            "❌ Permission check failed, you do not have permission to execute this command",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_bot_error(self, error: BotError, context, interaction, ctx):
        """Handle bot custom error"""
        await self._send_error_message(
            error.user_message,
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_default_error(self, error, interaction, ctx):
        """Default error handling"""
        await self._send_error_message(
            "❌ An unknown error occurred, please try again later",
            interaction, ctx, ephemeral=True
        )
    
    # === Recovery strategies ===
    
    async def _recover_network_error(self, error: BotError, context):
        """Network error recovery strategy"""
        # Can implement retry logic
        logger.info("Attempting network error recovery...")
        await asyncio.sleep(1)  # Simple wait
        return False  # Actual recovery logic can be implemented here
    
    async def _recover_database_error(self, error: BotError, context):
        """Database error recovery strategy"""
        logger.info("Attempting database error recovery...")
        # Can implement database reconnection logic
        return False
    
    async def _recover_discord_error(self, error: BotError, context):
        """Discord error recovery strategy"""
        logger.info("Attempting Discord error recovery...")
        return False
    
    # === Utility methods ===
    
    async def _send_error_message(
        self, 
        message: str, 
        interaction: Optional[discord.Interaction],
        ctx: Optional[commands.Context],
        ephemeral: bool = True
    ):
        """Send error message"""
        try:
            if interaction:
                if not interaction.response.is_done():
                    await interaction.response.send_message(message, ephemeral=ephemeral)
                else:
                    await interaction.followup.send(message, ephemeral=ephemeral)
            elif ctx:
                await ctx.send(message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_stats.copy()
    
    def reset_error_stats(self):
        """Reset error statistics"""
        self.error_stats.clear()
        logger.info("Error statistics reset")

# Global error handler instance
error_handler = ErrorHandler()

# Convenience decorator
def handle_errors(func):
    """Error handling decorator"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Try to get interaction or ctx from arguments
            interaction = None
            ctx = None
            
            for arg in args:
                if isinstance(arg, discord.Interaction):
                    interaction = arg
                    break
                elif isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            await error_handler.handle_error(
                e, 
                context={'function': func.__name__},
                interaction=interaction,
                ctx=ctx
            )
            raise  # Re-raise exception for upper layer handling
    
    return wrapper 