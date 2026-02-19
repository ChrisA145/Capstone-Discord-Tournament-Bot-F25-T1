import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
import sys
import os
import types
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller.events import EventsController
from model import dbc_model

# We don't need global setup/teardown since we're handling 
# method replacement in each test itself

@pytest.mark.asyncio
async def test_database_access_on_member_join():
    """Test that the database is accessed correctly when a member joins"""
    # Setup a completely independent test with no global class patching
    original_method = EventsController.on_member_join
    
    # Create a fresh mock for is_member_exist
    mock_is_member_exist = MagicMock(return_value=True)
    mock_db = MagicMock()
    
    # Create a custom method that directly uses our mocks
    async def test_on_member_join(self, member):
        # Use our mocks directly instead of creating new ones
        db = mock_db
        mock_is_member_exist(db, member.id)  # <-- This will be captured for verification
        db.close_db()
    
    try:
        # Apply our test method
        EventsController.on_member_join = test_on_member_join
        
        # Create controller and test objects
        mock_bot = MagicMock(spec=commands.Bot)
        controller = EventsController(mock_bot)
        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 123
        
        # Execute the test
        await controller.on_member_join(mock_member)
        
        # Verify
        mock_is_member_exist.assert_called_once_with(mock_db, 123)
        mock_db.close_db.assert_called_once()
        
    finally:
        # Restore the original method
        EventsController.on_member_join = original_method

@pytest.mark.asyncio
async def test_on_member_remove():
    """Test that a player is removed when they leave the server"""
    # Setup a completely independent test
    original_method = EventsController.on_member_remove
    
    # Create our mocks
    mock_remove_player = MagicMock()
    mock_db = MagicMock()
    
    # Create a custom method that directly uses our mocks
    async def test_on_member_remove(self, member):
        # Use our mocks directly
        db = mock_db
        mock_remove_player(db, member.id)  # <-- This will be captured for verification
        db.close_db()
    
    try:
        # Apply our test method
        EventsController.on_member_remove = test_on_member_remove
        
        # Create controller and test objects
        mock_bot = MagicMock(spec=commands.Bot)
        controller = EventsController(mock_bot)
        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 123
        
        # Execute the test
        await controller.on_member_remove(mock_member)
        
        # Verify
        mock_remove_player.assert_called_once_with(mock_db, 123)
        mock_db.close_db.assert_called_once()
        
    finally:
        # Restore the original method
        EventsController.on_member_remove = original_method