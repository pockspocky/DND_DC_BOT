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
    
    def _format_monster_embed(self, monster_data: Dict) -> discord.Embed:
        """格式化怪物信息为Discord嵌入"""
        embed = discord.Embed(
            title=f"🐉 {monster_data['name']}",
            description=f"{monster_data['size']} {monster_data['type']}, {monster_data['alignment']}",
            color=0xDC143C
        )
        
        # 基本信息
        ac_info = f"{monster_data['armor_class'][0]['value']}"
        if len(monster_data['armor_class']) > 0 and 'type' in monster_data['armor_class'][0]:
            ac_info += f" ({monster_data['armor_class'][0]['type']})"
            
        # 计算先攻修正
        dex_modifier = (monster_data['dexterity'] - 10) // 2
        initiative = f"{dex_modifier:+d}"
        
        embed.add_field(
            name="基本信息",
            value=(
                f"**AC**: {ac_info}\n"
                f"**HP**: {monster_data['hit_points']} ({monster_data['hit_points_roll']})\n"
                f"**先攻**: {initiative}\n"
                f"**CR**: {monster_data['challenge_rating']}\n"
                f"**XP**: {monster_data['xp']:,}"
            ),
            inline=True
        )
        
        # 属性值
        embed.add_field(
            name="属性",
            value=(
                f"**STR**: {monster_data['strength']} ({(monster_data['strength'] - 10) // 2:+d})\n"
                f"**DEX**: {monster_data['dexterity']} ({(monster_data['dexterity'] - 10) // 2:+d})\n"
                f"**CON**: {monster_data['constitution']} ({(monster_data['constitution'] - 10) // 2:+d})\n"
                f"**INT**: {monster_data['intelligence']} ({(monster_data['intelligence'] - 10) // 2:+d})\n"
                f"**WIS**: {monster_data['wisdom']} ({(monster_data['wisdom'] - 10) // 2:+d})\n"
                f"**CHA**: {monster_data['charisma']} ({(monster_data['charisma'] - 10) // 2:+d})"
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
        
        # 豁免检定
        if monster_data.get('proficiencies'):
            saving_throws = []
            skills = []
            
            for prof in monster_data['proficiencies']:
                prof_name = prof['proficiency']['name']
                if 'Saving Throw' in prof_name:
                    stat = prof_name.split(': ')[1]
                    saving_throws.append(f"**{stat}**: {prof['value']:+d}")
                elif 'Skill' in prof_name:
                    skill_name = prof_name.split(': ')[1]
                    skills.append(f"**{skill_name}**: {prof['value']:+d}")
            
            if saving_throws:
                embed.add_field(
                    name="豁免检定",
                    value="\n".join(saving_throws),
                    inline=True
                )
            
            if skills:
                embed.add_field(
                    name="技能",
                    value="\n".join(skills),
                    inline=True
                )
        
        # 抗性/免疫
        resistances = []
        if monster_data.get('damage_resistances'):
            resistances.append(f"**抗性**: {', '.join(monster_data['damage_resistances'])}")
        if monster_data.get('damage_immunities'):
            resistances.append(f"**免疫**: {', '.join(monster_data['damage_immunities'])}")
        if monster_data.get('damage_vulnerabilities'):
            resistances.append(f"**弱点**: {', '.join(monster_data['damage_vulnerabilities'])}")
        if monster_data.get('condition_immunities'):
            condition_names = [cond['name'] for cond in monster_data['condition_immunities']]
            resistances.append(f"**状态免疫**: {', '.join(condition_names)}")
        
        if resistances:
            embed.add_field(
                name="抗性/免疫",
                value="\n".join(resistances),
                inline=False
            )
        
        # 感官
        if monster_data.get('senses'):
            senses_info = []
            for sense, value in monster_data['senses'].items():
                if sense == 'passive_perception':
                    senses_info.append(f"**被动察觉**: {value}")
                else:
                    senses_info.append(f"**{sense}**: {value}")
            
            if senses_info:
                embed.add_field(
                    name="感官",
                    value="\n".join(senses_info),
                    inline=True
                )
        
        # 语言
        if monster_data.get('languages'):
            embed.add_field(
                name="语言",
                value=monster_data['languages'],
                inline=True
            )
        
        # 特殊能力
        if monster_data.get('special_abilities'):
            abilities_text = []
            for ability in monster_data['special_abilities']:
                name = ability['name']
                desc = ability.get('desc', '无描述')
                # 限制描述长度
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                abilities_text.append(f"**{name}**: {desc}")
            
            # 限制字段总长度
            abilities_value = "\n".join(abilities_text)
            if len(abilities_value) > 1000:
                abilities_value = abilities_value[:1000] + "..."
            
            if abilities_text:
                embed.add_field(
                    name="特殊能力",
                    value=abilities_value,
                    inline=False
                )
        
        # 攻击动作
        if monster_data.get('actions'):
            actions_text = []
            for action in monster_data['actions']:
                name = action['name']
                desc = action.get('desc', '无描述')
                # 限制描述长度
                if len(desc) > 120:
                    desc = desc[:120] + "..."
                actions_text.append(f"**{name}**: {desc}")
            
            # 限制字段总长度
            actions_value = "\n".join(actions_text)
            if len(actions_value) > 1000:
                actions_value = actions_value[:1000] + "..."
            
            if actions_text:
                embed.add_field(
                    name="攻击动作",
                    value=actions_value,
                    inline=False
                )
        
        # 传奇动作
        if monster_data.get('legendary_actions'):
            legendary_text = []
            for action in monster_data['legendary_actions']:
                name = action['name']
                desc = action.get('desc', '无描述')
                # 限制描述长度
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                legendary_text.append(f"**{name}**: {desc}")
            
            # 限制字段总长度
            legendary_value = "\n".join(legendary_text)
            if len(legendary_value) > 1000:
                legendary_value = legendary_value[:1000] + "..."
            
            if legendary_text:
                embed.add_field(
                    name="传奇动作",
                    value=legendary_value,
                    inline=False
                )
        
        # 反应动作
        if monster_data.get('reactions'):
            reactions_text = []
            for reaction in monster_data['reactions']:
                name = reaction['name']
                desc = reaction.get('desc', '无描述')
                # 限制描述长度
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                reactions_text.append(f"**{name}**: {desc}")
            
            # 限制字段总长度
            reactions_value = "\n".join(reactions_text)
            if len(reactions_value) > 1000:
                reactions_value = reactions_value[:1000] + "..."
            
            if reactions_text:
                embed.add_field(
                    name="反应动作",
                    value=reactions_value,
                    inline=False
                )
        
        embed.set_footer(text="数据来源: D&D 5e SRD API")
        return embed
    
    def _calculate_embed_length(self, embed: discord.Embed) -> int:
        """计算嵌入消息的总字符长度"""
        total_length = 0
        
        # 标题和描述
        if hasattr(embed, 'title') and embed.title:
            total_length += len(str(embed.title))
        if hasattr(embed, 'description') and embed.description:
            total_length += len(str(embed.description))
        
        # 所有字段
        for field in embed.fields:
            total_length += len(str(field.name)) + len(str(field.value))
        
        return total_length
    
    async def _send_monster_in_thread(self, interaction: discord.Interaction, monster_data: Dict, monster_name: str):
        """在Thread中分拆发送怪物信息"""
        try:
            # 先发送一个简要的回复消息
            summary_embed = discord.Embed(
                title=f"🐉 {monster_data['name']}",
                description=f"{monster_data['size']} {monster_data['type']}, {monster_data['alignment']}\n\n📋 **信息过于详细，已在下方Thread中展开显示**",
                color=0xDC143C
            )
            
            # 基本信息
            ac_info = f"{monster_data['armor_class'][0]['value']}"
            if len(monster_data['armor_class']) > 0 and 'type' in monster_data['armor_class'][0]:
                ac_info += f" ({monster_data['armor_class'][0]['type']})"
            
            dex_modifier = (monster_data['dexterity'] - 10) // 2
            initiative = f"{dex_modifier:+d}"
            
            summary_embed.add_field(
                name="核心数据",
                value=(
                    f"**AC**: {ac_info} | **HP**: {monster_data['hit_points']}\n"
                    f"**先攻**: {initiative} | **CR**: {monster_data['challenge_rating']}\n"
                    f"**XP**: {monster_data['xp']:,}"
                ),
                inline=False
            )
            
            summary_embed.set_footer(text="详细信息请查看下方Thread")
            
            # 发送摘要消息
            response_message = await interaction.followup.send(embed=summary_embed)
            
            # 检查消息是否成功发送，然后创建Thread
            if response_message is None:
                raise Exception("发送摘要消息失败")
            
            # 创建Thread
            thread = await response_message.create_thread(
                name=f"🐉 {monster_data['name']} - 详细信息",
                auto_archive_duration=1440  # 24小时后自动归档
            )
            
            # 在Thread中发送详细信息
            await self._send_detailed_monster_info(thread, monster_data)
            
        except Exception as e:
            self.logger.error(f"创建Thread失败: {e}")
            # 如果Thread创建失败，回退到普通嵌入消息
            embed = self._format_monster_embed(monster_data)
            await interaction.followup.send(embed=embed)
    
    async def _send_detailed_monster_info(self, thread, monster_data: Dict):
        """在Thread中发送详细的怪物信息"""
        
        # 1. 基本信息和属性
        basic_embed = discord.Embed(
            title="📊 基本信息与属性",
            color=0xDC143C
        )
        
        # 基本信息
        ac_info = f"{monster_data['armor_class'][0]['value']}"
        if len(monster_data['armor_class']) > 0 and 'type' in monster_data['armor_class'][0]:
            ac_info += f" ({monster_data['armor_class'][0]['type']})"
        
        dex_modifier = (monster_data['dexterity'] - 10) // 2
        initiative = f"{dex_modifier:+d}"
        
        basic_embed.add_field(
            name="基本信息",
            value=(
                f"**AC**: {ac_info}\n"
                f"**HP**: {monster_data['hit_points']} ({monster_data['hit_points_roll']})\n"
                f"**先攻**: {initiative}\n"
                f"**CR**: {monster_data['challenge_rating']}\n"
                f"**XP**: {monster_data['xp']:,}"
            ),
            inline=True
        )
        
        # 属性值
        basic_embed.add_field(
            name="六项属性",
            value=(
                f"**STR**: {monster_data['strength']} ({(monster_data['strength'] - 10) // 2:+d})\n"
                f"**DEX**: {monster_data['dexterity']} ({(monster_data['dexterity'] - 10) // 2:+d})\n"
                f"**CON**: {monster_data['constitution']} ({(monster_data['constitution'] - 10) // 2:+d})\n"
                f"**INT**: {monster_data['intelligence']} ({(monster_data['intelligence'] - 10) // 2:+d})\n"
                f"**WIS**: {monster_data['wisdom']} ({(monster_data['wisdom'] - 10) // 2:+d})\n"
                f"**CHA**: {monster_data['charisma']} ({(monster_data['charisma'] - 10) // 2:+d})"
            ),
            inline=True
        )
        
        # 速度
        speed_info = []
        for speed_type, speed_value in monster_data['speed'].items():
            speed_info.append(f"{speed_type}: {speed_value}")
        
        basic_embed.add_field(
            name="移动速度",
            value="\n".join(speed_info),
            inline=True
        )
        
        await thread.send(embed=basic_embed)
        
        # 2. 技能、豁免和抗性
        skills_embed = discord.Embed(
            title="🎯 技能与防御",
            color=0xDC143C
        )
        
        # 豁免检定和技能
        if monster_data.get('proficiencies'):
            saving_throws = []
            skills = []
            
            for prof in monster_data['proficiencies']:
                prof_name = prof['proficiency']['name']
                if 'Saving Throw' in prof_name:
                    stat = prof_name.split(': ')[1]
                    saving_throws.append(f"**{stat}**: {prof['value']:+d}")
                elif 'Skill' in prof_name:
                    skill_name = prof_name.split(': ')[1]
                    skills.append(f"**{skill_name}**: {prof['value']:+d}")
            
            if saving_throws:
                skills_embed.add_field(
                    name="豁免检定",
                    value="\n".join(saving_throws),
                    inline=True
                )
            
            if skills:
                skills_embed.add_field(
                    name="技能熟练",
                    value="\n".join(skills),
                    inline=True
                )
        
        # 抗性/免疫
        resistances = []
        if monster_data.get('damage_resistances'):
            resistances.append(f"**抗性**: {', '.join(monster_data['damage_resistances'])}")
        if monster_data.get('damage_immunities'):
            resistances.append(f"**免疫**: {', '.join(monster_data['damage_immunities'])}")
        if monster_data.get('damage_vulnerabilities'):
            resistances.append(f"**弱点**: {', '.join(monster_data['damage_vulnerabilities'])}")
        if monster_data.get('condition_immunities'):
            condition_names = [cond['name'] for cond in monster_data['condition_immunities']]
            resistances.append(f"**状态免疫**: {', '.join(condition_names)}")
        
        if resistances:
            skills_embed.add_field(
                name="抗性/免疫",
                value="\n".join(resistances),
                inline=False
            )
        
        # 感官和语言
        if monster_data.get('senses'):
            senses_info = []
            for sense, value in monster_data['senses'].items():
                if sense == 'passive_perception':
                    senses_info.append(f"**被动察觉**: {value}")
                else:
                    senses_info.append(f"**{sense}**: {value}")
            
            if senses_info:
                skills_embed.add_field(
                    name="感官",
                    value="\n".join(senses_info),
                    inline=True
                )
        
        if monster_data.get('languages'):
            skills_embed.add_field(
                name="语言",
                value=monster_data['languages'],
                inline=True
            )
        
        # 只有当有内容时才发送
        if skills_embed.fields:
            await thread.send(embed=skills_embed)
        
        # 3. 特殊能力
        if monster_data.get('special_abilities'):
            abilities_embed = discord.Embed(
                title="✨ 特殊能力",
                color=0xDC143C
            )
            
            for ability in monster_data['special_abilities']:
                name = ability['name']
                desc = ability.get('desc', '无描述')
                
                abilities_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=abilities_embed)
        
        # 4. 攻击动作
        if monster_data.get('actions'):
            actions_embed = discord.Embed(
                title="⚔️ 攻击动作",
                color=0xDC143C
            )
            
            for action in monster_data['actions']:
                name = action['name']
                desc = action.get('desc', '无描述')
                
                actions_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=actions_embed)
        
        # 5. 传奇动作
        if monster_data.get('legendary_actions'):
            legendary_embed = discord.Embed(
                title="👑 传奇动作",
                color=0xFFD700  # 金色
            )
            
            for action in monster_data['legendary_actions']:
                name = action['name']
                desc = action.get('desc', '无描述')
                
                legendary_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=legendary_embed)
        
        # 6. 反应动作
        if monster_data.get('reactions'):
            reactions_embed = discord.Embed(
                title="🛡️ 反应动作",
                color=0x4169E1  # 皇家蓝
            )
            
            for reaction in monster_data['reactions']:
                name = reaction['name']
                desc = reaction.get('desc', '无描述')
                
                reactions_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=reactions_embed)
        
        # 最后发送数据来源
        source_embed = discord.Embed(
            title="📚 数据来源",
            description="所有数据来自 D&D 5e 系统参考文档 (SRD) API",
            color=0x696969
        )
        await thread.send(embed=source_embed)

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
                embed.add_field(
                    name="提示",
                    value="• 请使用英文名称\n• 检查拼写是否正确\n• 尝试使用不同的关键词",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            # 先生成嵌入消息
            embed = self._format_monster_embed(monster_data)
            
            # 检查消息长度
            total_length = self._calculate_embed_length(embed)
            
            if total_length > 750:
                # 如果超过750字符，使用Thread分拆发送
                self.logger.info(f"怪物 {monster_data['name']} 信息过长 ({total_length} 字符)，创建Thread")
                await self._send_monster_in_thread(interaction, monster_data, name)
            else:
                # 正常发送嵌入消息
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