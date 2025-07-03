"""
D&D 5e查询命令
实现法术、怪物、技能的Discord斜杠命令
"""

import discord
from discord.ext import commands
from typing import Optional, Dict, List
import logging
from .api_client import DnDAPIClient

class QueryCommands(commands.Cog):
    """查询命令Cog"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = DnDAPIClient()
        self.logger = logging.getLogger(__name__)
    
    async def cog_load(self):
        """Cog加载时启动API客户端"""
        await self.api_client.start()
        self.logger.info("查询命令模块已加载")
    
    async def cog_unload(self):
        """Cog卸载时关闭API客户端"""
        await self.api_client.close()
        self.logger.info("查询命令模块已卸载")
    
    def _format_spell_embed(self, spell_data: Dict) -> discord.Embed:
        """格式化法术信息为Discord嵌入"""
        embed = discord.Embed(
            title=f"📜 {spell_data['name']}",
            description="\n".join(spell_data['desc']),
            color=0x8B4513  # 棕色
        )
        
        # 基本信息
        embed.add_field(
            name="基本信息",
            value=(
                f"**等级**: {spell_data['level']}\n"
                f"**学派**: {spell_data['school']['name']}\n"
                f"**施法时间**: {spell_data['casting_time']}\n"
                f"**射程**: {spell_data['range']}\n"
                f"**持续时间**: {spell_data['duration']}\n"
                f"**专注**: {'是' if spell_data['concentration'] else '否'}\n"
                f"**仪式**: {'是' if spell_data['ritual'] else '否'}"
            ),
            inline=True
        )
        
        # 成分
        components = []
        if 'V' in spell_data['components']:
            components.append("语言(V)")
        if 'S' in spell_data['components']:
            components.append("姿势(S)")
        if 'M' in spell_data['components']:
            material = spell_data.get('material', '材料')
            components.append(f"材料(M): {material}")
        
        embed.add_field(
            name="成分",
            value="\n".join(components),
            inline=True
        )
        
        # 伤害信息
        if spell_data.get('damage'):
            damage_info = []
            damage = spell_data['damage']
            
            if 'damage_at_slot_level' in damage:
                damage_info.append(f"**伤害类型**: {damage['damage_type']['name']}")
                damage_levels = damage['damage_at_slot_level']
                for level, dice in damage_levels.items():
                    damage_info.append(f"**{level}环**: {dice}")
            
            if damage_info:
                embed.add_field(
                    name="伤害",
                    value="\n".join(damage_info),
                    inline=False
                )
        
        # 豁免检定
        if spell_data.get('dc'):
            dc_info = spell_data['dc']
            embed.add_field(
                name="豁免检定",
                value=f"**类型**: {dc_info['dc_type']['name']}\n**结果**: {dc_info['dc_success']}",
                inline=True
            )
        
        # 影响区域
        if spell_data.get('area_of_effect'):
            aoe = spell_data['area_of_effect']
            embed.add_field(
                name="影响区域",
                value=f"**形状**: {aoe['type']}\n**大小**: {aoe['size']}英尺",
                inline=True
            )
        
        # 职业信息
        if spell_data.get('classes'):
            class_names = [cls['name'] for cls in spell_data['classes']]
            embed.add_field(
                name="可用职业",
                value=", ".join(class_names),
                inline=False
            )
        
        # 高环施法
        if spell_data.get('higher_level'):
            embed.add_field(
                name="高环施法",
                value="\n".join(spell_data['higher_level']),
                inline=False
            )
        
        embed.set_footer(text="数据来源: D&D 5e SRD API")
        return embed
    
    @discord.app_commands.command(name="spell", description="查询D&D 5e法术信息")
    @discord.app_commands.describe(name="法术名称（英文）")
    async def spell(self, interaction: discord.Interaction, name: str):
        """查询法术信息"""
        try:
            await interaction.response.defer()
            
            spell_data = await self.api_client.get_spell(name)
            
            if not spell_data:
                embed = discord.Embed(
                    title="❌ 未找到法术",
                    description=f"未找到名为 `{name}` 的法术。请检查拼写或尝试其他关键词。",
                    color=0xFF0000
                )
                embed.add_field(
                    name="提示",
                    value="• 请使用英文名称\n• 检查拼写是否正确\n• 尝试使用不同的关键词",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = self._format_spell_embed(spell_data)
            await interaction.followup.send(embed=embed)
            
        except discord.ConnectionClosed:
            # Discord连接问题，使用fallback响应
            if not interaction.response.is_done():
                await interaction.response.send_message("⚠️ 网络连接问题，正在重试查询...", ephemeral=True)
            try:
                spell_data = await self.api_client.get_spell(name)
                if spell_data:
                    embed = self._format_spell_embed(spell_data)
                    await interaction.edit_original_response(content="", embed=embed)
                else:
                    await interaction.edit_original_response(content="❌ 未找到该法术")
            except Exception as retry_error:
                self.logger.error(f"重试法术查询失败: {retry_error}")
                await interaction.edit_original_response(content="❌ 查询失败，请稍后重试")
        
        except Exception as e:
            self.logger.error(f"法术查询错误: {e}")
            
            # 安全的错误处理 - 避免Discord连接问题导致的二次错误
            try:
                if not interaction.response.is_done():
                    embed = discord.Embed(
                        title="❌ 查询失败",
                        description="查询过程中发生网络错误，请稍后重试。",
                        color=0xFF0000
                    )
                    embed.add_field(
                        name="可能的原因",
                        value="• 网络连接问题\n• API服务临时不可用\n• 代理配置问题",
                        inline=False
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="❌ 查询失败",
                        description="查询过程中发生错误，请稍后重试。",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
            except Exception as response_error:
                # 如果连Discord响应都失败了，记录错误但不再尝试响应
                self.logger.error(f"Discord响应失败: {response_error}")
                # 静默处理，避免进一步崩溃
    
    @discord.app_commands.command(name="monster", description="查询D&D 5e怪物信息")
    @discord.app_commands.describe(name="怪物名称（英文）")
    async def monster(self, interaction: discord.Interaction, name: str):
        """查询怪物信息"""
        try:
            await interaction.response.defer()
            
            monster_data = await self.api_client.get_monster(name)
            
            if not monster_data:
                embed = discord.Embed(
                    title="❌ 未找到怪物",
                    description=f"未找到名为 `{name}` 的怪物。请检查拼写或尝试其他关键词。",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # 简化的怪物信息展示
            embed = discord.Embed(
                title=f"🐉 {monster_data['name']}",
                description=f"{monster_data['size']} {monster_data['type']}, {monster_data['alignment']}",
                color=0xDC143C
            )
            
            # 基本属性
            ac_info = f"{monster_data['armor_class'][0]['value']}"
            embed.add_field(
                name="基本信息",
                value=(
                    f"**AC**: {ac_info}\n"
                    f"**HP**: {monster_data['hit_points']} ({monster_data['hit_points_roll']})\n"
                    f"**CR**: {monster_data['challenge_rating']}\n"
                    f"**XP**: {monster_data['xp']:,}"
                ),
                inline=True
            )
            
            # 属性值
            embed.add_field(
                name="属性",
                value=(
                    f"**STR**: {monster_data['strength']}\n"
                    f"**DEX**: {monster_data['dexterity']}\n"
                    f"**CON**: {monster_data['constitution']}\n"
                    f"**INT**: {monster_data['intelligence']}\n"
                    f"**WIS**: {monster_data['wisdom']}\n"
                    f"**CHA**: {monster_data['charisma']}"
                ),
                inline=True
            )
            
            # 速度
            speed_info = []
            for speed_type, speed_value in monster_data['speed'].items():
                speed_info.append(f"{speed_type}: {speed_value}")
            
            embed.add_field(
                name="速度",
                value="\n".join(speed_info),
                inline=True
            )
            
            embed.set_footer(text="数据来源: D&D 5e SRD API")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"怪物查询错误: {e}")
            
            # 安全的错误处理 - 避免Discord连接问题导致的二次错误
            try:
                if not interaction.response.is_done():
                    embed = discord.Embed(
                        title="❌ 查询失败",
                        description="查询过程中发生网络错误，请稍后重试。",
                        color=0xFF0000
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="❌ 查询失败",
                        description="查询过程中发生错误，请稍后重试。",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
            except Exception as response_error:
                # 如果连Discord响应都失败了，记录错误但不再尝试响应
                self.logger.error(f"Discord响应失败: {response_error}")
                # 静默处理，避免进一步崩溃
    
    @discord.app_commands.command(name="skill", description="查询D&D 5e技能信息")
    @discord.app_commands.describe(name="技能名称（英文）")
    async def skill(self, interaction: discord.Interaction, name: str):
        """查询技能信息"""
        try:
            await interaction.response.defer()
            
            skill_data = await self.api_client.get_skill(name)
            
            if not skill_data:
                embed = discord.Embed(
                    title="❌ 未找到技能",
                    description=f"未找到名为 `{name}` 的技能。请检查拼写或尝试其他关键词。",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🎯 {skill_data['name']}",
                description="\n".join(skill_data['desc']),
                color=0x4169E1
            )
            
            embed.add_field(
                name="关联属性",
                value=skill_data['ability_score']['name'],
                inline=True
            )
            
            embed.set_footer(text="数据来源: D&D 5e SRD API")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"技能查询错误: {e}")
            
            # 安全的错误处理 - 避免Discord连接问题导致的二次错误
            try:
                if not interaction.response.is_done():
                    embed = discord.Embed(
                        title="❌ 查询失败",
                        description="查询过程中发生网络错误，请稍后重试。",
                        color=0xFF0000
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="❌ 查询失败",
                        description="查询过程中发生错误，请稍后重试。",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
            except Exception as response_error:
                # 如果连Discord响应都失败了，记录错误但不再尝试响应
                self.logger.error(f"Discord响应失败: {response_error}")
                # 静默处理，避免进一步崩溃

async def setup(bot: commands.Bot):
    """设置Cog"""
    await bot.add_cog(QueryCommands(bot)) 