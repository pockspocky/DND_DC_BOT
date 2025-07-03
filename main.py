import discord
from discord.ext import commands
from discord import app_commands
import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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
        
        # 初始化机器人
        super().__init__(
            command_prefix=os.getenv('PREFIX', '!'),
            intents=intents,
            help_command=None  # 禁用默认帮助命令，后续自定义
        )
        
    async def setup_hook(self):
        """机器人启动时的初始化设置"""
        logger.info("正在设置机器人...")
        
        # 同步斜杠命令到Discord
        try:
            synced = await self.tree.sync()
            logger.info(f"已同步 {len(synced)} 个斜杠命令")
        except Exception as e:
            logger.error(f"同步斜杠命令失败: {e}")
        
        # 这里后续会添加数据库初始化、加载扩展等
        
    async def on_ready(self):
        """机器人准备就绪时的回调"""
        if self.user is None:
            logger.error("机器人用户对象为None，可能连接未完全建立")
            return
            
        logger.info(f'{self.user} 已成功登录!')
        logger.info(f'机器人ID: {self.user.id}')
        logger.info(f'连接到 {len(self.guilds)} 个服务器')
        
        # 设置机器人状态
        await self.change_presence(
            activity=discord.Game(name="龙与地下城 | /help"),
            status=discord.Status.online
        )
        
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
        value="`/ping` - 测试机器人响应\n`/help` - 显示此帮助信息\n`/echo <消息>` - 重复您的消息",
        inline=False
    )
    
    embed.add_field(
        name="🎲 即将推出",
        value="• 骰子系统 (`/roll`)\n• 角色管理 (`/character`)\n• 战斗辅助 (`/combat`)\n• 查询功能 (`/spell`, `/monster`)",
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

# 保留传统命令支持（可选）
@bot.command(name='sync')
@commands.is_owner()
async def sync(ctx):
    """同步斜杠命令（仅所有者可用）"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f'✅ 已同步 {len(synced)} 个斜杠命令')
    except Exception as e:
        await ctx.send(f'❌ 同步失败: {e}')

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
