import asyncio
import random
import json
import sys
import os

# Add function to assign roles to teams
def assign_team_roles(team):
    """
    Assign optimal roles to team members ensuring each role is assigned exactly once
    
    Args:
        team: List of player dictionaries with roleBasedPerformance data
        
    Returns:
        Team with assigned_role added to each player
    """
    # Standard roles in League of Legends
    standard_roles = ["top", "jungle", "mid", "bottom", "support"]
    
    # Create a performance matrix for all player-role combinations
    performance_matrix = {}
    for player_idx, player in enumerate(team):
        performance_matrix[player_idx] = {}
        for role in standard_roles:
            # Get player's performance for this role, or a very low value if not in preferences
            performance = player.get("roleBasedPerformance", {}).get(role, -100.0)
            performance_matrix[player_idx][role] = performance
    
    # Find optimal role assignment using a greedy algorithm
    assigned_roles = {}
    assigned_players = set()
    available_roles = set(standard_roles)
    
    # Make a copy of the team to avoid modifying the input parameter
    updated_team = []
    for player in team:
        updated_team.append(player.copy())
    
    # Sort roles by maximum performance difference between players
    role_priority = []
    for role in standard_roles:
        # Calculate performance spread for this role
        performances = [performance_matrix[player_idx][role] for player_idx in range(len(team))]
        performances = [p for p in performances if p > -100.0]  # Filter out unavailable roles
        if performances:
            spread = max(performances) - min(performances)
            role_priority.append((role, spread))
        else:
            role_priority.append((role, 0))
    
    # Sort roles by performance spread (highest first)
    role_priority.sort(key=lambda x: x[1], reverse=True)
    
    # Assign roles in priority order
    for role, _ in role_priority:
        if role not in available_roles:
            continue
            
        # Find best player for this role who hasn't been assigned yet
        best_perf = -float('inf')
        best_player = None
        
        for player_idx in range(len(team)):
            if player_idx in assigned_players:
                continue
                
            performance = performance_matrix[player_idx][role]
            if performance > best_perf and performance > -100.0:
                best_perf = performance
                best_player = player_idx
        
        # If we found a suitable player, assign them this role
        if best_player is not None:
            assigned_roles[best_player] = role
            assigned_players.add(best_player)
            available_roles.remove(role)
    
    # Handle any unassigned roles or players with "forced" role
    if len(assigned_roles) < len(team) or len(available_roles) > 0:
        # Assign remaining players to remaining roles
        unassigned_players = [i for i in range(len(team)) if i not in assigned_players]
        for player_idx in unassigned_players:
            if available_roles:
                # Find best available role for this player
                best_role = None
                best_perf = -float('inf')
                
                for role in available_roles:
                    perf = performance_matrix[player_idx][role]
                    if perf > best_perf:
                        best_perf = perf
                        best_role = role
                
                # Assign this player to the best available role
                if best_role:
                    assigned_roles[player_idx] = best_role
                    available_roles.remove(best_role)
                    assigned_players.add(player_idx)
                else:
                    # Fall back to "forced" role if no suitable role found
                    assigned_roles[player_idx] = "forced"
    
    # Update team with assigned roles
    for player_idx, role in assigned_roles.items():
        updated_team[player_idx]["assigned_role"] = role
    
    # Ensure every player has an assigned role (should not happen, but as a fallback)
    for player_idx, player in enumerate(updated_team):
        if "assigned_role" not in player:
            print(f"Player {player.get('game_name', 'Unknown')} had no assigned role after team assignment")
            player["assigned_role"] = "forced"
    
    return updated_team

def test_role_assignment():
    # Create test team with role preferences and performance data
    test_team = [
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
    
    # Test with multiple players preferring the same role
    print("=== Original Team ===")
    for player in test_team:
        print(f"{player['game_name']}: {player['role']}")
    
    # Assign roles
    assigned_team = assign_team_roles(test_team)
    
    print("\n=== Assigned Team ===")
    for player in assigned_team:
        print(f"{player['game_name']}: Preferences {player['role']} -> Assigned {player['assigned_role']}")
    
    # Count role assignments
    roles_count = {}
    for player in assigned_team:
        role = player["assigned_role"]
        roles_count[role] = roles_count.get(role, 0) + 1
    
    print("\n=== Role Assignment Counts ===")
    for role, count in roles_count.items():
        print(f"{role}: {count}")
    
    # Verify all standard roles are assigned once
    standard_roles = ["top", "jungle", "mid", "bottom", "support"]
    all_correct = True
    
    for role in standard_roles:
        if roles_count.get(role, 0) != 1:
            print(f"ERROR: Role '{role}' should be assigned exactly once, but was assigned {roles_count.get(role, 0)} times")
            all_correct = False
    
    if all_correct:
        print("\nSUCCESS: All roles are properly assigned!")
    else:
        print("\nFAILURE: Roles are not assigned correctly!")

if __name__ == "__main__":
    test_role_assignment()
    
# Add discord.py extension setup function
async def setup(bot):
    # This file is just for testing, so we don't need to add a cog
    pass