import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.tasks import Tasks_Collection

@pytest.mark.asyncio
async def test_promote_player_tier():
    # Create mock bot
    dummy_bot = MagicMock()
    dummy_bot.wait_until_ready = AsyncMock()
    
    # Create mock settings
    with patch('common.tasks.settings') as mock_settings:
        # Configure mock settings
        mock_settings.TIER_LIST = ['bronze', 'silver', 'gold', 'platinum']
        mock_settings.MIN_GAME_PLAYED = 10
        mock_settings.MIN_GAME_WINRATE = 62
        mock_settings.MAX_GAME_LOST = 15
        
        # Create Tasks_Collection instance with our mocked settings
        tasks_obj = Tasks_Collection(bot=dummy_bot)
        
        # Stop the task that was started in __init__
        tasks_obj.promote_player_tier.cancel()
        
        # Ensure settings were properly applied
        assert tasks_obj.tier_list == ['bronze', 'silver', 'gold', 'platinum']
        assert tasks_obj.min_game_played == 10
        assert tasks_obj.win_rate == 62
        assert tasks_obj.max_game_lost == 15

        # Simulated player data:
        # [player_id, tier, games_played, win_rate]
        mock_data = [
            [1, 'silver', 12, 65],   # should be promoted to gold
            [2, 'gold', 20, 45],     # should be demoted to silver (assumes MAX_GAME_LOST check works for any game count)
            [3, 'bronze', 5, 80],    # not enough games, no promotion
        ]

        # Mock database and relevant methods
        with patch('common.tasks.Tournament_DB') as mock_db_class, \
             patch('common.tasks.Player_game_info.fetch_for_tier_promotion') as mock_fetch, \
             patch('common.tasks.Player_game_info.update_tier') as mock_update:
            
            # Set up return values
            mock_db_instance = MagicMock()
            mock_db_class.return_value = mock_db_instance
            mock_fetch.return_value = mock_data
            
            # Call the method being tested
            await tasks_obj.promote_player_tier()

            # Verify calls to Tournament_DB
            mock_db_class.assert_called_once()
            mock_db_instance.close_db.assert_called_once()
            
            # Verify fetch_for_tier_promotion was called
            mock_fetch.assert_called_once_with(mock_db_instance)
            
            # Check promotion for player 1
            mock_update.assert_any_call(mock_db_instance, 1, 'gold')
            
            # Check demotion for player 2
            # Note: In the real code, the demotion logic is just checking player_game_played >= MAX_GAME_LOST
            mock_update.assert_any_call(mock_db_instance, 2, 'silver')
            
            # Verify player 3 was not updated (not enough games played)
            assert mock_update.call_count == 2

@pytest.mark.asyncio
async def test_before_promote_player_tier():
    # Create mock bot
    dummy_bot = MagicMock()
    dummy_bot.wait_until_ready = AsyncMock()
    
    # Create mock settings
    with patch('common.tasks.settings') as mock_settings:
        mock_settings.TIER_LIST = ['bronze', 'silver', 'gold']
        
        # Create Tasks_Collection instance with our mocked settings
        tasks_obj = Tasks_Collection(bot=dummy_bot)
        
        # Stop the task that was started in __init__
        tasks_obj.promote_player_tier.cancel()
        
        # Test the before_loop handler
        await tasks_obj.before_promote_player_tier()
        
        # Verify bot.wait_until_ready was called
        dummy_bot.wait_until_ready.assert_called_once()

@pytest.mark.asyncio
async def test_non_existent_tier():
    # Create mock bot
    dummy_bot = MagicMock()
    dummy_bot.wait_until_ready = AsyncMock()
    
    # Create mock settings and logger
    with patch('common.tasks.settings') as mock_settings, \
         patch('common.tasks.logger') as mock_logger:
        
        # Configure mock settings
        mock_settings.TIER_LIST = ['bronze', 'silver', 'gold']
        mock_settings.MIN_GAME_PLAYED = 10
        mock_settings.MIN_GAME_WINRATE = 62
        mock_settings.MAX_GAME_LOST = 15
        
        # Create Tasks_Collection instance with our mocked settings
        tasks_obj = Tasks_Collection(bot=dummy_bot)
        
        # Stop the task that was started in __init__
        tasks_obj.promote_player_tier.cancel()
        
        # Simulated player data with invalid tier
        mock_data = [
            [4, 'unknown_tier', 15, 70],  # Invalid tier
        ]

        # Mock database and relevant methods
        with patch('common.tasks.Tournament_DB') as mock_db_class, \
             patch('common.tasks.Player_game_info.fetch_for_tier_promotion') as mock_fetch, \
             patch('common.tasks.Player_game_info.update_tier') as mock_update:
            
            # Set up return values
            mock_db_instance = MagicMock()
            mock_db_class.return_value = mock_db_instance
            mock_fetch.return_value = mock_data
            
            # Call the method being tested
            await tasks_obj.promote_player_tier()

            # Verify log was called for invalid tier
            mock_logger.info.assert_called_with(f"the tier: unknown_tier is not in the {tasks_obj.tier_list}")
            
            # Verify update_tier was not called
            mock_update.assert_not_called()