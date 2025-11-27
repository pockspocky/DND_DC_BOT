#!/usr/bin/env python3
"""
DND Discord Bot - Dungeons & Dragons Bot
Main startup file responsible for bot initialization and basic commands
"""

import os
import aiohttp
import asyncio

# === Main Program Imports ===
import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
from database import db_manager
from scene_generator import scene_generator

# Import new utility system
try:
    from utils import setup_logging, get_logger, error_handler
    UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Utils system not available: {e}")
    UTILS_AVAILABLE = False

# Environment variables and configuration
load_dotenv()

# Logging configuration
if UTILS_AVAILABLE:
    # Use new professional logging system
    setup_logging(
        log_level="INFO",
        log_dir="logs",
        enable_json=False,
        enable_console_color=True
    )
    logger = get_logger(__name__)
else:
    # Fallback to basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

class DNDBot(commands.Bot):
    """Dungeons & Dragons Bot main class"""
    
    def __init__(self):
        # Bot permissions configuration
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        # Initialize bot
        super().__init__(
            command_prefix=os.getenv('PREFIX', '!'),
            intents=intents,
            help_command=None
        )
        
        # Set up HTTP client
        self._setup_http_client()
    
    def _setup_http_client(self):
        """Set up HTTP client configuration"""
        try:
            # Create connector with standard SSL verification
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                use_dns_cache=True,
                ttl_dns_cache=300,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
                force_close=False
            )
            
            # Create client session with standard settings
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self._custom_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=True,
                headers={
                    'User-Agent': 'DiscordBot (https://github.com/Rapptz/discord.py 2.3.2)'
                }
            )
            
            logger.info("HTTP client configuration complete")
            
        except Exception as e:
            logger.error(f"HTTP client configuration failed: {e}")
    
    async def close(self):
        """Clean up resources when closing bot"""
        try:
            if hasattr(self, '_custom_session'):
                await self._custom_session.close()
        except:
            pass
        await super().close()
        
    async def setup_hook(self):
        """Initialization when bot starts"""
        logger.info("Setting up bot...")
        
        # Initialize database
        await self._init_database()
        
        # Load all extensions
        await self._load_extensions()
        
        # Sync slash commands
        await self._sync_commands()
        
    async def _init_database(self):
        """Initialize database connection"""
        try:
            await db_manager.connect()
            await db_manager.initialize_database()
            logger.info("Database initialization complete")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _load_extensions(self):
        """Load all extension modules"""
        extensions = [
            'dice.dice_commands',
            'queries.query_commands',
            'combat.combat_commands'
        ]
        
        for ext in extensions:
            try:
                # Check if extension is already loaded
                if ext in self.extensions:
                    logger.info(f"{ext} extension already exists, skipping load")
                    continue
                
                await self.load_extension(ext)
                logger.info(f"{ext} extension loaded")
            except Exception as e:
                logger.error(f"Failed to load {ext} extension: {e}")
    
    async def _sync_commands(self):
        """Sync slash commands to Discord"""
        try:
            # Check if already synced
            if hasattr(self, '_commands_synced') and self._commands_synced:
                logger.info("Slash commands already synced, skipping")
                return
            
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
            self._commands_synced = True
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        
    async def on_ready(self):
        """Bot ready callback"""
        if not self.user:
            logger.error("Bot user object is None")
            return
            
        logger.info(f'{self.user} logged in successfully!')
        logger.info(f'Bot ID: {self.user.id}')
        logger.info(f'Connected to {len(self.guilds)} servers')
        
        # Sync server information
        await self._sync_guilds()
        
        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="Dungeons & Dragons | /help"),
            status=discord.Status.online
        )
        
        # Display database statistics
        await self._show_database_stats()
    
    async def _sync_guilds(self):
        """Sync server information to database"""
        for guild in self.guilds:
            try:
                await db_manager.create_or_update_guild(guild.id, guild.name)
                logger.info(f"Synced server: {guild.name}")
            except Exception as e:
                logger.error(f"Failed to sync server {guild.name}: {e}")
    
    async def _show_database_stats(self):
        """Display database statistics"""
        try:
            stats = await db_manager.get_database_stats()
            logger.info(f"Database statistics: {stats}")
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
    
    async def on_guild_join(self, guild):
        """Bot joins new server"""
        try:
            await db_manager.create_or_update_guild(guild.id, guild.name)
            logger.info(f"Joined new server: {guild.name}")
        except Exception as e:
            logger.error(f"Failed to process new server: {e}")
    
    async def on_interaction(self, interaction):
        """Handle interaction events (user information sync)"""
        if interaction.type == discord.InteractionType.application_command:
            try:
                user = interaction.user
                await db_manager.create_or_update_user(
                    user.id, 
                    user.name,
                    user.discriminator,
                    str(user.display_avatar.url) if user.display_avatar else ""
                )
            except Exception as e:
                logger.error(f"Failed to update user information: {e}")
        
    async def on_command_error(self, ctx, error):
        """Command error handling"""
        error_messages = {
            commands.CommandNotFound: f"❌ Command `{ctx.invoked_with}` not found, use `!help` to see available commands",
            commands.MissingRequiredArgument: f"❌ Missing required argument: `{error.param.name}`",
            commands.BadArgument: f"❌ Invalid argument: {error}"
        }
        
        message = error_messages.get(type(error), "❌ An error occurred while executing the command, please try again later")
        await ctx.send(message)
        
        if type(error) not in error_messages:
            logger.error(f"Command error: {error}")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Application command error handling"""
        if UTILS_AVAILABLE:
            # Use new error handling system
            try:
                await error_handler.handle_error(error, interaction=interaction)
            except Exception as handler_error:
                logger.error(f"Error handler failed: {handler_error}")
                # Fallback to basic error handling
                await self._basic_error_handling(interaction, error)
        else:
            # Fallback to basic error handling
            await self._basic_error_handling(interaction, error)
    
    async def _basic_error_handling(self, interaction: discord.Interaction, error: Exception):
        """Basic error handling (fallback)"""
        logger.error(f"Application command error: {error}")
        
        # Provide different messages based on error type
        error_str = str(error).lower()
        if "ssl" in error_str or "clientconnectorerror" in error_str:
            error_msg = "❌ Network connection issue, please try again later"
        elif "connection reset" in error_str:
            error_msg = "❌ Connection reset, please try again later"
        elif "unknown interaction" in error_str:
            error_msg = "❌ Interaction timeout, please try the command again"
        elif "timeout" in error_str:
            error_msg = "❌ Request timeout, please try again later"
        else:
            error_msg = "❌ Command execution failed, please try again later"
        
        # Try to send error message with multiple protections
        try:
            if not interaction.response.is_done():
                await asyncio.wait_for(
                    interaction.response.send_message(error_msg, ephemeral=True),
                    timeout=5.0
                )
            else:
                await asyncio.wait_for(
                    interaction.followup.send(error_msg, ephemeral=True),
                    timeout=5.0
                )
        except asyncio.TimeoutError:
            logger.error("Sending error message timed out")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

# Create bot instance
bot = DNDBot()

# Universal command protection decorator
def command_protection(func):
    """Add timeout and error protection to commands"""
    async def wrapper(interaction: discord.Interaction, *args, **kwargs):
        try:
            # Immediately acknowledge interaction to avoid timeout
            if not interaction.response.is_done():
                await interaction.response.defer(thinking=True)
            
            # Execute actual command with timeout protection
            await asyncio.wait_for(
                func(interaction, *args, **kwargs),
                timeout=15.0
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Command {func.__name__} response timeout")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Response timeout, please try again", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Response timeout, please try again", ephemeral=True)
            except:
                pass
        except Exception as e:
            logger.error(f"Command {func.__name__} failed: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Command execution failed, please try again later", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Command execution failed, please try again later", ephemeral=True)
            except:
                pass
    
    return wrapper

# === Basic Slash Commands ===

@bot.tree.command(name='ping', description='Test bot response and latency')
async def ping(interaction: discord.Interaction):
    """Test bot response"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

@bot.tree.command(name='help', description='Display bot help information')
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    try:
        # Immediately acknowledge interaction to avoid timeout
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🎲 DND Discord Bot Help",
            description="Dungeons & Dragons Discord Bot Command List",
            color=discord.Color.blue()
        )
        
        # Basic commands
        embed.add_field(
            name="📋 Basic Commands",
            value=(
                "`/ping` - Test bot response\n"
                "`/help` - Display this help information\n"
                "`/echo <message>` - Repeat your message\n"
                "`/dbstats` - Display database statistics"
            ),
            inline=False
        )
        
        # Dice system
        embed.add_field(
            name="🎲 Dice System",
            value=(
                "`/r` - Roll dice (supports multiple parameters)\n"
                "`/check <modifier>` - Skill check\n"
                "`/save <type> <modifier>` - Saving throw\n"
                "`/att <bonus> <damage dice>` - Attack roll\n"
                "`/stats` - Generate character stats\n"
                "`/rh` - Detailed dice help"
            ),
            inline=False
        )
        
        # Query features
        embed.add_field(
            name="🔍 Query Features",
            value=(
                "`/sp <spell name>` - Query D&D 5e spell information\n"
                "`/mon <monster name>` - Query monster stats and abilities\n"
                "`/sk <skill name>` - Query skill detailed description"
            ),
            inline=False
        )
        
        # Combat system
        embed.add_field(
            name="⚔️ Combat System",
            value=(
                "`/cs <name>` - Start new combat\n"
                "`/ce` - End current combat\n"
                "`/st` - View combat status\n"
                "`/add <character>` - Add participant\n"
                "`/rm <character>` - Remove participant\n"
                "`/next` - Next turn\n"
                "`/dmg <target> <damage>` - Deal damage\n"
                "`/heal <target> <healing>` - Heal character"
            ),
            inline=False
        )
        
        # DM tools
        embed.add_field(
            name="🎭 DM Tools",
            value=(
                "`/scene <description>` - Generate scene description\n"
                "• Supports custom length (50-500 characters)\n"
                "• Supports any style keywords\n"
                "• Common styles: descriptive, mysterious, tense, horror, romantic, humorous, epic, etc.\n"
                "• Or enter custom style keywords"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Usage Tips",
            value=(
                "• All commands support Discord slash command auto-completion\n"
                "• Query commands use English names\n"
                "• Dice commands support complex parameter combinations\n"
                "• Combat system requires DM permissions or administrator permissions\n"
                "• Scene generation supports any style keywords (e.g., poetic, sad, passionate, etc.)\n"
                "• Use `/rh` to view detailed dice usage"
            ),
            inline=False
        )
        
        embed.set_footer(text="DND Discord Bot | Make your Dungeons & Dragons game more exciting")
        
        # Send using followup with timeout protection
        await asyncio.wait_for(
            interaction.followup.send(embed=embed),
            timeout=10.0
        )
        
    except asyncio.TimeoutError:
        logger.error("Help command response timeout")
        try:
            await interaction.followup.send("❌ Response timeout, please try again", ephemeral=True)
        except:
            pass
    except Exception as e:
        logger.error(f"Help command failed: {e}")
        try:
            await interaction.followup.send("❌ Failed to get help information, please try again later", ephemeral=True)
        except:
            pass

@bot.tree.command(name='echo', description='Repeat your input message')
@app_commands.describe(message='Message content to repeat')
async def echo(interaction: discord.Interaction, message: str):
    """Repeat message"""
    await interaction.response.send_message(f'📢 {message}')

@bot.tree.command(name='scene', description='Generate D&D scene description')
@app_commands.describe(
    description='English scene description',
    length='Description length (characters, 50-500)',
    style='Description style (supports any style keywords, e.g., mysterious, horror, romantic, humorous, etc.)'
)
async def generate_scene(
    interaction: discord.Interaction, 
    description: str,
    length: int = 100,
    style: str = "descriptive"
):
    """Generate D&D scene description"""
    try:
        # Immediately acknowledge interaction to avoid timeout
        await interaction.response.defer()
        
        # Validate parameters
        if not description.strip():
            await interaction.followup.send("❌ Please provide a scene description", ephemeral=True)
            return
        
        if length < 50 or length > 500:
            await interaction.followup.send("❌ Length must be between 50-500 characters", ephemeral=True)
            return
        
        # Validate style input (allow any style keywords)
        if not style or len(style.strip()) == 0:
            await interaction.followup.send("❌ Please provide a valid style description", ephemeral=True)
            return
        
        if len(style.strip()) > 20:
            await interaction.followup.send("❌ Style description cannot exceed 20 characters", ephemeral=True)
            return
        
        # Generate scene description
        scene_description = await scene_generator.generate_scene_description(
            description, length, style
        )
        
        if scene_description:
            # Create beautiful embed message
            embed = discord.Embed(
                title="🎭 D&D Scene Description",
                description=scene_description,
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="📝 Original Description",
                value=description,
                inline=False
            )
            
            embed.add_field(
                name="⚙️ Generation Settings",
                value=f"**Length**: {length} chars **Style**: {style}\n**Actual Length**: {len(scene_description)} chars",
                inline=False
            )
            
            embed.set_footer(text="🎲 DM Tools | Generated by AI")
            
            # Send result
            await interaction.followup.send(embed=embed)
            
            logger.info(f"User {interaction.user} generated scene description: {description[:50]}...")
            
        else:
            await interaction.followup.send("❌ Scene description generation failed, please try again later", ephemeral=True)
            
    except asyncio.TimeoutError:
        logger.error("Scene generation command response timeout")
        try:
            await interaction.followup.send("❌ Scene description generation timeout, please try again", ephemeral=True)
        except:
            pass
    except Exception as e:
        logger.error(f"Scene generation command failed: {e}")
        try:
            await interaction.followup.send("❌ Scene description generation failed, please try again later", ephemeral=True)
        except:
            pass

@bot.tree.command(name='dbstats', description='Display database statistics')
async def database_stats(interaction: discord.Interaction):
    """Display database statistics"""
    try:
        # Immediately acknowledge interaction to avoid timeout
        await interaction.response.defer()
        
        stats = await asyncio.wait_for(
            db_manager.get_database_stats(),
            timeout=10.0
        )
        
        embed = discord.Embed(
            title="📊 Database Statistics",
            description="Current database usage",
            color=discord.Color.green()
        )
        
        # User and server statistics
        embed.add_field(
            name="Users & Servers",
            value=f"**Users**: {stats.get('users', 0)}\n**Servers**: {stats.get('guilds', 0)}",
            inline=True
        )
        
        # Game data statistics
        embed.add_field(
            name="Game Data",
            value=(
                f"**Characters**: {stats.get('characters', 0)}\n"
                f"**Equipment**: {stats.get('equipment', 0)}\n"
                f"**Combat Sessions**: {stats.get('combat_sessions', 0)}"
            ),
            inline=True
        )
        
        # Roll and query statistics
        embed.add_field(
            name="Activity Statistics",
            value=(
                f"**Roll History**: {stats.get('dice_history', 0)}\n"
                f"**Spell Queries**: {stats.get('spells', 0)}\n"
                f"**Monster Queries**: {stats.get('monsters', 0)}"
            ),
            inline=True
        )
        
        await asyncio.wait_for(
            interaction.followup.send(embed=embed),
            timeout=10.0
        )
        
    except asyncio.TimeoutError:
        logger.error("Database statistics command response timeout")
        try:
            await interaction.followup.send("❌ Database statistics retrieval timeout, please try again", ephemeral=True)
        except:
            pass
    except Exception as e:
        logger.error(f"Failed to get database statistics: {e}")
        try:
            await interaction.followup.send("❌ Failed to get database statistics, please try again later", ephemeral=True)
        except:
            pass

# === Developer Commands ===

@bot.command(name='sync')
@commands.is_owner()
async def sync(ctx):
    """Sync slash commands (owner only)"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

@bot.command(name='forcesync')
@commands.is_owner()
async def force_sync(ctx):
    """Force sync slash commands (owner only)"""
    try:
        bot.tree.clear_commands(guild=None)
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Force synced {len(synced)} slash commands")
    except Exception as e:
        await ctx.send(f"❌ Force sync failed: {e}")

# === Start Bot ===

async def main():
    """Main startup function"""
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("DISCORD_TOKEN environment variable not found")
        return
    
    # Startup retry mechanism
    max_retries = 3
    retry_delay = 5
    current_bot = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to start bot (attempt {attempt + 1}/{max_retries})")
            
            # If not first attempt, create new bot instance
            if attempt > 0:
                logger.info("Creating new bot instance...")
                current_bot = DNDBot()
            else:
                current_bot = bot
            
            # Start bot
            await current_bot.start(token)
            break  # Successfully started, exit retry loop
            
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Network connection error: {e}")
            if "ssl" in str(e).lower():
                logger.error("SSL connection issue, Docker deployment recommended")
                print("❌ SSL connection issue, Docker deployment recommended:")
                print("   ./deploy-docker.sh")
            
            # Clean up current bot instance
            if current_bot:
                try:
                    await current_bot.close()
                except:
                    pass
            
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("All retries failed, please check network connection")
                break
                
        except Exception as e:
            logger.error(f"Error occurred while starting bot: {e}")
            import traceback
            traceback.print_exc()
            
            # Clean up current bot instance
            if current_bot:
                try:
                    await current_bot.close()
                except:
                    pass
            
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("All retries failed")
                break
    
    # Clean up resources
    try:
        await db_manager.disconnect()
    except Exception as e:
        logger.error(f"Error cleaning up database connection: {e}")
    
    if current_bot:
        try:
            await current_bot.close()
        except Exception as e:
            logger.error(f"Error closing bot: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
