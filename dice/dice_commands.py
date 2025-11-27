"""
Advanced D&D Dice Command System
Uses the new advanced dice roller with expression-based syntax
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import logging
from dice.advanced_roller import advanced_roller
from dice.exceptions import DiceError, ParseError, ValidationError, UnsupportedFeatureError

logger = logging.getLogger(__name__)


class AdvancedDiceCommands(commands.Cog):
    """Advanced dice command group with expression-based rolling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.roller = advanced_roller
    
    @app_commands.command(name="r", description="Roll dice using advanced expression syntax")
    @app_commands.describe(
        expression="Dice expression (e.g., 2d20kh1+5, 4d6kh3, 10d6>=5)",
        private="Show result privately (only visible to you)"
    )
    async def roll_dice(self, interaction: discord.Interaction,
                       expression: str,
                       private: bool = False):
        """
        Advanced dice roll command with expression syntax
        
        Examples:
        - 2d20kh1+5: Advantage with +5 modifier
        - 4d6kh3: Ability score generation
        - 2d6r1: Reroll 1s once
        - 10d6>=5: Count successes (dice >= 5)
        - (1d8+2)*3: Complex expressions
        """
        try:
            # Roll dice
            result = await self.roller.roll(
                expression,
                interaction.user.id,
                interaction.guild_id or 0,
                interaction.channel_id or 0
            )
            
            # Format as Discord embed
            embed_dict = self.roller.format_embed(result, interaction.user.display_name)
            embed = discord.Embed.from_dict(embed_dict)
            
            # Send response
            await interaction.response.send_message(
                embed=embed,
                ephemeral=private
            )
            
        except UnsupportedFeatureError as e:
            await interaction.response.send_message(
                f"❌ **Unsupported Feature**\n{str(e)}",
                ephemeral=True
            )
        except ValidationError as e:
            await interaction.response.send_message(
                f"❌ **Validation Error**\n{str(e)}",
                ephemeral=True
            )
        except ParseError as e:
            await interaction.response.send_message(
                f"❌ **Invalid Syntax**\n{str(e)}\n\n"
                f"**Examples:**\n"
                f"• `d20` or `2d20kh1+5` - Basic rolls\n"
                f"• `4d6kh3` - Keep highest 3 of 4d6\n"
                f"• `2d6r1` - Reroll 1s once\n"
                f"• `10d6>=5` - Count successes\n"
                f"• `(1d8+2)*3` - Complex expressions",
                ephemeral=True
            )
        except DiceError as e:
            await interaction.response.send_message(
                f"❌ **Error**\n{str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error in roll command: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An unexpected error occurred. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="rh", description="Show advanced dice roller help")
    async def dice_help(self, interaction: discord.Interaction):
        """Advanced dice help command"""
        embed = discord.Embed(
            title="🎲 Advanced Dice Roller Help",
            description="Powerful expression-based dice rolling for D&D",
            color=0x00FFFF
        )
        
        embed.add_field(
            name="📋 Basic Syntax",
            value=(
                "`/r expression:<dice>`\n"
                "• `d20` - Roll 1d20\n"
                "• `2d6+3` - Roll 2d6 and add 3\n"
                "• `1d8-1` - Roll 1d8 and subtract 1"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Advantage/Disadvantage",
            value=(
                "• `2d20kh1` - Advantage (keep highest)\n"
                "• `2d20kl1` - Disadvantage (keep lowest)\n"
                "• `2d20kh1+5` - Advantage with modifier"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Keep/Drop Dice",
            value=(
                "• `4d6kh3` - Keep highest 3 (ability scores)\n"
                "• `4d6dl1` - Drop lowest 1 (same result)\n"
                "• `5d10kl2` - Keep lowest 2\n"
                "• `6d8dh2` - Drop highest 2"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔄 Reroll",
            value=(
                "• `2d6r1` - Reroll 1s once\n"
                "• `2d6ro1` - Reroll 1s repeatedly\n"
                "• `1d8r1r2` - Reroll 1s and 2s"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Min/Max Clamping",
            value=(
                "• `1d8min5` - Minimum result of 5\n"
                "• `2d10max8` - Maximum result of 8 per die\n"
                "• `4d6min2kh3` - Min 2, keep highest 3"
            ),
            inline=False
        )
        
        embed.add_field(
            name="✅ Success Counting",
            value=(
                "• `10d6>=5` - Count dice ≥ 5\n"
                "• `8d10<3` - Count dice < 3\n"
                "• `6d6=6` - Count 6s\n"
                "• `(10d6>=5)-2` - Successes minus 2"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🧮 Complex Expressions",
            value=(
                "• `(1d8+2)*3` - Parentheses supported\n"
                "• `1d8+2d6kh1+3` - Multiple dice terms\n"
                "• `2d20kh1+1d4+5` - Advantage + bonus damage"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value=(
                "• Operators apply in order: reroll → clamp → keep/drop\n"
                "• Use `private:True` to hide results from others\n"
                "• Maximum 10,000 dice per roll\n"
                "• Exploding dice (!) not supported"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="check", description="Skill check with advantage/disadvantage")
    @app_commands.describe(
        modifier="Skill modifier",
        advantage="Advantage/Disadvantage/Normal",
        skill="Skill name (optional)",
        private="Show result privately"
    )
    async def skill_check(self, interaction: discord.Interaction,
                         modifier: int = 0,
                         advantage: Optional[str] = None,
                         skill: Optional[str] = None,
                         private: bool = False):
        """Skill check command using advanced roller"""
        try:
            # Build expression based on advantage/disadvantage
            if advantage == "Advantage":
                expression = f"2d20kh1{modifier:+d}" if modifier != 0 else "2d20kh1"
            elif advantage == "Disadvantage":
                expression = f"2d20kl1{modifier:+d}" if modifier != 0 else "2d20kl1"
            else:
                expression = f"d20{modifier:+d}" if modifier != 0 else "d20"
            
            # Roll dice
            result = await self.roller.roll(
                expression,
                interaction.user.id,
                interaction.guild_id or 0,
                interaction.channel_id or 0
            )
            
            # Create embed
            embed = discord.Embed(
                title="🎯 Skill Check",
                color=0x00ff00
            )
            
            if skill:
                embed.add_field(name="Skill", value=skill, inline=True)
            embed.add_field(name="Modifier", value=f"{modifier:+d}", inline=True)
            adv_text = advantage if advantage else "Normal"
            embed.add_field(name="Type", value=adv_text, inline=True)
            embed.add_field(name="Result", value=f"**{result.final_value}**", inline=False)
            embed.add_field(name="Details", value=self.roller.format_result(result), inline=False)
            
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=private)
            
        except DiceError as e:
            await interaction.response.send_message(
                f"❌ **Error**\n{str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Skill check failed: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An unexpected error occurred.",
                ephemeral=True
            )
    
    @skill_check.autocomplete('advantage')
    async def advantage_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for advantage parameter"""
        choices = [
            app_commands.Choice(name="Normal", value="Normal"),
            app_commands.Choice(name="Advantage", value="Advantage"),
            app_commands.Choice(name="Disadvantage", value="Disadvantage")
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]
    
    @app_commands.command(name="save", description="Saving throw with advantage/disadvantage")
    @app_commands.describe(
        save_type="Saving throw type",
        modifier="Saving throw modifier",
        advantage="Advantage/Disadvantage/Normal",
        private="Show result privately"
    )
    async def saving_throw(self, interaction: discord.Interaction,
                          save_type: Optional[str] = None,
                          modifier: int = 0,
                          advantage: Optional[str] = None,
                          private: bool = False):
        """Saving throw command using advanced roller"""
        try:
            # Build expression based on advantage/disadvantage
            if advantage == "Advantage":
                expression = f"2d20kh1{modifier:+d}" if modifier != 0 else "2d20kh1"
            elif advantage == "Disadvantage":
                expression = f"2d20kl1{modifier:+d}" if modifier != 0 else "2d20kl1"
            else:
                expression = f"d20{modifier:+d}" if modifier != 0 else "d20"
            
            # Roll dice
            result = await self.roller.roll(
                expression,
                interaction.user.id,
                interaction.guild_id or 0,
                interaction.channel_id or 0
            )
            
            # Create embed
            embed = discord.Embed(
                title="🛡️ Saving Throw",
                color=0xff9900
            )
            
            embed.add_field(name="Save Type", value=save_type or "General", inline=True)
            embed.add_field(name="Modifier", value=f"{modifier:+d}", inline=True)
            adv_text = advantage if advantage else "Normal"
            embed.add_field(name="Type", value=adv_text, inline=True)
            embed.add_field(name="Result", value=f"**{result.final_value}**", inline=False)
            embed.add_field(name="Details", value=self.roller.format_result(result), inline=False)
            
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=private)
            
        except DiceError as e:
            await interaction.response.send_message(
                f"❌ **Error**\n{str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Saving throw failed: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An unexpected error occurred.",
                ephemeral=True
            )
    
    @saving_throw.autocomplete('save_type')
    async def save_type_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for save type"""
        choices = [
            app_commands.Choice(name="Strength", value="Strength"),
            app_commands.Choice(name="Dexterity", value="Dexterity"),
            app_commands.Choice(name="Constitution", value="Constitution"),
            app_commands.Choice(name="Intelligence", value="Intelligence"),
            app_commands.Choice(name="Wisdom", value="Wisdom"),
            app_commands.Choice(name="Charisma", value="Charisma")
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]
    
    @saving_throw.autocomplete('advantage')
    async def save_advantage_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for advantage parameter"""
        choices = [
            app_commands.Choice(name="Normal", value="Normal"),
            app_commands.Choice(name="Advantage", value="Advantage"),
            app_commands.Choice(name="Disadvantage", value="Disadvantage")
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]
    
    @app_commands.command(name="att", description="Attack roll and damage")
    @app_commands.describe(
        attack_bonus="Attack bonus",
        damage_dice="Damage dice expression (e.g., 1d8+3, 2d6)",
        advantage="Attack Advantage/Disadvantage/Normal",
        weapon="Weapon name (optional)",
        private="Show result privately"
    )
    async def attack_roll(self, interaction: discord.Interaction,
                         attack_bonus: int,
                         damage_dice: str,
                         advantage: Optional[str] = None,
                         weapon: Optional[str] = None,
                         private: bool = False):
        """Attack roll command using advanced roller"""
        try:
            # Build attack expression
            if advantage == "Advantage":
                attack_expr = f"2d20kh1{attack_bonus:+d}" if attack_bonus != 0 else "2d20kh1"
            elif advantage == "Disadvantage":
                attack_expr = f"2d20kl1{attack_bonus:+d}" if attack_bonus != 0 else "2d20kl1"
            else:
                attack_expr = f"d20{attack_bonus:+d}" if attack_bonus != 0 else "d20"
            
            # Roll attack
            attack_result = await self.roller.roll(
                attack_expr,
                interaction.user.id,
                interaction.guild_id or 0,
                interaction.channel_id or 0
            )
            
            # Roll damage
            damage_result = await self.roller.roll(
                damage_dice,
                interaction.user.id,
                interaction.guild_id or 0,
                interaction.channel_id or 0
            )
            
            # Create embed
            embed = discord.Embed(
                title="⚔️ Attack Roll",
                color=0xff0000
            )
            
            if weapon:
                embed.add_field(name="Weapon", value=weapon, inline=True)
            embed.add_field(name="Attack Bonus", value=f"{attack_bonus:+d}", inline=True)
            adv_text = advantage if advantage else "Normal"
            embed.add_field(name="Type", value=adv_text, inline=True)
            
            embed.add_field(
                name="Attack Result",
                value=f"**{attack_result.final_value}**",
                inline=False
            )
            embed.add_field(
                name="Attack Details",
                value=self.roller.format_result(attack_result),
                inline=False
            )
            
            embed.add_field(
                name="Damage Result",
                value=f"**{damage_result.final_value}**",
                inline=False
            )
            embed.add_field(
                name="Damage Details",
                value=self.roller.format_result(damage_result),
                inline=False
            )
            
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=private)
            
        except DiceError as e:
            await interaction.response.send_message(
                f"❌ **Error**\n{str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Attack roll failed: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An unexpected error occurred.",
                ephemeral=True
            )
    
    @attack_roll.autocomplete('advantage')
    async def attack_advantage_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for advantage parameter"""
        choices = [
            app_commands.Choice(name="Normal", value="Normal"),
            app_commands.Choice(name="Advantage", value="Advantage"),
            app_commands.Choice(name="Disadvantage", value="Disadvantage")
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]
    
    @app_commands.command(name="stats", description="Generate D&D character ability scores")
    @app_commands.describe(
        method="Ability score generation method",
        private="Show result privately"
    )
    async def generate_stats(self, interaction: discord.Interaction,
                           method: Optional[str] = None,
                           private: bool = True):
        """Generate character ability scores using advanced roller"""
        try:
            method_value = method if method else "4d6 Drop Lowest"
            
            if method_value == "Standard Array":
                # D&D 5e standard array
                stats = [15, 14, 13, 12, 10, 8]
                embed = discord.Embed(
                    title="📊 Ability Scores - Standard Array",
                    description="D&D 5e standard ability array\nAssign to: Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma",
                    color=0x9932cc
                )
                embed.add_field(
                    name="Ability Values",
                    value=" | ".join([f"**{stat}**" for stat in stats]),
                    inline=False
                )
                
            elif method_value == "4d6 Drop Lowest":
                # Roll 4d6 drop lowest 6 times
                results = []
                for _ in range(6):
                    result = await self.roller.roll(
                        "4d6kh3",
                        interaction.user.id,
                        interaction.guild_id or 0,
                        interaction.channel_id or 0
                    )
                    results.append(result)
                
                stats = [r.final_value for r in results]
                
                embed = discord.Embed(
                    title="📊 Ability Scores - 4d6 Drop Lowest",
                    description="Roll 4d6 for 6 abilities, keep highest 3\nAssign to: Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma",
                    color=0x9932cc
                )
                
                embed.add_field(
                    name="Ability Values",
                    value=" | ".join([f"**{stat}**" for stat in stats]),
                    inline=False
                )
                
                # Display roll details
                details_list = []
                for i, result in enumerate(results):
                    details_list.append(f"{i+1}. {self.roller.format_result(result)}")
                
                embed.add_field(
                    name="Roll Details (1-3)",
                    value="\n".join(details_list[:3]),
                    inline=True
                )
                
                if len(details_list) > 3:
                    embed.add_field(
                        name="Roll Details (4-6)",
                        value="\n".join(details_list[3:]),
                        inline=True
                    )
                
            else:  # 3d6
                # Roll 3d6 six times
                results = []
                for _ in range(6):
                    result = await self.roller.roll(
                        "3d6",
                        interaction.user.id,
                        interaction.guild_id or 0,
                        interaction.channel_id or 0
                    )
                    results.append(result)
                
                stats = [r.final_value for r in results]
                
                embed = discord.Embed(
                    title="📊 Ability Scores - 3d6",
                    description="Roll 3d6 for 6 abilities\nAssign to: Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma",
                    color=0x9932cc
                )
                
                embed.add_field(
                    name="Ability Values",
                    value=" | ".join([f"**{stat}**" for stat in stats]),
                    inline=False
                )
                
                # Display roll details
                details_list = []
                for i, result in enumerate(results):
                    details_list.append(f"{i+1}. {self.roller.format_result(result)}")
                
                embed.add_field(
                    name="Roll Details (1-3)",
                    value="\n".join(details_list[:3]),
                    inline=True
                )
                
                if len(details_list) > 3:
                    embed.add_field(
                        name="Roll Details (4-6)",
                        value="\n".join(details_list[3:]),
                        inline=True
                    )
            
            # Calculate modifiers and statistics
            modifiers = [(stat - 10) // 2 for stat in stats]
            modifier_str = " | ".join([f"{mod:+d}" for mod in modifiers])
            
            embed.add_field(
                name="Ability Modifiers",
                value=modifier_str,
                inline=False
            )
            
            total = sum(stats)
            average = total / 6
            embed.add_field(
                name="Statistics",
                value=f"Total: {total} | Average: {average:.1f}",
                inline=False
            )
            
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=private)
            
        except DiceError as e:
            await interaction.response.send_message(
                f"❌ **Error**\n{str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Ability score generation failed: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ An unexpected error occurred.",
                ephemeral=True
            )
    
    @generate_stats.autocomplete('method')
    async def method_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for method parameter"""
        choices = [
            app_commands.Choice(name="4d6 Drop Lowest", value="4d6 Drop Lowest"),
            app_commands.Choice(name="Standard Array", value="Standard Array"),
            app_commands.Choice(name="3d6", value="3d6")
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]


async def setup(bot):
    """Set up advanced dice command group"""
    await bot.add_cog(AdvancedDiceCommands(bot))
