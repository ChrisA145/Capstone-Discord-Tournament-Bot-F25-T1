import unittest
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock necessary modules before importing genetic_match_making
sys.modules['discord'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['config.settings'] = MagicMock()
sys.modules['model.dbc_model'] = MagicMock()
sys.modules['model.dbc_model.Tournament_DB'] = MagicMock()
sys.modules['model.dbc_model.Game'] = MagicMock()
sys.modules['model.dbc_model.Player'] = MagicMock()

# Mock logger
logger = MagicMock()
logger.error = MagicMock()
logger.warning = MagicMock()
logger.info = MagicMock()

# Now import the module we want to test
from controller.genetic_match_making import GeneticMatchMaking
# Patch logger
GeneticMatchMaking.logger = logger

class TestRoleAssignment(unittest.TestCase):
    
    def setUp(self):
        self.matchmaker = GeneticMatchMaking()
        
        # Create test teams with role preferences and performance data
        self.test_team = [
            {
                'user_id': 'player1',
                'game_name': 'Player1',
                'tier': 'gold',
                'rank': 'II',
                'role': ['mid', 'top', 'jungle'],
                'roleBasedPerformance': {
                    'mid': 0.8, 
                    'top': 0.7, 
                    'jungle': 0.6,
                    'forced': 0.5
                }
            },
            {
                'user_id': 'player2',
                'game_name': 'Player2',
                'tier': 'silver',
                'rank': 'I',
                'role': ['support', 'mid'],
                'roleBasedPerformance': {
                    'support': 0.75, 
                    'mid': 0.65,
                    'forced': 0.5
                }
            },
            {
                'user_id': 'player3',
                'game_name': 'Player3',
                'tier': 'platinum',
                'rank': 'IV',
                'role': ['jungle', 'top', 'mid'],
                'roleBasedPerformance': {
                    'jungle': 0.85, 
                    'top': 0.75, 
                    'mid': 0.65, 
                    'forced': 0.5
                }
            },
            {
                'user_id': 'player4',
                'game_name': 'Player4',
                'tier': 'gold',
                'rank': 'III',
                'role': ['bottom', 'mid'],
                'roleBasedPerformance': {
                    'bottom': 0.8, 
                    'mid': 0.7, 
                    'forced': 0.5
                }
            },
            {
                'user_id': 'player5',
                'game_name': 'Player5',
                'tier': 'diamond',
                'rank': 'IV',
                'role': ['top', 'support', 'mid'],
                'roleBasedPerformance': {
                    'top': 0.9, 
                    'support': 0.8, 
                    'mid': 0.7, 
                    'forced': 0.5
                }
            }
        ]
        
    def test_assign_team_roles_assigns_all_roles(self):
        """Test that all standard roles are assigned exactly once"""
        assigned_team = self.matchmaker.assign_team_roles(self.test_team)
        
        # Check that all 5 players have an assigned role
        self.assertEqual(len(assigned_team), 5)
        
        # Check that each player has an assigned_role
        for player in assigned_team:
            self.assertIn('assigned_role', player)
        
        # Get all assigned roles
        assigned_roles = [player['assigned_role'] for player in assigned_team]
        
        # Check that each standard role appears exactly once
        standard_roles = ["top", "jungle", "mid", "bottom", "support"]
        for role in standard_roles:
            self.assertEqual(assigned_roles.count(role), 1, 
                             f"Role '{role}' should be assigned exactly once, but was assigned {assigned_roles.count(role)} times")
    
    def test_assign_team_roles_optimizes_performance(self):
        """Test that roles are assigned to optimize performance"""
        assigned_team = self.matchmaker.assign_team_roles(self.test_team)
        
        # Find the player assigned to top
        top_player = next(p for p in assigned_team if p['assigned_role'] == 'top')
        
        # Player5 has the highest top lane performance, so should be assigned there
        self.assertEqual(top_player['user_id'], 'player5', 
                         "Player with highest top performance should be assigned top")
        
        # Find the player assigned to jungle
        jungle_player = next(p for p in assigned_team if p['assigned_role'] == 'jungle')
        
        # Player3 has the highest jungle performance, so should be assigned there
        self.assertEqual(jungle_player['user_id'], 'player3',
                         "Player with highest jungle performance should be assigned jungle")
    
    def test_assign_team_roles_handles_missing_preferences(self):
        """Test that roles can be assigned even when players don't have all role preferences"""
        # Add a player with limited role preferences
        self.test_team.append({
            'user_id': 'player6',
            'game_name': 'Player6',
            'tier': 'gold',
            'rank': 'I',
            'role': ['mid'],  # Only one role preference
            'roleBasedPerformance': {
                'mid': 0.95,  # Very high mid performance
                'forced': 0.5
            }
        })
        
        # Remove one player to keep team size at 5
        test_team = self.test_team[1:]
        
        assigned_team = self.matchmaker.assign_team_roles(test_team)
        
        # Check that each role is still assigned exactly once
        assigned_roles = [player['assigned_role'] for player in assigned_team]
        standard_roles = ["top", "jungle", "mid", "bottom", "support"]
        for role in standard_roles:
            self.assertEqual(assigned_roles.count(role), 1, 
                             f"Role '{role}' should be assigned exactly once, but was assigned {assigned_roles.count(role)} times")
        
        # Player6 should be assigned mid because they have highest mid performance
        mid_player = next(p for p in assigned_team if p['assigned_role'] == 'mid')
        self.assertEqual(mid_player['user_id'], 'player6',
                         "Player with highest mid performance should be assigned mid")

if __name__ == '__main__':
    unittest.main()