"""
基础命令系统框架
提供统一的命令注册、路由、权限管理、参数验证等功能
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import functools
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
import logging
import inspect
import os

# 获取日志器
logger = logging.getLogger(__name__)

class CommandCategory(Enum):
    """命令分类"""
    DICE = "dice"           # 骰子相关命令
    QUERY = "query"         # 查询相关命令
    COMBAT = "combat"       # 战斗相关命令
    CHARACTER = "character" # 角色相关命令
    ADMIN = "admin"         # 管理员命令
    UTILITY = "utility"     # 工具命令
    FUN = "fun"            # 娱乐命令

class PermissionLevel(Enum):
    """权限级别"""
    EVERYONE = 0      # 所有人
    REGISTERED = 1    # 已注册用户
    MODERATOR = 2     # 版主
    ADMIN = 3         # 管理员
    OWNER = 4         # 机器人所有者

class CommandInfo:
    """命令信息类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        category: CommandCategory,
        permission_level: PermissionLevel = PermissionLevel.EVERYONE,
        cooldown: Optional[float] = None,
        usage: Optional[str] = None,
        examples: Optional[List[str]] = None,
        enabled: bool = True
    ):
        self.name = name
        self.description = description
        self.category = category
        self.permission_level = permission_level
        self.cooldown = cooldown
        self.usage = usage
        self.examples = examples or []
        self.enabled = enabled
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_used: Optional[float] = None

class CommandRegistry:
    """命令注册器"""
    
    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.cooldowns: Dict[str, Dict[int, float]] = {}
        self.command_handlers: Dict[str, Callable] = {}
        self.permission_checkers: Dict[PermissionLevel, Callable] = {}
        
        # 注册默认权限检查器
        self._register_default_permission_checkers()
    
    def _register_default_permission_checkers(self):
        """注册默认权限检查器"""
        self.permission_checkers[PermissionLevel.EVERYONE] = self._check_everyone
        self.permission_checkers[PermissionLevel.REGISTERED] = self._check_registered
        self.permission_checkers[PermissionLevel.MODERATOR] = self._check_moderator
        self.permission_checkers[PermissionLevel.ADMIN] = self._check_admin
        self.permission_checkers[PermissionLevel.OWNER] = self._check_owner
    
    def register_command(
        self,
        name: str,
        description: str,
        category: CommandCategory,
        handler: Callable,
        permission_level: PermissionLevel = PermissionLevel.EVERYONE,
        cooldown: Optional[float] = None,
        usage: Optional[str] = None,
        examples: Optional[List[str]] = None
    ) -> CommandInfo:
        """注册命令"""
        
        command_info = CommandInfo(
            name=name,
            description=description,
            category=category,
            permission_level=permission_level,
            cooldown=cooldown,
            usage=usage,
            examples=examples
        )
        
        self.commands[name] = command_info
        self.command_handlers[name] = handler
        
        if cooldown:
            self.cooldowns[name] = {}
        
        logger.info(f"注册命令: {name} (分类: {category.value})")
        return command_info
    
    def get_command(self, name: str) -> Optional[CommandInfo]:
        """获取命令信息"""
        return self.commands.get(name)
    
    def get_commands_by_category(self, category: CommandCategory) -> List[CommandInfo]:
        """根据分类获取命令列表"""
        return [cmd for cmd in self.commands.values() if cmd.category == category]
    
    def get_all_commands(self) -> List[CommandInfo]:
        """获取所有命令"""
        return list(self.commands.values())
    
    async def check_permissions(
        self, 
        command_name: str, 
        user: Union[discord.User, discord.Member], 
        guild: Optional[discord.Guild] = None
    ) -> bool:
        """检查用户权限"""
        
        command_info = self.commands.get(command_name)
        if not command_info:
            return False
        
        if not command_info.enabled:
            return False
        
        permission_checker = self.permission_checkers.get(command_info.permission_level)
        if not permission_checker:
            logger.warning(f"未找到权限检查器: {command_info.permission_level}")
            return False
        
        try:
            return await permission_checker(user, guild)
        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False
    
    async def check_cooldown(self, command_name: str, user_id: int) -> Optional[float]:
        """检查命令冷却时间"""
        
        command_info = self.commands.get(command_name)
        if not command_info or not command_info.cooldown:
            return None
        
        user_cooldowns = self.cooldowns.get(command_name, {})
        last_used = user_cooldowns.get(user_id)
        
        if last_used is None:
            return None
        
        time_passed = time.time() - last_used
        if time_passed >= command_info.cooldown:
            return None
        
        return command_info.cooldown - time_passed
    
    def set_cooldown(self, command_name: str, user_id: int):
        """设置命令冷却时间"""
        if command_name in self.cooldowns:
            self.cooldowns[command_name][user_id] = time.time()
    
    def update_command_stats(self, command_name: str, execution_time: float):
        """更新命令统计"""
        command_info = self.commands.get(command_name)
        if command_info:
            command_info.execution_count += 1
            command_info.total_execution_time += execution_time
            command_info.last_used = time.time()
    
    # === 默认权限检查器 ===
    
    async def _check_everyone(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """所有人都可以使用"""
        return True
    
    async def _check_registered(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """已注册用户可以使用"""
        return True
    
    async def _check_moderator(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """版主可以使用"""
        if not guild:
            return False
        
        if isinstance(user, discord.Member):
            member = user
        else:
            member = guild.get_member(user.id)
        
        if not member:
            return False
        
        return member.guild_permissions.manage_messages
    
    async def _check_admin(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """管理员可以使用"""
        if not guild:
            return False
        
        if isinstance(user, discord.Member):
            member = user
        else:
            member = guild.get_member(user.id)
        
        if not member:
            return False
        
        return member.guild_permissions.administrator
    
    async def _check_owner(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """机器人所有者可以使用"""
        owner_id = os.getenv('OWNER_ID')
        if owner_id:
            return str(user.id) == owner_id
        return False

# 全局命令注册器
command_registry = CommandRegistry()

def command_route(
    name: str,
    description: str,
    category: CommandCategory,
    permission_level: PermissionLevel = PermissionLevel.EVERYONE,
    cooldown: Optional[float] = None,
    usage: Optional[str] = None,
    examples: Optional[List[str]] = None
):
    """命令路由装饰器"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            start_time = time.time()
            
            try:
                # 检查权限
                has_permission = await command_registry.check_permissions(
                    name, interaction.user, interaction.guild
                )
                
                if not has_permission:
                    await interaction.response.send_message(
                        "❌ 您没有使用此命令的权限", 
                        ephemeral=True
                    )
                    return
                
                # 检查冷却时间
                cooldown_remaining = await command_registry.check_cooldown(
                    name, interaction.user.id
                )
                
                if cooldown_remaining is not None:
                    await interaction.response.send_message(
                        f"❌ 命令冷却中，请等待 {cooldown_remaining:.1f} 秒后再试",
                        ephemeral=True
                    )
                    return
                
                # 设置冷却时间
                command_registry.set_cooldown(name, interaction.user.id)
                
                # 执行命令
                result = await func(interaction, *args, **kwargs)
                
                # 更新统计
                execution_time = time.time() - start_time
                command_registry.update_command_stats(name, execution_time)
                
                # 记录命令执行日志
                logger.info(
                    f"命令执行: {name}",
                    extra={
                        'command': name,
                        'user_id': interaction.user.id,
                        'guild_id': interaction.guild.id if interaction.guild else None,
                        'execution_time': execution_time * 1000
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                command_registry.update_command_stats(name, execution_time)
                
                logger.error(
                    f"命令执行失败: {name} - {str(e)}",
                    extra={
                        'command': name,
                        'user_id': interaction.user.id,
                        'guild_id': interaction.guild.id if interaction.guild else None,
                        'execution_time': execution_time * 1000,
                        'error': str(e)
                    }
                )
                
                # 重新抛出异常让错误处理器处理
                raise
        
        # 注册命令到注册器
        command_registry.register_command(
            name=name,
            description=description,
            category=category,
            handler=wrapper,
            permission_level=permission_level,
            cooldown=cooldown,
            usage=usage,
            examples=examples
        )
        
        return wrapper
    
    return decorator