#!/usr/bin/env python3
"""
DND Discord Bot - 龙与地下城机器人
主启动文件，负责机器人初始化和基础命令
整合了所有网络和SSL修复，可直接启动
"""

# === 网络和SSL修复配置 ===
# 在所有导入之前设置环境变量
import os
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# 设置代理环境变量
PROXY_URL = 'http://127.0.0.1:7890'
os.environ['HTTP_PROXY'] = PROXY_URL
os.environ['HTTPS_PROXY'] = PROXY_URL
os.environ['ALL_PROXY'] = PROXY_URL

# 强制禁用SSL验证
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 禁用SSL警告
import urllib3
urllib3.disable_warnings()

# 设置aiohttp连接参数
import aiohttp
import asyncio

# 创建自定义连接器配置
def create_connector():
    """创建优化的aiohttp连接器"""
    connector = aiohttp.TCPConnector(
        limit=100,  # 连接池大小
        limit_per_host=10,  # 每个主机的连接数
        ttl_dns_cache=300,  # DNS缓存时间
        use_dns_cache=True,
        ssl=False,  # 禁用SSL验证
        keepalive_timeout=30,  # 保持连接时间
        enable_cleanup_closed=True
    )
    return connector

# 显示启动信息
print("🔧 DND Discord Bot 启动")
print("✅ 所有SSL验证已禁用")
print("✅ 代理环境变量已设置")
print("✅ SSL上下文已设置为不验证")
print("🚀 启动机器人...")
print("=" * 50)

# === 主程序导入 ===
import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
from database import db_manager

# 导入新的工具系统
try:
    from utils import setup_logging, get_logger, error_handler
    UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Utils system not available: {e}")
    UTILS_AVAILABLE = False

# 环境变量和配置
load_dotenv()
# PROXY_URL已在文件开头设置

# 日志配置
if UTILS_AVAILABLE:
    # 使用新的专业日志系统
    setup_logging(
        log_level="INFO",
        log_dir="logs",
        enable_json=False,
        enable_console_color=True
    )
    logger = get_logger(__name__)
else:
    # 回退到基本日志配置
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
    """龙与地下城机器人主类"""
    
    def __init__(self):
        # 机器人权限配置
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        # 代理配置确认
        if PROXY_URL:
            print(f"为Discord连接准备代理设置: {PROXY_URL}")
            logger.info(f"使用代理: {PROXY_URL}")
        
        # 初始化机器人
        super().__init__(
            command_prefix=os.getenv('PREFIX', '!'),
            intents=intents,
            help_command=None,
            proxy=PROXY_URL  # discord.py WebSocket连接代理
        )
        
        # 强制设置HTTP客户端使用代理
        self._setup_http_client()
    
    def _setup_http_client(self):
        """设置HTTP客户端配置"""
        try:
            # 创建自定义连接器
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                ssl=False,  # 禁用SSL验证
                use_dns_cache=True,
                ttl_dns_cache=300,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
                force_close=False
            )
            
            # 创建客户端会话
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            # 如果使用代理，添加代理参数
            session_kwargs = {
                'connector': connector,
                'timeout': timeout,
                'trust_env': True,
                'headers': {
                    'User-Agent': 'DiscordBot (https://github.com/Rapptz/discord.py 2.3.2)'
                }
            }
            
            # 直接在session中设置代理
            if PROXY_URL:
                session_kwargs['proxy'] = PROXY_URL
            
            self._custom_session = aiohttp.ClientSession(**session_kwargs)
            
            logger.info("HTTP客户端配置完成")
            
        except Exception as e:
            logger.error(f"HTTP客户端配置失败: {e}")
    
    async def close(self):
        """关闭机器人时清理资源"""
        try:
            if hasattr(self, '_custom_session'):
                await self._custom_session.close()
        except:
            pass
        await super().close()
        
    async def setup_hook(self):
        """机器人启动时的初始化"""
        logger.info("正在设置机器人...")
        
        # 确保HTTP连接器也使用代理
        if PROXY_URL:
            logger.info(f"代理设置确认: {PROXY_URL}")
        
        # 初始化数据库
        await self._init_database()
        
        # 加载所有扩展
        await self._load_extensions()
        
        # 同步斜杠命令
        await self._sync_commands()
        
    async def _init_database(self):
        """初始化数据库连接"""
        try:
            await db_manager.connect()
            await db_manager.initialize_database()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _load_extensions(self):
        """加载所有扩展模块"""
        extensions = [
            'dice.dice_commands',
            'queries.query_commands',
            'combat.combat_commands'
        ]
        
        for ext in extensions:
            try:
                # 检查扩展是否已经加载
                if ext in self.extensions:
                    logger.info(f"{ext}扩展已存在，跳过加载")
                    continue
                
                await self.load_extension(ext)
                logger.info(f"{ext}扩展已加载")
            except Exception as e:
                logger.error(f"加载{ext}扩展失败: {e}")
    
    async def _sync_commands(self):
        """同步斜杠命令到Discord"""
        try:
            # 检查是否已经同步过
            if hasattr(self, '_commands_synced') and self._commands_synced:
                logger.info("斜杠命令已经同步过，跳过")
                return
            
            synced = await self.tree.sync()
            logger.info(f"已同步 {len(synced)} 个斜杠命令")
            self._commands_synced = True
        except Exception as e:
            logger.error(f"同步斜杠命令失败: {e}")
        
    async def on_ready(self):
        """机器人就绪回调"""
        if not self.user:
            logger.error("机器人用户对象为None")
            return
            
        logger.info(f'{self.user} 已成功登录!')
        logger.info(f'机器人ID: {self.user.id}')
        logger.info(f'连接到 {len(self.guilds)} 个服务器')
        
        # 代理连接成功提示
        if PROXY_URL:
            logger.info("Discord连接成功，代理设置工作正常")
        
        # 同步服务器信息
        await self._sync_guilds()
        
        # 设置机器人状态
        await self.change_presence(
            activity=discord.Game(name="龙与地下城 | /help"),
            status=discord.Status.online
        )
        
        # 显示数据库统计
        await self._show_database_stats()
    
    async def _sync_guilds(self):
        """同步服务器信息到数据库"""
        for guild in self.guilds:
            try:
                await db_manager.create_or_update_guild(guild.id, guild.name)
                logger.info(f"已同步服务器: {guild.name}")
            except Exception as e:
                logger.error(f"同步服务器失败 {guild.name}: {e}")
    
    async def _show_database_stats(self):
        """显示数据库统计信息"""
        try:
            stats = await db_manager.get_database_stats()
            logger.info(f"数据库统计: {stats}")
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
    
    async def on_guild_join(self, guild):
        """机器人加入新服务器"""
        try:
            await db_manager.create_or_update_guild(guild.id, guild.name)
            logger.info(f"已加入新服务器: {guild.name}")
        except Exception as e:
            logger.error(f"处理新服务器失败: {e}")
    
    async def on_interaction(self, interaction):
        """处理交互事件（用户信息同步）"""
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
                logger.error(f"更新用户信息失败: {e}")
        
    async def on_command_error(self, ctx, error):
        """命令错误处理"""
        error_messages = {
            commands.CommandNotFound: f"❌ 未找到命令 `{ctx.invoked_with}`，使用 `!help` 查看可用命令",
            commands.MissingRequiredArgument: f"❌ 缺少必需参数: `{error.param.name}`",
            commands.BadArgument: f"❌ 参数错误: {error}"
        }
        
        message = error_messages.get(type(error), "❌ 执行命令时发生错误，请稍后再试")
        await ctx.send(message)
        
        if type(error) not in error_messages:
            logger.error(f"命令错误: {error}")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """应用命令错误处理"""
        if UTILS_AVAILABLE:
            # 使用新的错误处理系统
            try:
                await error_handler.handle_error(error, interaction=interaction)
            except Exception as handler_error:
                logger.error(f"错误处理器失败: {handler_error}")
                # 回退到基本错误处理
                await self._basic_error_handling(interaction, error)
        else:
            # 回退到基本错误处理
            await self._basic_error_handling(interaction, error)
    
    async def _basic_error_handling(self, interaction: discord.Interaction, error: Exception):
        """基本错误处理（回退方案）"""
        logger.error(f"应用命令错误: {error}")
        
        # 根据错误类型给出不同的提示
        error_str = str(error).lower()
        if "ssl" in error_str or "clientconnectorerror" in error_str:
            error_msg = "❌ 网络连接问题，请稍后重试"
        elif "connection reset" in error_str:
            error_msg = "❌ 连接被重置，请稍后重试"
        elif "unknown interaction" in error_str:
            error_msg = "❌ 交互超时，请重新尝试命令"
        elif "timeout" in error_str:
            error_msg = "❌ 请求超时，请稍后重试"
        else:
            error_msg = "❌ 命令执行失败，请稍后重试"
        
        # 尝试发送错误消息，包含多重保护
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
            logger.error("发送错误消息超时")
        except Exception as e:
            logger.error(f"发送错误消息失败: {e}")

# 创建机器人实例
bot = DNDBot()

# 通用命令保护装饰器
def command_protection(func):
    """为命令添加超时和错误保护"""
    async def wrapper(interaction: discord.Interaction, *args, **kwargs):
        try:
            # 立即确认交互，避免超时
            if not interaction.response.is_done():
                await interaction.response.defer(thinking=True)
            
            # 执行实际命令，添加超时保护
            await asyncio.wait_for(
                func(interaction, *args, **kwargs),
                timeout=15.0
            )
            
        except asyncio.TimeoutError:
            logger.error(f"命令 {func.__name__} 响应超时")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ 响应超时，请重试", ephemeral=True)
                else:
                    await interaction.followup.send("❌ 响应超时，请重试", ephemeral=True)
            except:
                pass
        except Exception as e:
            logger.error(f"命令 {func.__name__} 失败: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ 命令执行失败，请稍后重试", ephemeral=True)
                else:
                    await interaction.followup.send("❌ 命令执行失败，请稍后重试", ephemeral=True)
            except:
                pass
    
    return wrapper

# === 基础斜杠命令 ===

@bot.tree.command(name='ping', description='测试机器人响应和延迟')
async def ping(interaction: discord.Interaction):
    """测试机器人响应"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! 延迟: {latency}ms')

@bot.tree.command(name='help', description='显示机器人帮助信息')
async def help_command(interaction: discord.Interaction):
    """显示帮助信息"""
    try:
        # 立即确认交互，避免超时
        await interaction.response.defer(thinking=True)
        
        embed = discord.Embed(
            title="🎲 DND Discord Bot 帮助",
            description="龙与地下城Discord机器人命令列表",
            color=discord.Color.blue()
        )
        
        # 基础命令
        embed.add_field(
            name="📋 基础命令",
            value=(
                "`/ping` - 测试机器人响应\n"
                "`/help` - 显示此帮助信息\n"
                "`/echo <消息>` - 重复您的消息\n"
                "`/dbstats` - 显示数据库统计信息"
            ),
            inline=False
        )
        
        # 骰子系统
        embed.add_field(
            name="🎲 骰子系统",
            value=(
                "`/r` - 投掷骰子 (支持多种参数)\n"
                "`/check <修正值>` - 技能检定\n"
                "`/save <类型> <修正值>` - 豁免检定\n"
                "`/att <加值> <伤害骰>` - 攻击检定\n"
                "`/stats` - 生成角色属性\n"
                "`/rh` - 骰子详细帮助"
            ),
            inline=False
        )
        
        # 查询功能
        embed.add_field(
            name="🔍 查询功能",
            value=(
                "`/sp <法术名>` - 查询D&D 5e法术信息\n"
                "`/mon <怪物名>` - 查询怪物属性和能力\n"
                "`/sk <技能名>` - 查询技能详细说明"
            ),
            inline=False
        )
        
        # 战斗系统
        embed.add_field(
            name="⚔️ 战斗系统",
            value=(
                "`/cs <名称>` - 开始新战斗\n"
                "`/ce` - 结束当前战斗\n"
                "`/st` - 查看战斗状态\n"
                "`/add <角色>` - 添加参与者\n"
                "`/rm <角色>` - 移除参与者\n"
                "`/next` - 下一个回合\n"
                "`/dmg <目标> <伤害>` - 造成伤害\n"
                "`/heal <目标> <治疗>` - 治疗角色"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 使用提示",
            value=(
                "• 所有命令都支持Discord的斜杠命令自动补全\n"
                "• 查询命令请使用英文名称\n"
                "• 骰子命令支持复杂的参数组合\n"
                "• 战斗系统需要DM权限或管理员权限\n"
                "• 使用 `/rh` 查看详细的骰子用法"
            ),
            inline=False
        )
        
        embed.set_footer(text="DND Discord Bot | 让您的龙与地下城游戏更精彩")
        
        # 使用followup发送，添加超时保护
        await asyncio.wait_for(
            interaction.followup.send(embed=embed),
            timeout=10.0
        )
        
    except asyncio.TimeoutError:
        logger.error("Help命令响应超时")
        try:
            await interaction.followup.send("❌ 响应超时，请重试", ephemeral=True)
        except:
            pass
    except Exception as e:
        logger.error(f"Help命令失败: {e}")
        try:
            await interaction.followup.send("❌ 获取帮助信息失败，请稍后重试", ephemeral=True)
        except:
            pass

@bot.tree.command(name='echo', description='重复您输入的消息')
@app_commands.describe(message='要重复的消息内容')
async def echo(interaction: discord.Interaction, message: str):
    """重复消息"""
    await interaction.response.send_message(f'📢 {message}')

@bot.tree.command(name='dbstats', description='显示数据库统计信息')
async def database_stats(interaction: discord.Interaction):
    """显示数据库统计"""
    try:
        # 立即确认交互，避免超时
        await interaction.response.defer(thinking=True)
        
        stats = await asyncio.wait_for(
            db_manager.get_database_stats(),
            timeout=10.0
        )
        
        embed = discord.Embed(
            title="📊 数据库统计",
            description="当前数据库使用情况",
            color=discord.Color.green()
        )
        
        # 用户和服务器统计
        embed.add_field(
            name="用户与服务器",
            value=f"**用户**: {stats.get('users', 0)}\n**服务器**: {stats.get('guilds', 0)}",
            inline=True
        )
        
        # 游戏数据统计
        embed.add_field(
            name="游戏数据",
            value=(
                f"**角色**: {stats.get('characters', 0)}\n"
                f"**装备**: {stats.get('equipment', 0)}\n"
                f"**战斗**: {stats.get('combat_sessions', 0)}"
            ),
            inline=True
        )
        
        # 投掷和查询统计
        embed.add_field(
            name="活动统计",
            value=(
                f"**投掷记录**: {stats.get('dice_history', 0)}\n"
                f"**法术查询**: {stats.get('spells', 0)}\n"
                f"**怪物查询**: {stats.get('monsters', 0)}"
            ),
            inline=True
        )
        
        await asyncio.wait_for(
            interaction.followup.send(embed=embed),
            timeout=10.0
        )
        
    except asyncio.TimeoutError:
        logger.error("数据库统计命令响应超时")
        try:
            await interaction.followup.send("❌ 获取数据库统计超时，请重试", ephemeral=True)
        except:
            pass
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        try:
            await interaction.followup.send("❌ 获取数据库统计失败，请稍后再试", ephemeral=True)
        except:
            pass

# === 开发者命令 ===

@bot.command(name='sync')
@commands.is_owner()
async def sync(ctx):
    """同步斜杠命令（仅所有者）"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ 已同步 {len(synced)} 个斜杠命令")
    except Exception as e:
        await ctx.send(f"❌ 同步失败: {e}")

@bot.command(name='forcesync')
@commands.is_owner()
async def force_sync(ctx):
    """强制同步斜杠命令（仅所有者）"""
    try:
        bot.tree.clear_commands(guild=None)
        synced = await bot.tree.sync()
        await ctx.send(f"✅ 已强制同步 {len(synced)} 个斜杠命令")
    except Exception as e:
        await ctx.send(f"❌ 强制同步失败: {e}")

# === 启动机器人 ===

async def main():
    """主启动函数"""
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("未找到DISCORD_TOKEN环境变量")
        return
    
    # 启动重试机制
    max_retries = 3
    retry_delay = 5
    current_bot = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试启动机器人 (尝试 {attempt + 1}/{max_retries})")
            
            # 检查网络连接
            await check_network_connection()
            
            # 如果不是第一次尝试，创建新的机器人实例
            if attempt > 0:
                logger.info("创建新的机器人实例...")
                current_bot = DNDBot()
            else:
                current_bot = bot
            
            # 启动机器人
            await current_bot.start(token)
            break  # 成功启动，退出重试循环
            
        except aiohttp.ClientConnectorError as e:
            logger.error(f"网络连接错误: {e}")
            if "ssl" in str(e).lower():
                logger.error("SSL连接问题，建议使用Docker部署")
                print("❌ SSL连接问题，建议使用Docker部署：")
                print("   ./deploy-docker.sh")
            
            # 清理当前机器人实例
            if current_bot:
                try:
                    await current_bot.close()
                except:
                    pass
            
            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("所有重试均失败，建议检查网络连接和代理设置")
                break
                
        except Exception as e:
            logger.error(f"启动机器人时发生错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 清理当前机器人实例
            if current_bot:
                try:
                    await current_bot.close()
                except:
                    pass
            
            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("所有重试均失败")
                break
    
    # 清理资源
    try:
        await db_manager.disconnect()
    except Exception as e:
        logger.error(f"清理数据库连接时出错: {e}")
    
    if current_bot:
        try:
            await current_bot.close()
        except Exception as e:
            logger.error(f"关闭机器人时出错: {e}")

async def check_network_connection():
    """检查网络连接"""
    try:
        logger.info("检查网络连接...")
        
        # 测试代理连接
        if PROXY_URL:
            logger.info(f"使用代理: {PROXY_URL}")
            
            # 创建带代理的会话
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(
                proxy=PROXY_URL,
                timeout=timeout,
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get('https://httpbin.org/ip') as response:
                    if response.status == 200:
                        logger.info("代理连接正常")
                    else:
                        logger.warning(f"代理连接响应: {response.status}")
        
        logger.info("网络连接检查完成")
        
    except Exception as e:
        logger.warning(f"网络连接检查失败: {e}")
        logger.info("但这不影响机器人启动，继续尝试...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
