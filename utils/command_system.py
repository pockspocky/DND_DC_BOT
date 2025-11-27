"""
Basic command system framework
Provides unified command registration, routing, permission management, parameter validation, and other features
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

# Get logger
logger = logging.getLogger(__name__)

class CommandCategory(Enum):
    """Command categories"""
    DICE = "dice"           # Dice-related commands
    QUERY = "query"         # Query-related commands
    COMBAT = "combat"       # Combat-related commands
    CHARACTER = "character" # Character-related commands
    ADMIN = "admin"         # Administrator commands
    UTILITY = "utility"     # Utility commands
    FUN = "fun"            # Fun commands

class PermissionLevel(Enum):
    """Permission levels"""
    EVERYONE = 0      # Everyone
    REGISTERED = 1    # Registered users
    MODERATOR = 2     # Moderators
    ADMIN = 3         # Administrators
    OWNER = 4         # Bot owner

class CommandInfo:
    """Command information class"""
    
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
    """Command registry"""
    
    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.cooldowns: Dict[str, Dict[int, float]] = {}
        self.command_handlers: Dict[str, Callable] = {}
        self.permission_checkers: Dict[PermissionLevel, Callable] = {}
        
        # Register default permission checkers
        self._register_default_permission_checkers()
    
    def _register_default_permission_checkers(self):
        """Register default permission checkers"""
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
        """Register command"""
        
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
        
        logger.info(f"Registered command: {name} (category: {category.value})")
        return command_info
    
    def get_command(self, name: str) -> Optional[CommandInfo]:
        """Get command information"""
        return self.commands.get(name)
    
    def get_commands_by_category(self, category: CommandCategory) -> List[CommandInfo]:
        """Get command list by category"""
        return [cmd for cmd in self.commands.values() if cmd.category == category]
    
    def get_all_commands(self) -> List[CommandInfo]:
        """Get all commands"""
        return list(self.commands.values())
    
    async def check_permissions(
        self, 
        command_name: str, 
        user: Union[discord.User, discord.Member], 
        guild: Optional[discord.Guild] = None
    ) -> bool:
        """Check user permissions"""
        
        command_info = self.commands.get(command_name)
        if not command_info:
            return False
        
        if not command_info.enabled:
            return False
        
        permission_checker = self.permission_checkers.get(command_info.permission_level)
        if not permission_checker:
            logger.warning(f"Permission checker not found: {command_info.permission_level}")
            return False
        
        try:
            return await permission_checker(user, guild)
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    async def check_cooldown(self, command_name: str, user_id: int) -> Optional[float]:
        """Check command cooldown"""
        
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
        """Set command cooldown"""
        if command_name in self.cooldowns:
            self.cooldowns[command_name][user_id] = time.time()
    
    def update_command_stats(self, command_name: str, execution_time: float):
        """Update command statistics"""
        command_info = self.commands.get(command_name)
        if command_info:
            command_info.execution_count += 1
            command_info.total_execution_time += execution_time
            command_info.last_used = time.time()
    
    # === Default permission checkers ===
    
    async def _check_everyone(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """Everyone can use"""
        return True
    
    async def _check_registered(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """Registered users can use"""
        return True
    
    async def _check_moderator(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild]) -> bool:
        """Moderators can use"""
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
        """Administrators can use"""
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
        """Bot owner can use"""
        owner_id = os.getenv('OWNER_ID')
        if owner_id:
            return str(user.id) == owner_id
        return False

# Global command registry
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
    """Command routing decorator"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            start_time = time.time()
            
            try:
                # Check permissions
                has_permission = await command_registry.check_permissions(
                    name, interaction.user, interaction.guild
                )
                
                if not has_permission:
                    await interaction.response.send_message(
                        "❌ You do not have permission to use this command", 
                        ephemeral=True
                    )
                    return
                
                # Check cooldown
                cooldown_remaining = await command_registry.check_cooldown(
                    name, interaction.user.id
                )
                
                if cooldown_remaining is not None:
                    await interaction.response.send_message(
                        f"❌ Command on cooldown, please wait {cooldown_remaining:.1f} seconds",
                        ephemeral=True
                    )
                    return
                
                # Set cooldown
                command_registry.set_cooldown(name, interaction.user.id)
                
                # Execute command
                result = await func(interaction, *args, **kwargs)
                
                # Update statistics
                execution_time = time.time() - start_time
                command_registry.update_command_stats(name, execution_time)
                
                # Log command execution
                logger.info(
                    f"Command executed: {name}",
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
                    f"Command execution failed: {name} - {str(e)}",
                    extra={
                        'command': name,
                        'user_id': interaction.user.id,
                        'guild_id': interaction.guild.id if interaction.guild else None,
                        'execution_time': execution_time * 1000,
                        'error': str(e)
                    }
                )
                
                # Re-raise exception for error handler to process
                raise
        
        # Register command to registry
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