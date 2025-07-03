import discord
from discord.ext import commands
from discord import app_commands
import os
import logging
from dotenv import load_dotenv
import aiohttp
from database import db_manager

# 加载环境变量
load_dotenv()

# 代理配置（如果需要）
PROXY_URL = os.getenv('PROXY_URL')  # 例如: http://127.0.0.1:7890

# 备份和管理代理设置
original_http_proxy = os.environ.get('HTTP_PROXY')
original_https_proxy = os.environ.get('HTTPS_PROXY')

# 如果设置了代理，为Discord连接配置环境变量
if PROXY_URL:
    os.environ['HTTP_PROXY'] = PROXY_URL
    os.environ['HTTPS_PROXY'] = PROXY_URL
    print(f"为Discord连接设置代理环境变量: {PROXY_URL}")  # 使用print，logger还未配置

# 配置日志
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
    """龙与地下城Discord机器人主类"""
    
    def __init__(self):
        # 设置机器人意图
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        # 记录代理配置
        if PROXY_URL:
            logger.info(f"使用代理: {PROXY_URL}")
        
        # 初始化机器人
        super().__init__(
            command_prefix=os.getenv('PREFIX', '!'),
            intents=intents,
            help_command=None,  # 禁用默认帮助命令，后续自定义
            proxy=PROXY_URL if PROXY_URL else None
        )
        
    async def setup_hook(self):
        """机器人启动时的初始化设置"""
        logger.info("正在设置机器人...")
        
        # 初始化数据库
        try:
            await db_manager.connect()
            await db_manager.initialize_database()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
        
        # 加载骰子命令扩展
        try:
            await self.load_extension('dice.dice_commands')
            logger.info("骰子命令扩展已加载")
        except Exception as e:
            logger.error(f"加载骰子命令扩展失败: {e}")
        
        # 加载查询命令扩展
        try:
            await self.load_extension('queries.query_commands')
            logger.info("查询命令扩展已加载")
        except Exception as e:
            logger.error(f"加载查询命令扩展失败: {e}")
        
        # 同步斜杠命令到Discord
        try:
            synced = await self.tree.sync()
            logger.info(f"已同步 {len(synced)} 个斜杠命令")
        except Exception as e:
            logger.error(f"同步斜杠命令失败: {e}")
        
        # 这里后续会添加加载其他扩展
        
    async def on_ready(self):
        """机器人准备就绪时的回调"""
        if self.user is None:
            logger.error("机器人用户对象为None，可能连接未完全建立")
            return
            
        logger.info(f'{self.user} 已成功登录!')
        logger.info(f'机器人ID: {self.user.id}')
        logger.info(f'连接到 {len(self.guilds)} 个服务器')
        
        # Discord连接成功后，清理全局代理设置（避免影响D&D API）
        if PROXY_URL and os.environ.get('HTTP_PROXY'):
            logger.info("Discord连接成功，清理全局代理设置以优化D&D API连接")
            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']
        
        # 同步所有服务器到数据库
        for guild in self.guilds:
            try:
                await db_manager.create_or_update_guild(guild.id, guild.name)
                logger.info(f"已同步服务器: {guild.name}")
            except Exception as e:
                logger.error(f"同步服务器失败 {guild.name}: {e}")
        
        # 设置机器人状态
        await self.change_presence(
            activity=discord.Game(name="龙与地下城 | /help"),
            status=discord.Status.online
        )
        
        # 输出数据库统计信息
        try:
            stats = await db_manager.get_database_stats()
            logger.info(f"数据库统计: {stats}")
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
    
    async def on_guild_join(self, guild):
        """机器人加入新服务器时的回调"""
        try:
            await db_manager.create_or_update_guild(guild.id, guild.name)
            logger.info(f"已加入新服务器: {guild.name}")
        except Exception as e:
            logger.error(f"处理新服务器失败: {e}")
    
    async def on_interaction(self, interaction):
        """处理交互事件（斜杠命令）"""
        if interaction.type == discord.InteractionType.application_command:
            # 确保用户在数据库中
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
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ 未找到命令 `{ctx.invoked_with}`，使用 `!help` 查看可用命令")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ 缺少必需参数: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ 参数错误: {error}")
        else:
            logger.error(f"命令错误: {error}")
            await ctx.send("❌ 执行命令时发生错误，请稍后再试")

# 创建机器人实例
bot = DNDBot()

# 斜杠命令 (Slash Commands)
@bot.tree.command(name='ping', description='测试机器人响应和延迟')
async def ping(interaction: discord.Interaction):
    """测试机器人响应"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! 延迟: {latency}ms')

@bot.tree.command(name='help', description='显示机器人帮助信息')
async def help_command(interaction: discord.Interaction):
    """显示帮助信息"""
    embed = discord.Embed(
        title="🎲 DND Discord Bot 帮助",
        description="龙与地下城Discord机器人命令列表",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📋 基础命令",
        value="`/ping` - 测试机器人响应\n`/help` - 显示此帮助信息\n`/echo <消息>` - 重复您的消息\n`/dbstats` - 显示数据库统计信息",
        inline=False
    )
    
    embed.add_field(
        name="🎲 骰子系统",
        value="`/roll` - 投掷骰子 (支持多种参数)\n`/check <修正值>` - 技能检定\n`/save <类型> <修正值>` - 豁免检定\n`/attack <加值> <伤害骰>` - 攻击检定\n`/stats` - 生成角色属性\n`/rollhelp` - 骰子详细帮助",
        inline=False
    )
    
    embed.add_field(
        name="🔍 查询功能",
        value="`/spell <法术名>` - 查询D&D 5e法术信息\n`/monster <怪物名>` - 查询怪物属性和能力\n`/skill <技能名>` - 查询技能详细说明",
        inline=False
    )
    
    embed.add_field(
        name="🚧 即将推出",
        value="• 角色管理 (`/character`)\n• 战斗辅助 (`/combat`)\n• 装备查询 (`/equipment`)",
        inline=False
    )
    
    embed.set_footer(text="更多功能正在开发中... 使用 / 开头输入命令")
    await interaction.response.send_message(embed=embed)

# 演示带参数的斜杠命令
@bot.tree.command(name='echo', description='重复您输入的消息')
@app_commands.describe(message='要重复的消息内容')
async def echo(interaction: discord.Interaction, message: str):
    """演示带参数的斜杠命令"""
    await interaction.response.send_message(f'🔊 您说: {message}')

# 数据库状态命令
@bot.tree.command(name='dbstats', description='显示数据库统计信息')
async def database_stats(interaction: discord.Interaction):
    """显示数据库统计信息"""
    try:
        stats = await db_manager.get_database_stats()
        
        embed = discord.Embed(
            title="📊 数据库统计信息",
            description="当前数据库中的数据统计",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="👥 用户数据",
            value=f"用户: {stats.get('users', 0)}\n角色: {stats.get('characters', 0)}\n成就: {stats.get('achievements', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🏰 服务器数据",
            value=f"服务器: {stats.get('guilds', 0)}\n战斗会话: {stats.get('combat_sessions', 0)}\n投掷记录: {stats.get('dice_history', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="📚 游戏数据",
            value=f"法术: {stats.get('spells', 0)}\n怪物: {stats.get('monsters', 0)}\n装备: {stats.get('equipment', 0)}",
            inline=True
        )
        
        embed.set_footer(text="数据库运行正常")
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        await interaction.response.send_message("❌ 获取数据库统计信息失败", ephemeral=True)

# 保留传统命令支持（可选）
@bot.command(name='sync')
@commands.is_owner()
async def sync(ctx):
    """同步斜杠命令（仅所有者可用）"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f'✅ 已同步 {len(synced)} 个斜杠命令')
        
        # 列出所有同步的命令
        if synced:
            cmd_list = '\n'.join([f'• /{cmd.name}: {cmd.description}' for cmd in synced])
            await ctx.send(f'📋 同步的命令列表:\n```\n{cmd_list}\n```')
    except Exception as e:
        await ctx.send(f'❌ 同步失败: {e}')

@bot.command(name='forcesync')
@commands.is_owner()
async def force_sync(ctx):
    """强制清除并重新同步斜杠命令"""
    try:
        # 清除所有命令
        bot.tree.clear_commands(guild=None)
        await ctx.send('🧹 已清除所有斜杠命令')
        
        # 重新同步
        synced = await bot.tree.sync()
        await ctx.send(f'✅ 强制重新同步完成: {len(synced)} 个命令')
        
        # 列出命令
        if synced:
            cmd_list = '\n'.join([f'• /{cmd.name}: {cmd.description}' for cmd in synced])
            await ctx.send(f'📋 命令列表:\n```\n{cmd_list}\n```')
            
    except Exception as e:
        await ctx.send(f'❌ 强制同步失败: {e}')

if __name__ == "__main__":
    # 获取Discord Token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("未找到DISCORD_TOKEN环境变量！")
        exit(1)
    
    try:
        # 启动机器人
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Discord Token无效！")
    except Exception as e:
        logger.error(f"启动机器人时发生错误: {e}")
    finally:
        # 确保关闭数据库连接
        try:
            import asyncio
            asyncio.run(db_manager.disconnect())
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
