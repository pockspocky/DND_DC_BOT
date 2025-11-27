"""
D&D 5e Query Command System
Simplified spell, monster, and skill query functionality
"""
import discord
from discord.ext import commands
from typing import Optional, Dict
import logging
from .api_client import DnDAPIClient

class QueryCommands(commands.Cog):
    """D&D Query Command Group - Spell, Monster, and Skill Queries"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = DnDAPIClient()
        self.logger = logging.getLogger(__name__)
    
    async def cog_load(self):
        """Start API client"""
        await self.api_client.start()
        self.logger.info("Query command module loaded")
    
    async def cog_unload(self):
        """Close API client"""
        await self.api_client.close()
        self.logger.info("Query command module unloaded")
    
    def _format_spell_embed(self, spell_data: Dict) -> discord.Embed:
        """Format spell information as Discord embed"""
        embed = discord.Embed(
            title=f"📜 {spell_data['name']}",
            description="\n".join(spell_data['desc']),
            color=0x8B4513  # Brown
        )
        
        # Basic information
        embed.add_field(
            name="Basic Info",
            value=(
                f"**Level**: {spell_data['level']}\n"
                f"**School**: {spell_data['school']['name']}\n"
                f"**Casting Time**: {spell_data['casting_time']}\n"
                f"**Range**: {spell_data['range']}\n"
                f"**Duration**: {spell_data['duration']}\n"
                f"**Concentration**: {'Yes' if spell_data['concentration'] else 'No'}\n"
                f"**Ritual**: {'Yes' if spell_data['ritual'] else 'No'}"
            ),
            inline=True
        )
        
        # Components
        components = []
        if 'V' in spell_data['components']:
            components.append("Verbal (V)")
        if 'S' in spell_data['components']:
            components.append("Somatic (S)")
        if 'M' in spell_data['components']:
            material = spell_data.get('material', 'Material')
            components.append(f"Material (M): {material}")
        
        embed.add_field(
            name="Components",
            value="\n".join(components),
            inline=True
        )
        
        # Damage information
        if spell_data.get('damage'):
            damage_info = []
            damage = spell_data['damage']
            
            if 'damage_at_slot_level' in damage:
                damage_info.append(f"**Damage Type**: {damage['damage_type']['name']}")
                damage_levels = damage['damage_at_slot_level']
                for level, dice in damage_levels.items():
                    damage_info.append(f"**Level {level}**: {dice}")
            
            if damage_info:
                embed.add_field(
                    name="Damage",
                    value="\n".join(damage_info),
                    inline=False
                )
        
        # Saving throw
        if spell_data.get('dc'):
            dc_info = spell_data['dc']
            embed.add_field(
                name="Saving Throw",
                value=f"**Type**: {dc_info['dc_type']['name']}\n**On Success**: {dc_info['dc_success']}",
                inline=True
            )
        
        # Area of effect
        if spell_data.get('area_of_effect'):
            aoe = spell_data['area_of_effect']
            embed.add_field(
                name="Area of Effect",
                value=f"**Shape**: {aoe['type']}\n**Size**: {aoe['size']} feet",
                inline=True
            )
        
        # Class information
        if spell_data.get('classes'):
            class_names = [cls['name'] for cls in spell_data['classes']]
            embed.add_field(
                name="Available Classes",
                value=", ".join(class_names),
                inline=False
            )
        
        # At higher levels
        if spell_data.get('higher_level'):
            embed.add_field(
                name="At Higher Levels",
                value="\n".join(spell_data['higher_level']),
                inline=False
            )
        
        embed.set_footer(text="Data Source: D&D 5e SRD API")
        return embed
    
    @discord.app_commands.command(name="sp", description="Query D&D 5e spell information")
    @discord.app_commands.describe(name="Spell name (English)")
    async def spell(self, interaction: discord.Interaction, name: str):
        """Query spell information"""
        try:
            await interaction.response.defer()
            
            spell_data = await self.api_client.get_spell(name)
            
            if not spell_data:
                embed = discord.Embed(
                    title="❌ Spell Not Found",
                    description=f"Could not find spell named `{name}`. Please check spelling or try different keywords.",
                    color=0xFF0000
                )
                embed.add_field(
                    name="Tips",
                    value="• Use English spell names\n• Check spelling\n• Try different keywords",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = self._format_spell_embed(spell_data)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Spell query error: {e}")
            # Simplified error handling
            try:
                error_embed = discord.Embed(
                    title="❌ Query Failed",
                    description="An error occurred during the query, please try again later",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except Exception:
                # Silent handling to avoid further errors
                pass
    
    def _format_monster_embed(self, monster_data: Dict) -> discord.Embed:
        """Format monster information as Discord embed"""
        embed = discord.Embed(
            title=f"🐉 {monster_data['name']}",
            description=f"{monster_data['size']} {monster_data['type']}, {monster_data['alignment']}",
            color=0xDC143C
        )
        
        # Basic information
        ac_info = f"{monster_data['armor_class'][0]['value']}"
        if len(monster_data['armor_class']) > 0 and 'type' in monster_data['armor_class'][0]:
            ac_info += f" ({monster_data['armor_class'][0]['type']})"
            
        # Calculate initiative modifier
        dex_modifier = (monster_data['dexterity'] - 10) // 2
        initiative = f"{dex_modifier:+d}"
        
        embed.add_field(
            name="Basic Info",
            value=(
                f"**AC**: {ac_info}\n"
                f"**HP**: {monster_data['hit_points']} ({monster_data['hit_points_roll']})\n"
                f"**Initiative**: {initiative}\n"
                f"**CR**: {monster_data['challenge_rating']}\n"
                f"**XP**: {monster_data['xp']:,}"
            ),
            inline=True
        )
        
        # Ability scores
        embed.add_field(
            name="Abilities",
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
        
        # Speed
        speed_info = []
        for speed_type, speed_value in monster_data['speed'].items():
            speed_info.append(f"{speed_type}: {speed_value}")
        
        embed.add_field(
            name="Speed",
            value="\n".join(speed_info),
            inline=True
        )
        
        # Saving throws
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
                    name="Saving Throws",
                    value="\n".join(saving_throws),
                    inline=True
                )
            
            if skills:
                embed.add_field(
                    name="Skills",
                    value="\n".join(skills),
                    inline=True
                )
        
        # Resistances/Immunities
        resistances = []
        if monster_data.get('damage_resistances'):
            resistances.append(f"**Resistances**: {', '.join(monster_data['damage_resistances'])}")
        if monster_data.get('damage_immunities'):
            resistances.append(f"**Immunities**: {', '.join(monster_data['damage_immunities'])}")
        if monster_data.get('damage_vulnerabilities'):
            resistances.append(f"**Vulnerabilities**: {', '.join(monster_data['damage_vulnerabilities'])}")
        if monster_data.get('condition_immunities'):
            condition_names = [cond['name'] for cond in monster_data['condition_immunities']]
            resistances.append(f"**Condition Immunities**: {', '.join(condition_names)}")
        
        if resistances:
            embed.add_field(
                name="Resistances/Immunities",
                value="\n".join(resistances),
                inline=False
            )
        
        # Senses
        if monster_data.get('senses'):
            senses_info = []
            for sense, value in monster_data['senses'].items():
                if sense == 'passive_perception':
                    senses_info.append(f"**Passive Perception**: {value}")
                else:
                    senses_info.append(f"**{sense}**: {value}")
            
            if senses_info:
                embed.add_field(
                    name="Senses",
                    value="\n".join(senses_info),
                    inline=True
                )
        
        # Languages
        if monster_data.get('languages'):
            embed.add_field(
                name="Languages",
                value=monster_data['languages'],
                inline=True
            )
        
        # Special abilities
        if monster_data.get('special_abilities'):
            abilities_text = []
            for ability in monster_data['special_abilities']:
                name = ability['name']
                desc = ability.get('desc', 'No description')
                # Reasonable description length limit
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                abilities_text.append(f"**{name}**: {desc}")
            
            # Limit total field length (Discord limit is 1024 characters)
            abilities_value = "\n".join(abilities_text)
            if len(abilities_value) > 1020:
                abilities_value = abilities_value[:1020] + "..."
            
            if abilities_text:
                embed.add_field(
                    name="Special Abilities",
                    value=abilities_value,
                    inline=False
                )
        
        # Actions
        if monster_data.get('actions'):
            actions_text = []
            for action in monster_data['actions']:
                name = action['name']
                desc = action.get('desc', 'No description')
                # Reasonable description length limit
                if len(desc) > 250:
                    desc = desc[:250] + "..."
                actions_text.append(f"**{name}**: {desc}")
            
            # Limit total field length (Discord limit is 1024 characters)
            actions_value = "\n".join(actions_text)
            if len(actions_value) > 1020:
                actions_value = actions_value[:1020] + "..."
            
            if actions_text:
                embed.add_field(
                    name="Actions",
                    value=actions_value,
                    inline=False
                )
        
        # Legendary actions
        if monster_data.get('legendary_actions'):
            legendary_text = []
            for action in monster_data['legendary_actions']:
                name = action['name']
                desc = action.get('desc', 'No description')
                # Reasonable description length limit
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                legendary_text.append(f"**{name}**: {desc}")
            
            # Limit total field length (Discord limit is 1024 characters)
            legendary_value = "\n".join(legendary_text)
            if len(legendary_value) > 1020:
                legendary_value = legendary_value[:1020] + "..."
            
            if legendary_text:
                embed.add_field(
                    name="Legendary Actions",
                    value=legendary_value,
                    inline=False
                )
        
        # Reactions
        if monster_data.get('reactions'):
            reactions_text = []
            for reaction in monster_data['reactions']:
                name = reaction['name']
                desc = reaction.get('desc', 'No description')
                # Reasonable description length limit
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                reactions_text.append(f"**{name}**: {desc}")
            
            # Limit total field length (Discord limit is 1024 characters)
            reactions_value = "\n".join(reactions_text)
            if len(reactions_value) > 1020:
                reactions_value = reactions_value[:1020] + "..."
            
            if reactions_text:
                embed.add_field(
                    name="Reactions",
                    value=reactions_value,
                    inline=False
                )
        
        embed.set_footer(text="Data Source: D&D 5e SRD API")
        return embed
    
    def _calculate_embed_length(self, embed: discord.Embed) -> int:
        """Calculate total character length of embed message"""
        total_length = 0
        
        # Title and description
        if hasattr(embed, 'title') and embed.title:
            total_length += len(str(embed.title))
        if hasattr(embed, 'description') and embed.description:
            total_length += len(str(embed.description))
        
        # All fields
        for field in embed.fields:
            total_length += len(str(field.name)) + len(str(field.value))
        
        return total_length
    
    async def _send_monster_in_thread(self, interaction: discord.Interaction, monster_data: Dict, monster_name: str):
        """Send monster information split across thread messages"""
        try:
            # Check if in guild channel (threads can only be created in guild channels)
            if interaction.guild is None:
                self.logger.info(f"User queried monster {monster_data['name']} in DM, using regular embed")
                embed = self._format_monster_embed(monster_data)
                await interaction.edit_original_response(embed=embed)
                return
            
            # Check if bot has permission to create threads
            if not interaction.app_permissions.create_public_threads:
                self.logger.warning("Bot lacks thread creation permission, using regular embed")
                embed = self._format_monster_embed(monster_data)
                await interaction.edit_original_response(embed=embed)
                return
            
            # Send a brief summary message first
            summary_embed = discord.Embed(
                title=f"🐉 {monster_data['name']}",
                description=f"{monster_data['size']} {monster_data['type']}, {monster_data['alignment']}\n\n📋 **Detailed information displayed in thread below**",
                color=0xDC143C
            )
            
            # Basic information
            ac_info = f"{monster_data['armor_class'][0]['value']}"
            if len(monster_data['armor_class']) > 0 and 'type' in monster_data['armor_class'][0]:
                ac_info += f" ({monster_data['armor_class'][0]['type']})"
            
            dex_modifier = (monster_data['dexterity'] - 10) // 2
            initiative = f"{dex_modifier:+d}"
            
            summary_embed.add_field(
                name="Core Stats",
                value=(
                    f"**AC**: {ac_info} | **HP**: {monster_data['hit_points']}\n"
                    f"**Initiative**: {initiative} | **CR**: {monster_data['challenge_rating']}\n"
                    f"**XP**: {monster_data['xp']:,}"
                ),
                inline=False
            )
            
            summary_embed.set_footer(text="See thread below for detailed information")
            
            # Use edit_original_response to send summary, ensuring message has full guild info
            await interaction.edit_original_response(embed=summary_embed)
            
            # Wait briefly to ensure message is fully sent
            import asyncio
            await asyncio.sleep(0.5)
            
            # Get original response message with full guild info
            original_message = await interaction.original_response()
            
            # Create thread
            thread = await original_message.create_thread(
                name=f"🐉 {monster_data['name']} - Details",
                auto_archive_duration=1440  # Auto-archive after 24 hours
            )
            
            # Send detailed information in thread
            await self._send_detailed_monster_info(thread, monster_data)
            
        except discord.Forbidden:
            self.logger.error("Thread creation failed: Insufficient permissions")
            embed = self._format_monster_embed(monster_data)
            await interaction.edit_original_response(embed=embed)
        except discord.HTTPException as e:
            self.logger.error(f"Thread creation failed: Discord API error - {e}")
            embed = self._format_monster_embed(monster_data)
            await interaction.edit_original_response(embed=embed)
        except Exception as e:
            self.logger.error(f"Thread creation failed: {e}")
            # Fall back to regular embed if thread creation fails
            embed = self._format_monster_embed(monster_data)
            await interaction.edit_original_response(embed=embed)
    
    async def _send_detailed_monster_info(self, thread, monster_data: Dict):
        """Send detailed monster information in thread"""
        
        # 1. Basic information and abilities
        basic_embed = discord.Embed(
            title="📊 Basic Info & Abilities",
            color=0xDC143C
        )
        
        # Basic information
        ac_info = f"{monster_data['armor_class'][0]['value']}"
        if len(monster_data['armor_class']) > 0 and 'type' in monster_data['armor_class'][0]:
            ac_info += f" ({monster_data['armor_class'][0]['type']})"
        
        dex_modifier = (monster_data['dexterity'] - 10) // 2
        initiative = f"{dex_modifier:+d}"
        
        basic_embed.add_field(
            name="Basic Info",
            value=(
                f"**AC**: {ac_info}\n"
                f"**HP**: {monster_data['hit_points']} ({monster_data['hit_points_roll']})\n"
                f"**Initiative**: {initiative}\n"
                f"**CR**: {monster_data['challenge_rating']}\n"
                f"**XP**: {monster_data['xp']:,}"
            ),
            inline=True
        )
        
        # Ability scores
        basic_embed.add_field(
            name="Ability Scores",
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
        
        # Speed
        speed_info = []
        for speed_type, speed_value in monster_data['speed'].items():
            speed_info.append(f"{speed_type}: {speed_value}")
        
        basic_embed.add_field(
            name="Speed",
            value="\n".join(speed_info),
            inline=True
        )
        
        await thread.send(embed=basic_embed)
        
        # 2. Skills, saves, and defenses
        skills_embed = discord.Embed(
            title="🎯 Skills & Defenses",
            color=0xDC143C
        )
        
        # Saving throws and skills
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
                    name="Saving Throws",
                    value="\n".join(saving_throws),
                    inline=True
                )
            
            if skills:
                skills_embed.add_field(
                    name="Skill Proficiencies",
                    value="\n".join(skills),
                    inline=True
                )
        
        # Resistances/Immunities
        resistances = []
        if monster_data.get('damage_resistances'):
            resistances.append(f"**Resistances**: {', '.join(monster_data['damage_resistances'])}")
        if monster_data.get('damage_immunities'):
            resistances.append(f"**Immunities**: {', '.join(monster_data['damage_immunities'])}")
        if monster_data.get('damage_vulnerabilities'):
            resistances.append(f"**Vulnerabilities**: {', '.join(monster_data['damage_vulnerabilities'])}")
        if monster_data.get('condition_immunities'):
            condition_names = [cond['name'] for cond in monster_data['condition_immunities']]
            resistances.append(f"**Condition Immunities**: {', '.join(condition_names)}")
        
        if resistances:
            skills_embed.add_field(
                name="Resistances/Immunities",
                value="\n".join(resistances),
                inline=False
            )
        
        # Senses and languages
        if monster_data.get('senses'):
            senses_info = []
            for sense, value in monster_data['senses'].items():
                if sense == 'passive_perception':
                    senses_info.append(f"**Passive Perception**: {value}")
                else:
                    senses_info.append(f"**{sense}**: {value}")
            
            if senses_info:
                skills_embed.add_field(
                    name="Senses",
                    value="\n".join(senses_info),
                    inline=True
                )
        
        if monster_data.get('languages'):
            skills_embed.add_field(
                name="Languages",
                value=monster_data['languages'],
                inline=True
            )
        
        # Only send if there's content
        if skills_embed.fields:
            await thread.send(embed=skills_embed)
        
        # 3. Special abilities
        if monster_data.get('special_abilities'):
            abilities_embed = discord.Embed(
                title="✨ Special Abilities",
                color=0xDC143C
            )
            
            for ability in monster_data['special_abilities']:
                name = ability['name']
                desc = ability.get('desc', 'No description')
                
                abilities_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=abilities_embed)
        
        # 4. Actions
        if monster_data.get('actions'):
            actions_embed = discord.Embed(
                title="⚔️ Actions",
                color=0xDC143C
            )
            
            for action in monster_data['actions']:
                name = action['name']
                desc = action.get('desc', 'No description')
                
                actions_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=actions_embed)
        
        # 5. Legendary actions
        if monster_data.get('legendary_actions'):
            legendary_embed = discord.Embed(
                title="👑 Legendary Actions",
                color=0xFFD700  # Gold
            )
            
            for action in monster_data['legendary_actions']:
                name = action['name']
                desc = action.get('desc', 'No description')
                
                legendary_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=legendary_embed)
        
        # 6. Reactions
        if monster_data.get('reactions'):
            reactions_embed = discord.Embed(
                title="🛡️ Reactions",
                color=0x4169E1  # Royal blue
            )
            
            for reaction in monster_data['reactions']:
                name = reaction['name']
                desc = reaction.get('desc', 'No description')
                
                reactions_embed.add_field(
                    name=name,
                    value=desc,
                    inline=False
                )
            
            await thread.send(embed=reactions_embed)
        
        # Finally send data source
        source_embed = discord.Embed(
            title="📚 Data Source",
            description="All data from D&D 5e System Reference Document (SRD) API",
            color=0x696969
        )
        await thread.send(embed=source_embed)

    @discord.app_commands.command(name="mon", description="Query D&D 5e monster information")
    @discord.app_commands.describe(name="Monster name (English)")
    async def monster(self, interaction: discord.Interaction, name: str):
        """Query monster information"""
        try:
            await interaction.response.defer()
            
            monster_data = await self.api_client.get_monster(name)
            
            if not monster_data:
                embed = discord.Embed(
                    title="❌ Monster Not Found",
                    description=f"Could not find monster named `{name}`. Please check spelling or try different keywords.",
                    color=0xFF0000
                )
                embed.add_field(
                    name="Tips",
                    value="• Use English monster names\n• Check spelling\n• Try different keywords",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Generate embed message first
            embed = self._format_monster_embed(monster_data)
            
            # Check message length
            total_length = self._calculate_embed_length(embed)
            
            if total_length > 750:
                # If over 750 characters, split across thread
                self.logger.info(f"Monster {monster_data['name']} info too long ({total_length} chars), creating thread")
                await self._send_monster_in_thread(interaction, monster_data, name)
            else:
                # Send regular embed message
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Monster query error: {e}")
            
            # Safe error handling - avoid secondary errors from Discord connection issues
            try:
                if not interaction.response.is_done():
                    embed = discord.Embed(
                        title="❌ Query Failed",
                        description="A network error occurred during the query, please try again later.",
                        color=0xFF0000
                    )
                    embed.add_field(
                        name="Possible Causes",
                        value="• Network connection issues\n• API service temporarily unavailable\n• Proxy configuration issues",
                        inline=False
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="❌ Query Failed",
                        description="An error occurred during the query, please try again later.",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
            except Exception as response_error:
                # If even Discord response fails, log error but don't try to respond again
                self.logger.error(f"Discord response failed: {response_error}")
                # Silent handling to avoid further crashes
    
    @discord.app_commands.command(name="sk", description="Query D&D 5e skill information")
    @discord.app_commands.describe(name="Skill name (English)")
    async def skill(self, interaction: discord.Interaction, name: str):
        """Query skill information"""
        try:
            await interaction.response.defer()
            
            skill_data = await self.api_client.get_skill(name)
            
            if not skill_data:
                embed = discord.Embed(
                    title="❌ Skill Not Found",
                    description=f"Could not find skill named `{name}`. Please check spelling or try different keywords.",
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
                name="Associated Ability",
                value=skill_data['ability_score']['name'],
                inline=True
            )
            
            embed.set_footer(text="Data Source: D&D 5e SRD API")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Skill query error: {e}")
            
            # Safe error handling - avoid secondary errors from Discord connection issues
            try:
                if not interaction.response.is_done():
                    embed = discord.Embed(
                        title="❌ Query Failed",
                        description="A network error occurred during the query, please try again later.",
                        color=0xFF0000
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="❌ Query Failed",
                        description="An error occurred during the query, please try again later.",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
            except Exception as response_error:
                # If even Discord response fails, log error but don't try to respond again
                self.logger.error(f"Discord response failed: {response_error}")
                # Silent handling to avoid further crashes

async def setup(bot: commands.Bot):
    """Setup Cog"""
    await bot.add_cog(QueryCommands(bot)) 