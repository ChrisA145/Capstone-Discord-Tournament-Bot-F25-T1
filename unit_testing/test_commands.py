import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord import Interaction, Permissions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller.checkin_controller import CheckinController
from controller.player_management import PlayerManagement
from controller.tier_management import TierManagement


@pytest.fixture
def test_bot():
    return MagicMock()

@pytest.fixture
def admin_user():
    """Creates a mock user with administrator permissions."""
    user = MagicMock()
    user.guild_permissions = Permissions(administrator=True)
    return user

@pytest.fixture
def non_admin_user():
    """Creates a mock user without administrator permissions."""
    user = MagicMock()
    user.guild_permissions = Permissions(administrator=False)
    return user

@pytest.fixture
def mock_interaction(admin_user):
    """Creates a mock interaction with an admin user."""
    interaction = MagicMock(spec=Interaction)
    interaction.user = admin_user
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction

@pytest.fixture
def mock_interaction_non_admin(non_admin_user):
    """Creates a mock interaction with a non-admin user."""
    interaction = MagicMock(spec=Interaction)
    interaction.user = non_admin_user
    interaction.response.send_message = AsyncMock()
    return interaction

@pytest.mark.asyncio
async def test_checkin_admin(test_bot, mock_interaction):
    """Test that the /checkin_game command executes successfully for admins."""
    cog = CheckinController(test_bot)
    
    # Mock the settings
    with patch("controller.checkin_controller.settings") as mock_settings:
        # Set the correct channel name
        mock_settings.TOURNAMENT_CH = "tournament-channel"
        
        # Mock the channel search
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.send = AsyncMock()
        mock_channel.name = "tournament-channel"
        
        # Set up the mock channel in the guild
        mock_interaction.guild.channels = [mock_channel]
        
        with patch("controller.checkin_controller.CheckinView", return_value=MagicMock()) as mock_view, \
             patch("asyncio.sleep", AsyncMock()) as mock_sleep:
             
            mock_view.return_value.message = MagicMock()
            
            # Execute the command
            await cog.checkin.callback(cog, mock_interaction, timeout=60)

            # Assert the interaction response
            mock_interaction.response.send_message.assert_called_once_with(
                f"Invitation successfully sent to {mock_channel.name}")
            
            # We don't need to assert mock_sleep because we've patched it to return immediately

@pytest.mark.asyncio
async def test_checkin_non_admin(test_bot, mock_interaction_non_admin):
    """Test that non-admins cannot execute the /checkin_game command."""
    cog = CheckinController(test_bot)

    await cog.checkin.callback(cog, mock_interaction_non_admin, timeout=60)

    mock_interaction_non_admin.response.send_message.assert_called_once_with(
        "Sorry you dont have required permission to use this command", ephemeral=True
    )

@pytest.mark.asyncio
async def test_view_player_tier_admin(test_bot, mock_interaction):
    """Test /view_player_tier command for admins with a valid player."""
    cog = TierManagement(test_bot)
    
    with patch("controller.tier_management.Tournament_DB") as mock_db_class, \
         patch("controller.tier_management.Game") as mock_game_class:
         
        mock_db = MagicMock()
        mock_game = MagicMock()
        mock_db_class.return_value = mock_db
        mock_game_class.return_value = mock_game
        
        # Set up mock cursor and fetchone results
        mock_db.cursor.execute = MagicMock()
        mock_db.cursor.fetchone = MagicMock(side_effect=[
            (123, "TestPlayer", "TAG123"),  # First call returns player data
            ("Gold", "II", 7.5)            # Second call returns tier data
        ])
        
        await cog.view_player_tier.callback(cog, mock_interaction, player_name="TestPlayer")
        
        # Check that the correct SQL queries were executed
        mock_db.cursor.execute.assert_any_call(
            "SELECT user_id, game_name, tag_id FROM player WHERE game_name LIKE ?", 
            ("%TestPlayer%",)
        )
        mock_db.cursor.execute.assert_any_call(
            "SELECT tier, rank, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
            (123,)
        )
        
        # Check that response.send_message was called with an embed
        mock_interaction.response.send_message.assert_called_once()
        embed = mock_interaction.response.send_message.call_args.kwargs['embed']
        assert embed.title == "Player Tier: TestPlayer"
        
        # Check that database connections were closed
        mock_db.close_db.assert_called_once()
        mock_game.close_db.assert_called_once()

@pytest.mark.asyncio
async def test_view_player_tier_invalid_player(test_bot, mock_interaction):
    """Test /view_player_tier when an invalid player is given."""
    cog = TierManagement(test_bot)

    with patch("controller.tier_management.Tournament_DB") as mock_db_class, \
         patch("controller.tier_management.Game") as mock_game_class:
         
        mock_db = MagicMock()
        mock_game = MagicMock()
        mock_db_class.return_value = mock_db
        mock_game_class.return_value = mock_game
        
        # Set up mock cursor to return no player
        mock_db.cursor.execute = MagicMock()
        mock_db.cursor.fetchone = MagicMock(return_value=None)
        
        await cog.view_player_tier.callback(cog, mock_interaction, player_name="NonExistentPlayer")
        
        # Check response for player not found
        mock_interaction.response.send_message.assert_called_once_with(
            "Player 'NonExistentPlayer' not found", ephemeral=True
        )
        
        # Check that database connections were closed
        mock_db.close_db.assert_called_once()
        mock_game.close_db.assert_called_once()

@pytest.mark.asyncio
async def test_view_player_tier_non_admin(test_bot, mock_interaction_non_admin):
    """Test that non-admins cannot use the /view_player_tier command."""
    cog = TierManagement(test_bot)

    await cog.view_player_tier.callback(cog, mock_interaction_non_admin, player_name="TestPlayer")

    mock_interaction_non_admin.response.send_message.assert_called_once_with(
        "Sorry, you don't have required permission to use this command", ephemeral=True
    )

@pytest.mark.asyncio
async def test_toxicity_update_admin(test_bot, mock_interaction):
    """Test the /toxicity command for admins when a valid player is found."""
    cog = PlayerManagement(test_bot)

    with patch("controller.player_management.PlayerModel.update_toxicity", return_value=True):
        await cog.toxicity.callback(cog, mock_interaction, player="toxic_player")

        mock_interaction.response.send_message.assert_called_once_with(
            "toxic_player's toxicity point has been updated.", ephemeral=True
        )

@pytest.mark.asyncio
async def test_toxicity_update_invalid_player(test_bot, mock_interaction):
    """Test the /toxicity command when a player is not found."""
    cog = PlayerManagement(test_bot)

    with patch("controller.player_management.PlayerModel.update_toxicity", return_value=False):
        await cog.toxicity.callback(cog, mock_interaction, player="unknown_player")

        mock_interaction.response.send_message.assert_called_once_with(
            "unknown_player, this username could not be found.", ephemeral=True
        )

@pytest.mark.asyncio
async def test_toxicity_update_non_admin(test_bot, mock_interaction_non_admin):
    """Test that non-admins cannot use the /toxicity command."""
    cog = PlayerManagement(test_bot)

    await cog.toxicity.callback(cog, mock_interaction_non_admin, player="some_player")

    mock_interaction_non_admin.response.send_message.assert_called_once_with(
        "❌ This command is only for administrators.", ephemeral=True
    )

@pytest.mark.asyncio
async def test_get_toxicity(test_bot, mock_interaction):
    """Test the /get_toxicity command when a player is found."""
    cog = PlayerManagement(test_bot)
    
    with patch("controller.player_management.Player") as mock_player_class:
        mock_player = MagicMock()
        mock_player_class.return_value = mock_player
        
        # Mock finding player and getting toxicity points
        mock_player.find_player_by_name.return_value = 123
        mock_player.get_toxicity_points.return_value = 5
        
        await cog.get_toxicity.callback(cog, mock_interaction, player="toxic_player")
        
        # Check that the correct methods were called
        mock_player.find_player_by_name.assert_called_once_with("toxic_player")
        mock_player.get_toxicity_points.assert_called_once_with(123)
        mock_player.close_db.assert_called_once()
        
        # Check the response
        mock_interaction.response.send_message.assert_called_once_with(
            "toxic_player has 5 toxicity point(s).", ephemeral=True
        )

@pytest.mark.asyncio
async def test_get_toxicity_player_not_found(test_bot, mock_interaction):
    """Test the /get_toxicity command when a player is not found."""
    cog = PlayerManagement(test_bot)
    
    with patch("controller.player_management.Player") as mock_player_class:
        mock_player = MagicMock()
        mock_player_class.return_value = mock_player
        
        # Mock player not found
        mock_player.find_player_by_name.return_value = None
        
        await cog.get_toxicity.callback(cog, mock_interaction, player="unknown_player")
        
        # Check that the correct methods were called
        mock_player.find_player_by_name.assert_called_once_with("unknown_player")
        mock_player.close_db.assert_called_once()
        
        # Check the response
        mock_interaction.response.send_message.assert_called_once_with(
            "unknown_player, this username could not be found.", ephemeral=True
        )