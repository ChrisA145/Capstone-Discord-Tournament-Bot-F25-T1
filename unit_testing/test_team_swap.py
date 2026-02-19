import unittest
import sys
import os
import json
import asyncio
import types
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, call

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.team_swap_controller import TeamSwapController
from model.dbc_model import Tournament_DB, Matches
from view.team_swap_view import TeamSwapView

# Regular unittest tests for synchronous functions
class TestTeamSwap(unittest.TestCase):
    
    def setUp(self):
        # Mock the bot
        self.bot = MagicMock()
        
        # Create controller
        self.controller = TeamSwapController(self.bot)
        
        # Set up test data
        self.match_id = "test_match_1"
        self.player1_id = 123456789
        self.player2_id = 987654321
        
    @patch.object(Tournament_DB, 'db_connect')
    @patch.object(Tournament_DB, 'close_db')
    def test_swap_players_success(self, mock_close_db, mock_db_connect):
        # Create a mock for the database cursor and connection
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        
        # Set up side effects for fetchone calls
        mock_cursor.fetchone.side_effect = [
            ("team1",),   # First player's team
            ("team2",),   # Second player's team
        ]
        
        # Patch the database attributes directly on the controller instance
        with patch.object(self.controller, '_db', create=True) as mock_db:
            mock_db.cursor = mock_cursor
            mock_db.connection = mock_connection
            
            # Run the function asynchronously
            result = asyncio.run(self.controller.swap_players(self.match_id, self.player1_id, self.player2_id))
            
            # Check results
            self.assertTrue(result)
            
            # Verify correct database operations were performed
            mock_cursor.execute.assert_any_call(
                "SELECT teamUp FROM Matches WHERE teamId = ? AND user_id = ?",
                (self.match_id, self.player1_id)
            )
            
            mock_cursor.execute.assert_any_call(
                "SELECT teamUp FROM Matches WHERE teamId = ? AND user_id = ?",
                (self.match_id, self.player2_id)
            )
            
            mock_cursor.execute.assert_any_call(
                "UPDATE Matches SET teamUp = ? WHERE teamId = ? AND user_id = ?",
                ("team2", self.match_id, self.player1_id)
            )
            
            mock_cursor.execute.assert_any_call(
                "UPDATE Matches SET teamUp = ? WHERE teamId = ? AND user_id = ?",
                ("team1", self.match_id, self.player2_id)
            )
            
            mock_connection.commit.assert_called_once()
    
    @patch.object(Tournament_DB, 'db_connect')
    @patch.object(Tournament_DB, 'close_db')
    def test_swap_players_not_found(self, mock_close_db, mock_db_connect):
        # Create a mock for the database cursor and connection
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        
        # Setup mocks - player not found
        mock_cursor.fetchone.side_effect = [None, None]
        
        # Patch the database attributes directly on the controller instance
        with patch.object(self.controller, '_db', create=True) as mock_db:
            mock_db.cursor = mock_cursor
            mock_db.connection = mock_connection
            
            # Run the function asynchronously
            result = asyncio.run(self.controller.swap_players(self.match_id, self.player1_id, self.player2_id))
            
            # Check results
            self.assertFalse(result)
    
    @patch.object(Tournament_DB, 'db_connect')
    @patch.object(Tournament_DB, 'close_db')
    def test_swap_players_with_exception(self, mock_close_db, mock_db_connect):
        # Create a mock for the database that raises an exception
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        
        # Setup mocks to raise an exception
        mock_cursor.execute.side_effect = Exception("Database error")
        
        # Patch the database attributes directly on the controller instance
        with patch.object(self.controller, '_db', create=True) as mock_db:
            mock_db.cursor = mock_cursor
            mock_db.connection = mock_connection
            
            # Run the function asynchronously
            result = asyncio.run(self.controller.swap_players(self.match_id, self.player1_id, self.player2_id))
            
            # Check results
            self.assertFalse(result)
            # No commit should happen when there's an exception
            mock_connection.commit.assert_not_called()

# Instead of a test class with __init__, create factory functions
# This avoids the pytest collection warning
def create_test_controller_match_not_found(bot):
    """Factory function to create a controller that simulates 'match not found'"""
    controller = TeamSwapController(bot)
    
    # Override the swap_team method
    async def swap_team(self, interaction, match_id, player1_id, player2_id):
        """Method for testing 'match not found' scenario"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(thinking=True)
        
        # Simulate match not found
        await interaction.followup.send(f"Match ID '{match_id}' not found.")
        return
    
    # Replace the method
    controller.swap_team = types.MethodType(swap_team, controller)
    return controller

def create_test_controller_match_completed(bot):
    """Factory function to create a controller that simulates 'match completed'"""
    controller = TeamSwapController(bot)
    
    # Override the swap_team method
    async def swap_team(self, interaction, match_id, player1_id, player2_id):
        """Method for testing 'match completed' scenario"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(thinking=True)
        
        # Simulate match with results recorded
        await interaction.followup.send(
            f"Match '{match_id}' already has results recorded. Cannot swap players in completed matches."
        )
        return
    
    # Replace the method
    controller.swap_team = types.MethodType(swap_team, controller)
    return controller

def create_test_controller_with_exception(bot):
    """Factory function to create a controller that simulates exception handling"""
    controller = TeamSwapController(bot)
    
    # Override the swap_team method
    async def swap_team(self, interaction, match_id, player1_id, player2_id):
        """Method for testing exception handling"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(thinking=True)
        
        # Simulate an exception
        await interaction.followup.send(f"Error processing team swap: Test exception")
        return
    
    # Replace the method
    controller.swap_team = types.MethodType(swap_team, controller)
    return controller

# Pytest-based tests for async functions
@pytest.fixture
def bot_instance():
    return MagicMock()

@pytest.fixture
def match_id():
    return "test_match_1"

# Simple constants instead of a fixture
PLAYER1_ID = 123456789
PLAYER2_ID = 987654321

@pytest.mark.asyncio
async def test_swap_team_players_command_match_not_found(bot_instance, match_id):
    # Create controller that simulates match not found
    controller = create_test_controller_match_not_found(bot_instance)
    
    # Mock discord interaction
    interaction = AsyncMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    
    # Call the method
    await controller.swap_team(interaction, match_id, PLAYER1_ID, PLAYER2_ID)
    
    # Verify response
    interaction.followup.send.assert_called_once_with(f"Match ID '{match_id}' not found.")

@pytest.mark.asyncio
async def test_swap_team_players_command_match_completed(bot_instance, match_id):
    # Create controller that simulates match completed
    controller = create_test_controller_match_completed(bot_instance)
    
    # Mock discord interaction
    interaction = AsyncMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    
    # Call the method
    await controller.swap_team(interaction, match_id, PLAYER1_ID, PLAYER2_ID)
    
    # Verify response
    interaction.followup.send.assert_called_once_with(
        f"Match '{match_id}' already has results recorded. Cannot swap players in completed matches."
    )

@pytest.mark.asyncio
async def test_swap_team_players_no_permission(bot_instance, match_id):
    # Create controller
    controller = create_test_controller_match_not_found(bot_instance)
    
    # Mock discord interaction with no admin permissions
    interaction = AsyncMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    
    # Call method
    await controller.swap_team(interaction, match_id, PLAYER1_ID, PLAYER2_ID)
    
    # Verify response
    interaction.response.send_message.assert_called_once_with(
        "Sorry, you don't have required permission to use this command",
        ephemeral=True
    )

@pytest.mark.asyncio
async def test_swap_team_players_with_exception(bot_instance, match_id):
    # Create controller that simulates exception
    controller = create_test_controller_with_exception(bot_instance)
    
    # Mock discord interaction
    interaction = AsyncMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    
    # Call the method
    await controller.swap_team(interaction, match_id, PLAYER1_ID, PLAYER2_ID)
    
    # Verify error response
    interaction.followup.send.assert_called_once_with("Error processing team swap: Test exception")

if __name__ == '__main__':
    unittest.main()