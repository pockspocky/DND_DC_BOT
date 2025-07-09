"""
错误处理系统
提供统一的异常处理、错误分类、错误恢复机制
"""

import discord
from discord.ext import commands
import asyncio
import traceback
import sys
from typing import Dict, Type, Optional, Callable, Any
from enum import Enum
import logging

# 获取日志器
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 轻微错误，不影响使用
    MEDIUM = "medium"     # 中等错误，影响部分功能
    HIGH = "high"         # 严重错误，影响核心功能
    CRITICAL = "critical" # 严重错误，可能导致机器人崩溃

class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"           # 网络连接错误
    DATABASE = "database"         # 数据库操作错误
    DISCORD_API = "discord_api"   # Discord API错误
    PERMISSION = "permission"     # 权限相关错误
    USER_INPUT = "user_input"     # 用户输入错误
    SYSTEM = "system"             # 系统级错误
    EXTERNAL_API = "external_api" # 外部API错误
    VALIDATION = "validation"     # 数据验证错误

class BotError(Exception):
    """机器人自定义异常基类"""
    
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
        self.user_message = user_message or "操作失败，请稍后重试"
        self.error_code = error_code
        self.recoverable = recoverable
        
    def __str__(self):
        return f"[{self.category.value.upper()}] {super().__str__()}"

class NetworkError(BotError):
    """网络相关错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            category=ErrorCategory.NETWORK,
            user_message="网络连接问题，请稍后重试",
            **kwargs
        )

class DatabaseError(BotError):
    """数据库相关错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            user_message="数据库操作失败，请稍后重试",
            **kwargs
        )

class ValidationError(BotError):
    """数据验证错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message="输入参数有误，请检查后重试",
            **kwargs
        )

class PermissionError(BotError):
    """权限相关错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.MEDIUM,
            user_message="权限不足，无法执行此操作",
            **kwargs
        )

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.error_stats: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        
        # 注册默认错误处理器
        self._register_default_handlers()
        
        # 注册恢复策略
        self._register_recovery_strategies()
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        
        # Discord API错误
        self.register_handler(discord.HTTPException, self._handle_discord_http_error)
        self.register_handler(discord.Forbidden, self._handle_discord_forbidden)
        self.register_handler(discord.NotFound, self._handle_discord_not_found)
        
        # 网络错误
        self.register_handler(asyncio.TimeoutError, self._handle_timeout_error)
        self.register_handler(ConnectionError, self._handle_connection_error)
        
        # 命令错误
        self.register_handler(commands.CommandNotFound, self._handle_command_not_found)
        self.register_handler(commands.MissingRequiredArgument, self._handle_missing_argument)
        self.register_handler(commands.BadArgument, self._handle_bad_argument)
        self.register_handler(commands.CheckFailure, self._handle_check_failure)
        
        # 机器人自定义错误
        self.register_handler(BotError, self._handle_bot_error)
    
    def _register_recovery_strategies(self):
        """注册错误恢复策略"""
        self.recovery_strategies[ErrorCategory.NETWORK] = self._recover_network_error
        self.recovery_strategies[ErrorCategory.DATABASE] = self._recover_database_error
        self.recovery_strategies[ErrorCategory.DISCORD_API] = self._recover_discord_error
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """注册错误处理器"""
        self.error_handlers[exception_type] = handler
        logger.debug(f"已注册错误处理器: {exception_type.__name__}")
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        interaction: Optional[discord.Interaction] = None,
        ctx: Optional[commands.Context] = None
    ) -> bool:
        """
        处理错误
        
        Args:
            error: 发生的异常
            context: 错误上下文信息
            interaction: Discord交互对象
            ctx: 命令上下文对象
            
        Returns:
            是否成功处理错误
        """
        
        # 更新错误统计
        error_type = type(error).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        # 记录错误详情
        await self._log_error(error, context, interaction, ctx)
        
        # 查找对应的错误处理器
        handler = self._find_handler(error)
        
        if handler:
            try:
                success = await handler(error, context, interaction, ctx)
                if success:
                    logger.info(f"错误处理成功: {error_type}")
                    return True
                else:
                    logger.warning(f"错误处理器返回失败: {error_type}")
            except Exception as handler_error:
                logger.error(f"错误处理器本身出错: {handler_error}")
        
        # 尝试恢复策略
        if isinstance(error, BotError):
            recovery_func = self.recovery_strategies.get(error.category)
            if recovery_func:
                try:
                    recovered = await recovery_func(error, context)
                    if recovered:
                        logger.info(f"错误恢复成功: {error_type}")
                        return True
                except Exception as recovery_error:
                    logger.error(f"错误恢复失败: {recovery_error}")
        
        # 默认错误处理
        await self._handle_default_error(error, interaction, ctx)
        return False
    
    def _find_handler(self, error: Exception) -> Optional[Callable]:
        """查找适合的错误处理器"""
        error_type = type(error)
        
        # 直接匹配
        if error_type in self.error_handlers:
            return self.error_handlers[error_type]
        
        # 查找父类匹配
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
        """记录错误详情"""
        
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
        }
        
        # 添加上下文信息
        if context:
            error_info.update(context)
        
        # 添加Discord相关信息
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
        
        # 根据错误严重程度选择日志级别
        if isinstance(error, BotError):
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical("严重错误", extra=error_info)
            elif error.severity == ErrorSeverity.HIGH:
                logger.error("高级错误", extra=error_info)
            elif error.severity == ErrorSeverity.MEDIUM:
                logger.warning("中等错误", extra=error_info)
            else:
                logger.info("轻微错误", extra=error_info)
        else:
            logger.error("未分类错误", extra=error_info)
    
    # === 具体错误处理器 ===
    
    async def _handle_discord_http_error(self, error, context, interaction, ctx):
        """处理Discord HTTP错误"""
        if error.status == 429:  # 速率限制
            await self._send_error_message(
                "操作过于频繁，请稍后重试",
                interaction, ctx, ephemeral=True
            )
        elif error.status >= 500:  # 服务器错误
            await self._send_error_message(
                "Discord服务器错误，请稍后重试",
                interaction, ctx, ephemeral=True
            )
        else:
            await self._send_error_message(
                "Discord API错误，请稍后重试",
                interaction, ctx, ephemeral=True
            )
        return True
    
    async def _handle_discord_forbidden(self, error, context, interaction, ctx):
        """处理权限不足错误"""
        await self._send_error_message(
            "❌ 权限不足，请检查机器人权限设置",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_discord_not_found(self, error, context, interaction, ctx):
        """处理资源未找到错误"""
        await self._send_error_message(
            "❌ 请求的资源未找到",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_timeout_error(self, error, context, interaction, ctx):
        """处理超时错误"""
        await self._send_error_message(
            "❌ 操作超时，请稍后重试",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_connection_error(self, error, context, interaction, ctx):
        """处理连接错误"""
        await self._send_error_message(
            "❌ 网络连接问题，请稍后重试",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_command_not_found(self, error, context, interaction, ctx):
        """处理命令未找到错误"""
        # 对于斜杠命令，这种错误不应该发生，所以不发送消息
        return True
    
    async def _handle_missing_argument(self, error, context, interaction, ctx):
        """处理缺少参数错误"""
        await self._send_error_message(
            f"❌ 缺少必需参数: `{error.param.name}`",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_bad_argument(self, error, context, interaction, ctx):
        """处理参数错误"""
        await self._send_error_message(
            f"❌ 参数错误: {str(error)}",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_check_failure(self, error, context, interaction, ctx):
        """处理检查失败错误"""
        await self._send_error_message(
            "❌ 权限检查失败，您没有执行此命令的权限",
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_bot_error(self, error: BotError, context, interaction, ctx):
        """处理机器人自定义错误"""
        await self._send_error_message(
            error.user_message,
            interaction, ctx, ephemeral=True
        )
        return True
    
    async def _handle_default_error(self, error, interaction, ctx):
        """默认错误处理"""
        await self._send_error_message(
            "❌ 发生未知错误，请稍后重试",
            interaction, ctx, ephemeral=True
        )
    
    # === 恢复策略 ===
    
    async def _recover_network_error(self, error: BotError, context):
        """网络错误恢复策略"""
        # 可以实现重试逻辑
        logger.info("尝试网络错误恢复...")
        await asyncio.sleep(1)  # 简单等待
        return False  # 这里可以实现实际的恢复逻辑
    
    async def _recover_database_error(self, error: BotError, context):
        """数据库错误恢复策略"""
        logger.info("尝试数据库错误恢复...")
        # 可以实现数据库重连逻辑
        return False
    
    async def _recover_discord_error(self, error: BotError, context):
        """Discord错误恢复策略"""
        logger.info("尝试Discord错误恢复...")
        return False
    
    # === 工具方法 ===
    
    async def _send_error_message(
        self, 
        message: str, 
        interaction: Optional[discord.Interaction],
        ctx: Optional[commands.Context],
        ephemeral: bool = True
    ):
        """发送错误消息"""
        try:
            if interaction:
                if not interaction.response.is_done():
                    await interaction.response.send_message(message, ephemeral=ephemeral)
                else:
                    await interaction.followup.send(message, ephemeral=ephemeral)
            elif ctx:
                await ctx.send(message)
        except Exception as e:
            logger.error(f"发送错误消息失败: {e}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计信息"""
        return self.error_stats.copy()
    
    def reset_error_stats(self):
        """重置错误统计"""
        self.error_stats.clear()
        logger.info("错误统计已重置")

# 全局错误处理器实例
error_handler = ErrorHandler()

# 便捷装饰器
def handle_errors(func):
    """错误处理装饰器"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # 尝试从参数中获取interaction或ctx
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
            raise  # 重新抛出异常以便上层处理
    
    return wrapper 