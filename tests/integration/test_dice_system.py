"""
Integration Tests for Advanced Dice System
Tests end-to-end flows from expression to Discord response
Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
"""
import pytest
import asyncio
import discord
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from dice.advanced_roller import AdvancedDiceRoller
from dice.dice_commands import AdvancedDiceCommands
from dice.exceptions import ParseError, ValidationError, UnsupportedFeatureError
import json

# Use anyio for async test support, only run with asyncio backend
pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::trio.TrioDeprecationWarning")]


@pytest.fixture
def roller():
    """Create a fresh roller instance for each test"""
    return AdvancedDiceRoller()


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot"""
    bot = Mock()
    bot.user = Mock()
    bot.user.id = 123456789
    return bot


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction"""
    interaction = Mock(spec=discord.Interaction)
    interaction.user = Mock()
    interaction.user.id = 987654321
    interaction.user.display_name = "TestUser"
    interaction.user.display_avatar = Mock()
    interaction.user.display_avatar.url = "https://example.com/avatar.png"
    interaction.guild_id = 111222333
    interaction.channel_id = 444555666
    interaction.response = AsyncMock()
    return interaction


@pytest.fixture
def dice_commands(mock_bot):
    """Create dice commands cog"""
    return AdvancedDiceCommands(mock_bot)


class TestBasicRollCommand:
    """Test /r command end-to-end flow"""
    
    async def test_simple_roll_success(self, dice_commands, mock_interaction):
        """Test basic roll command with simple expression"""
        # Requirement 10.1: Parse and evaluate dice expression
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "2d6+3", False)
        
        # Should send a response
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Should have an embed
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        assert isinstance(embed, discord.Embed)
        
        # Requirement 10.2: Display original expression, final result, and breakdown
        embed_dict = embed.to_dict()
        assert 'title' in embed_dict
        assert 'fields' in embed_dict
        
        # Should have result and breakdown fields
        field_names = [f['name'] for f in embed_dict['fields']]
        assert 'Result' in field_names or 'Final Result' in field_names
    
    
    async def test_advantage_roll(self, dice_commands, mock_interaction):
        """Test advantage roll (2d20kh1)"""
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "2d20kh1+5", False)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        
        # Requirement 10.3: Display dropped dice with strikethrough
        # The embed should contain the breakdown
        embed_dict = embed.to_dict()
        assert 'fields' in embed_dict
    
    
    async def test_success_counting_roll(self, dice_commands, mock_interaction):
        """Test success counting expression"""
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "10d6>=5", False)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        
        # Requirement 10.4: Display success count and dice list
        embed_dict = embed.to_dict()
        assert 'fields' in embed_dict
    
    
    async def test_complex_expression(self, dice_commands, mock_interaction):
        """Test complex multi-dice expression"""
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "1d8+2d6kh1+3", False)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
    
    
    async def test_private_roll(self, dice_commands, mock_interaction):
        """Test private roll (ephemeral message)"""
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "d20", True)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Should be ephemeral
        assert call_args.kwargs.get('ephemeral') == True


class TestErrorHandling:
    """Test error handling paths"""
    
    
    async def test_invalid_syntax_error(self, dice_commands, mock_interaction):
        """Test invalid syntax produces user-friendly error"""
        # Requirement 10.5: Display error message visible only to user
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "2d", False)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Should be ephemeral error message
        assert call_args.kwargs.get('ephemeral') == True
        
        # Should contain error indicator
        message = call_args.args[0] if call_args.args else ""
        assert "❌" in message or "Error" in message
    
    
    async def test_unsupported_feature_error(self, dice_commands, mock_interaction):
        """Test unsupported feature (exploding dice) produces error"""
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "2d6!", False)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Should be ephemeral error
        assert call_args.kwargs.get('ephemeral') == True
        
        # Should mention unsupported feature
        message = call_args.args[0] if call_args.args else ""
        assert "Unsupported" in message or "not supported" in message.lower()
    
    
    async def test_validation_error(self, dice_commands, mock_interaction):
        """Test validation error for excessive dice count"""
        await dice_commands.roll_dice.callback(dice_commands, mock_interaction, "100000d6", False)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Should be ephemeral error
        assert call_args.kwargs.get('ephemeral') == True
        
        # Should mention validation
        message = call_args.args[0] if call_args.args else ""
        assert "❌" in message


class TestCheckCommand:
    """Test /check command"""
    
    
    async def test_normal_skill_check(self, dice_commands, mock_interaction):
        """Test normal skill check"""
        await dice_commands.skill_check.callback(dice_commands, 
            mock_interaction,
            modifier=5,
            advantage=None,
            skill="Perception",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        embed_dict = embed.to_dict()
        
        # Should show skill check title
        assert 'Skill Check' in embed_dict.get('title', '')
    
    
    async def test_advantage_skill_check(self, dice_commands, mock_interaction):
        """Test skill check with advantage"""
        await dice_commands.skill_check.callback(dice_commands, 
            mock_interaction,
            modifier=3,
            advantage="Advantage",
            skill="Stealth",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
    
    
    async def test_disadvantage_skill_check(self, dice_commands, mock_interaction):
        """Test skill check with disadvantage"""
        await dice_commands.skill_check.callback(dice_commands, 
            mock_interaction,
            modifier=-1,
            advantage="Disadvantage",
            skill="Athletics",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()


class TestSaveCommand:
    """Test /save command"""
    
    
    async def test_normal_saving_throw(self, dice_commands, mock_interaction):
        """Test normal saving throw"""
        await dice_commands.saving_throw.callback(dice_commands, 
            mock_interaction,
            save_type="Dexterity",
            modifier=2,
            advantage=None,
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        embed_dict = embed.to_dict()
        
        # Should show saving throw title
        assert 'Saving Throw' in embed_dict.get('title', '')
    
    
    async def test_advantage_saving_throw(self, dice_commands, mock_interaction):
        """Test saving throw with advantage"""
        await dice_commands.saving_throw.callback(dice_commands, 
            mock_interaction,
            save_type="Wisdom",
            modifier=4,
            advantage="Advantage",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()


class TestAttackCommand:
    """Test /att command"""
    
    
    async def test_normal_attack(self, dice_commands, mock_interaction):
        """Test normal attack roll"""
        await dice_commands.attack_roll.callback(dice_commands, 
            mock_interaction,
            attack_bonus=5,
            damage_dice="1d8+3",
            advantage=None,
            weapon="Longsword",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        embed_dict = embed.to_dict()
        
        # Should show attack roll title
        assert 'Attack' in embed_dict.get('title', '')
        
        # Should have both attack and damage results
        field_names = [f['name'] for f in embed_dict.get('fields', [])]
        assert any('Attack' in name for name in field_names)
        assert any('Damage' in name for name in field_names)
    
    
    async def test_advantage_attack(self, dice_commands, mock_interaction):
        """Test attack with advantage"""
        await dice_commands.attack_roll.callback(dice_commands, 
            mock_interaction,
            attack_bonus=7,
            damage_dice="2d6+4",
            advantage="Advantage",
            weapon="Greatsword",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()
    
    
    async def test_attack_with_complex_damage(self, dice_commands, mock_interaction):
        """Test attack with complex damage expression"""
        await dice_commands.attack_roll.callback(dice_commands, 
            mock_interaction,
            attack_bonus=3,
            damage_dice="1d6+1d4+2",
            advantage=None,
            weapon="Shortsword",
            private=False
        )
        
        mock_interaction.response.send_message.assert_called_once()


class TestStatsCommand:
    """Test /stats command"""
    
    
    async def test_4d6_drop_lowest(self, dice_commands, mock_interaction):
        """Test ability score generation with 4d6 drop lowest"""
        await dice_commands.generate_stats.callback(dice_commands, 
            mock_interaction,
            method="4d6 Drop Lowest",
            private=True
        )
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        embed_dict = embed.to_dict()
        
        # Should show ability scores title
        assert 'Ability Scores' in embed_dict.get('title', '')
        
        # Should be private by default
        assert call_args.kwargs.get('ephemeral') == True
    
    
    async def test_standard_array(self, dice_commands, mock_interaction):
        """Test standard array generation"""
        await dice_commands.generate_stats.callback(dice_commands, 
            mock_interaction,
            method="Standard Array",
            private=True
        )
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        assert 'embed' in call_args.kwargs
    
    
    async def test_3d6_method(self, dice_commands, mock_interaction):
        """Test 3d6 ability score generation"""
        await dice_commands.generate_stats.callback(dice_commands, 
            mock_interaction,
            method="3d6",
            private=True
        )
        
        mock_interaction.response.send_message.assert_called_once()


class TestDatabasePersistence:
    """Test database persistence of rolls"""
    
    
    async def test_roll_saved_to_database(self, roller):
        """Test that rolls are saved to database with all required fields"""
        # Mock database manager
        with patch('database.db_manager') as mock_db:
            mock_db.get_user_by_discord_id = AsyncMock(return_value={'id': 1})
            mock_db.get_guild_by_discord_id = AsyncMock(return_value={'id': 1})
            mock_db.log_dice_roll = AsyncMock(return_value=1)
            
            # Roll dice
            result = await roller.roll("2d6+3", 123, 456, 789)
            
            # Verify database was called
            mock_db.log_dice_roll.assert_called_once()
            call_args = mock_db.log_dice_roll.call_args
            
            # Requirement 11.2: Should include user_id, guild_id, channel_id
            assert call_args.kwargs['user_id'] == 1
            assert call_args.kwargs['guild_id'] == 1
            assert call_args.kwargs['channel_id'] == 789
            
            # Requirement 11.1: Should include expression and result
            assert call_args.kwargs['dice_expression'] == "2d6+3"
            assert 'result' in call_args.kwargs
            
            # Requirement 11.3: Should include complete breakdown
            assert 'details' in call_args.kwargs
            details = json.loads(call_args.kwargs['details'])
            assert 'dice_results' in details
    
    
    async def test_roll_with_keep_drop_saved(self, roller):
        """Test that rolls with keep/drop are saved with kept/dropped status"""
        with patch('database.db_manager') as mock_db:
            mock_db.get_user_by_discord_id = AsyncMock(return_value={'id': 1})
            mock_db.get_guild_by_discord_id = AsyncMock(return_value={'id': 1})
            mock_db.log_dice_roll = AsyncMock(return_value=1)
            
            # Roll with keep highest
            result = await roller.roll("4d6kh3", 123, 456, 789)
            
            mock_db.log_dice_roll.assert_called_once()
            call_args = mock_db.log_dice_roll.call_args
            
            # Check details include kept/dropped status
            details = json.loads(call_args.kwargs['details'])
            assert 'dice_results' in details
            
            # Should have roll information
            dice_result = details['dice_results'][0]
            assert 'rolls' in dice_result
            
            # Each roll should have kept status
            for roll in dice_result['rolls']:
                assert 'kept' in roll
    
    
    async def test_success_count_roll_saved(self, roller):
        """Test that success counting rolls are saved correctly"""
        with patch('database.db_manager') as mock_db:
            mock_db.get_user_by_discord_id = AsyncMock(return_value={'id': 1})
            mock_db.get_guild_by_discord_id = AsyncMock(return_value={'id': 1})
            mock_db.log_dice_roll = AsyncMock(return_value=1)
            
            # Roll with success counting
            result = await roller.roll("10d6>=5", 123, 456, 789)
            
            mock_db.log_dice_roll.assert_called_once()
            call_args = mock_db.log_dice_roll.call_args
            
            # Should be marked as success_count type
            assert call_args.kwargs['roll_type'] == 'success_count'
            
            # Details should include success count
            details = json.loads(call_args.kwargs['details'])
            assert details['is_success_count'] == True
            assert 'success_count' in details
    
    
    async def test_database_error_handled_gracefully(self, roller):
        """Test that database errors don't crash the roll"""
        with patch('database.db_manager') as mock_db:
            # Simulate database error
            mock_db.get_user_by_discord_id = AsyncMock(side_effect=Exception("DB Error"))
            
            # Roll should still succeed
            result = await roller.roll("d20", 123, 456, 789)
            
            # Should have a valid result
            assert result is not None
            assert result.final_value >= 1
            assert result.final_value <= 20


class TestHelpCommand:
    """Test /rh help command"""
    
    
    async def test_help_command(self, dice_commands, mock_interaction):
        """Test help command displays documentation"""
        await dice_commands.dice_help.callback(dice_commands, mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        
        # Should be ephemeral
        assert call_args.kwargs.get('ephemeral') == True
        
        # Should have an embed
        assert 'embed' in call_args.kwargs
        embed = call_args.kwargs['embed']
        embed_dict = embed.to_dict()
        
        # Should have help title
        assert 'Help' in embed_dict.get('title', '') or 'help' in embed_dict.get('title', '').lower()
        
        # Should have multiple fields explaining features
        assert len(embed_dict.get('fields', [])) > 3


class TestEndToEndFlows:
    """Test complete end-to-end flows"""
    
    
    async def test_complete_roll_flow(self, roller):
        """Test complete flow from expression to result"""
        # Parse, evaluate, format
        result = await roller.roll("2d20kh1+5", 123, 456, 789)
        
        # Should have valid result
        assert result is not None
        assert result.expression == "2d20kh1+5"
        assert result.final_value >= 6  # Min: 1 + 5
        assert result.final_value <= 25  # Max: 20 + 5
        
        # Should have dice results
        assert len(result.dice_results) > 0
        
        # Format as string
        formatted = roller.format_result(result)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        
        # Format as embed
        embed_dict = roller.format_embed(result, "TestUser")
        assert isinstance(embed_dict, dict)
        assert 'title' in embed_dict
        assert 'fields' in embed_dict
    
    
    async def test_multiple_rolls_cached(self, roller):
        """Test that multiple rolls are cached per user"""
        user_id = 123
        
        # Roll multiple times
        result1 = await roller.roll("d20", user_id, 456, 789)
        result2 = await roller.roll("2d6", user_id, 456, 789)
        
        # Last result should be cached
        cached = roller.get_last_result(user_id)
        assert cached is not None
        assert cached.expression == "2d6"
    
    
    async def test_different_users_separate_cache(self, roller):
        """Test that different users have separate caches"""
        user1_id = 123
        user2_id = 456
        
        # Roll for different users
        result1 = await roller.roll("d20", user1_id, 789, 111)
        result2 = await roller.roll("d6", user2_id, 789, 111)
        
        # Each user should have their own cached result
        cached1 = roller.get_last_result(user1_id)
        cached2 = roller.get_last_result(user2_id)
        
        assert cached1.expression == "d20"
        assert cached2.expression == "d6"
