from collections import defaultdict
import copy
import json
import random

""" Load player data from combined_player_data.json """
def load_player_data():
    try:
        with open('combined_player_data.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading player data: {e}")
        return {}

""" Calculate a player's tier based on their rank
    This assigns a tier value (1-5) based on the player's actual rank and applies
    variations to simulate skill differences within the same rank
"""
def calculate_player_tier(rank):
    # Base tier values for each rank
    tier_values = {
        "bronze": 1,
        "silver": 2,
        "gold": 3,
        "platinum": 4,
        "diamond": 5,
        "master": 6
    }
    
    base_tier = tier_values.get(rank.lower(), 1)
    
    # Add some randomness to represent skill variation within a rank
    # Higher ranks have less variation as they tend to be more consistent
    variation_factors = {
        "bronze": 0.4,
        "silver": 0.3,
        "gold": 0.25,
        "platinum": 0.2,
        "diamond": 0.15,
        "master": 0.1
    }
    
    variation = variation_factors.get(rank.lower(), 0.3)
    
    # Random adjustment: can be higher or lower than their rank suggests
    # For example, some gold players might play at a platinum level, others at a silver level
    adjustment = random.uniform(-variation, variation)
    
    # Calculate final tier
    final_tier = base_tier + adjustment
    
    return final_tier

""" Get random players from the player data """
def get_random_players(count=10, specific_rank=None):
    player_data = load_player_data()
    
    if not player_data:
        return []
    
    if specific_rank and specific_rank.lower() in player_data:
        # Get players from a specific rank
        rank_pool = player_data[specific_rank.lower()]
        if len(rank_pool) < count:
            # If not enough players in the specific rank, supplement with players from other ranks
            other_players = []
            for rank in player_data:
                if rank != specific_rank.lower():
                    other_players.extend(player_data[rank])
            
            selected_players = random.sample(rank_pool, min(count, len(rank_pool)))
            if len(selected_players) < count:
                additional_needed = count - len(selected_players)
                selected_players.extend(random.sample(other_players, min(additional_needed, len(other_players))))
        else:
            selected_players = random.sample(rank_pool, count)
    else:
        # Get players from all ranks
        all_players = []
        for rank in player_data:
            all_players.extend([(player, rank) for player in player_data[rank]])
        
        if len(all_players) < count:
            selected_pairs = random.choices(all_players, k=count)
        else:
            selected_pairs = random.sample(all_players, count)
        
        selected_players = []
        for player, rank in selected_pairs:
            player_copy = player.copy()
            player_copy['rank_tier'] = rank
            selected_players.append(player_copy)
    
    # Convert to the format expected by the algorithm
    formatted_players = []
    roles = ['top', 'jungle', 'mid', 'bottom', 'support']
    
    for i, player in enumerate(selected_players):
        # For players from combined_player_data.json, we need to generate some attributes
        actual_rank = player.get('rank_tier', random.choice(['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master']))
        
        player_obj = {
            'user_id': f"player{i+1}",
            'game_name': player.get('name', f"Player{i+1}"),
            'tier': actual_rank,
            'calculated_tier': calculate_player_tier(actual_rank),
            'rank': random.choice(['I', 'II', 'III', 'IV']),
            'wr': random.randint(45, 95),
            'role': random.sample(roles, random.randint(1, 5))
        }
        formatted_players.append(player_obj)
    
    return formatted_players

""" Intial step sort player based on tier, rank and win ratio based on
    step1: sort based on player tier
    step2: if players have same tier sort based on rank
    step3: if players have same tier & rank then sort based on WR
"""
async def intialSortingPlayer(players):
    #define custom order of tier & rank
    tier_order = {"challenger": 1, "grandmaster": 2, "master": 3, "diamond": 4, "emerald": 5, "platinum": 6, "gold": 7, "silver": 8, "bronze": 9, "iron": 10, "default": 11}
    rank_order = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}

    sortedPlayers = sorted(players, key=lambda pl: (tier_order[pl['tier']], rank_order[pl['rank']], -pl['wr']))
    
    return sortedPlayers

""" for sorted player calculate their relative perfomance based on their role preference order
    Assumption: player effective output according to theire role prefernce is 5% reduce
                set SkillFactor_set for each tier based on different considerations, and each skill 
                    has 5% skill advance/difference than the next tier

    A standard matimatical formula for player skill factor based on the above assumptions and conditions
        relative_performance = player_skillFactor*0.75 + (1- pref_penality/100)*0.25

    for player doesnt have role prefernece then the forced asighned role set as playerPerfomanceOfRole['forced']
"""
async def performance(players):
    players_output = []
    SkillFactor_set = {"default": 0.0, "iron": 1.0, "bronze": 1.05, "silver": 1.10, "gold": 1.15, "platinum": 1.20, "emerald": 1.25, "diamond": 1.30, "master": 1.35, "grandmaster": 1.40, "challenger": 1.45}

    for player in players:
        playerPerfomanceOfRole = {}
        player_role = player["role"]
        
        # Priority order for skill factor calculation:
        # 1. Use manual_tier if available (from database)
        # 2. Use calculated_tier if available (calculated on the fly)
        # 3. Fall back to tier-based skill factor from SkillFactor_set
        
        if "manual_tier" in player and player["manual_tier"] is not None:
            # Scale manual_tier (0-10) to match SkillFactor_set range (1.0-1.45)
            # This gives a smooth progression where each point in manual_tier
            # roughly equals a 4.5% increase in skill factor
            player_skillFactor = 1.0 + (player["manual_tier"] / 10.0) * 0.45
        elif "calculated_tier" in player:
            # Scale the calculated tier to match our SkillFactor_set range
            # Scale from 1-6 range to match our SkillFactor_set values (roughly 1.0-1.45)
            player_skillFactor = 1.0 + (player["calculated_tier"] - 1) * 0.09
        else:
            # Fall back to tier-based skill factor
            player_skillFactor = SkillFactor_set.get(player["tier"], SkillFactor_set["default"])

        # To calculate the relative performance of each player based on their tier and role_preference
        totalPlayerRolesProcessd = 0
        for i, role in enumerate(player_role):
            pref_penality = i*5

            relative_performance = player_skillFactor*0.75 + (1- pref_penality/100)*0.25
            playerPerfomanceOfRole[role] = relative_performance
            totalPlayerRolesProcessd += 1

        if(totalPlayerRolesProcessd < 5):
            playerPerfomanceOfRole['forced'] = player_skillFactor*0.75

        player["roleBasedPerformance"] = playerPerfomanceOfRole

        players_output.append(player)
    return players_output
async def relativePerformance(tier, role_preference, calculated_tier=None):
    playerPerfomanceOfRole = {}
    SkillFactor_set = {"default": 0.0, "iron": 1.0, "bronze": 1.05, "silver": 1.10, "gold": 1.15, "platinum": 1.20, "emerald": 1.25, "diamond": 1.30, "master": 1.35, "grandmaster": 1.40, "challenger": 1.45}

    # Get player skill factor based on their tier or calculated_tier
    if calculated_tier is not None:
        # Scale the calculated tier to match our SkillFactor_set range
        player_skillFactor = 1.0 + (calculated_tier - 1) * 0.09
    else:
        player_skillFactor = SkillFactor_set.get(tier)

    # To calculate the relative performance of each player based on their tier and role_preference
    totalRolePlayerSelected = 0
    for i, role in enumerate(role_preference):
        pref_penality = i*5

        relative_performance = player_skillFactor*0.75 + (1- pref_penality/100)*0.25
        playerPerfomanceOfRole[role] = relative_performance
        totalRolePlayerSelected+=1

    if(totalRolePlayerSelected <= 5):
        playerPerfomanceOfRole['forced'] = player_skillFactor*0.75

    return playerPerfomanceOfRole

def teamPerformance(team):
    totalRelativePerformance = 0
    for player in team:
        totalRelativePerformance += sum(player["roleBasedPerformance"].values())
    return totalRelativePerformance

def possible_assighn_role(player, teamRoleSet):
    for role, performance in player["roleBasedPerformance"].items():
        if role not in teamRoleSet:
            return role, performance
    # If forced role is available and not in team role set
    if "forced" in player["roleBasedPerformance"] and "forced" not in teamRoleSet:
        return "forced", player["roleBasedPerformance"]["forced"]
    return None, None

def isPlayerRoleprefered(player, nextPlayer, role):
    return player["roleBasedPerformance"].get(role, 0) > nextPlayer["roleBasedPerformance"].get(role, 0)

def assignPlayer_toTeam(player, team1, team2, team1_roles, team2_roles):
    role, performance = possible_assighn_role(player, team1_roles)
    if role and performance:
        team1.append(player)
        team1_roles.add(role)
        return "T1"
    
    role, performance = possible_assighn_role(player, team2_roles)
    if role and performance:
        team2.append(player)
        team2_roles.add(role)
        return "T2"
    
    return None

def buildTeams(players):
    team1, team2 = [], []
    team1_roles, team2_roles = set(), set()
    t1_performance = 0
    t2_performance = 0
    for player in players:
        player_index = players.index(player)
        next_player = players[player_index + 1] if player_index + 1 < len(players) else None

        role_assigned_to = {}
        if len(team1) != 0 and len(team2) <= len(team1):
            if t2_performance <= t1_performance:
                role, performance = possible_assighn_role(player, team2_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    # next_player = next((p for p in players if p != player), None)
                    if next_player:
                        next_player_role, next_player_performance = possible_assighn_role(next_player, team2_roles)
                        if next_player_role and performance >= next_player_performance:
                            team2.append(role_assigned_to)
                            team2_roles.add(role)
                            t2_performance += performance
                            continue
                        else:
                            team1.append(role_assigned_to)
                            team1_roles.add(role)
                            t1_performance += performance
                    else:
                        team2.append(role_assigned_to)
                        team2_roles.add(role)
            else:
                role, performance = possible_assighn_role(player, team1_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    team1.append(role_assigned_to)
                    team1_roles.add(role)
                    t1_performance += performance
        else:
            if t1_performance <= t2_performance:
                role, performance = possible_assighn_role(player, team1_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    # next_player = next((p for p in players if p != player), None)
                    if next_player:
                        next_player_role, next_player_performance = possible_assighn_role(next_player, team1_roles)
                        if next_player_role and performance >= next_player_performance:
                            team1.append(role_assigned_to)
                            team1_roles.add(role)
                            t1_performance += performance
                            continue
                        else:
                            team2.append(role_assigned_to)
                            team2_roles.add(role)
                            t2_performance += performance
                    else:
                        team1.append(role_assigned_to)
                        team1_roles.add(role)
            else:
                role, performance = possible_assighn_role(player, team2_roles)
                role_assigned_to["team_role"] = role
                role_assigned_to["assigned_to"] = player
                if role:
                    team2.append(role_assigned_to)
                    team2_roles.add(role)
                    t2_performance += performance
                    
    return team1, team2


"""this is to makes sure same player not teamup for tournamantes
    method: verify_swap_teams
        grouping each team based on their respective game history based on (gameid/customid)

"""
def verify_swap_teams(t1, t2):
    group_t1 = defaultdict(list)
    group_t2 = defaultdict(list)

    for player in t1:
        for player_name, gameid in player.items():
            group_t1[gameid].append(player_name)

    for player in t2:
        for player_name, gameid in player.items():
            group_t2[gameid].append(player_name)

    for gameid in group_t1:
        if len(group_t1[gameid]) > 2:
            if gameid not in group_t2:
                players_t1 = group_t1[gameid]
                players_t2 = group_t2.get(gameid, [])
               
                for i in range(len(players_t1)):
                    if i < len(players_t2):
                        t1 = [player if player != players_t1[i] else {players_t2[i]: gameid} for player in t1]
                        t2 = [player if player != players_t2[i] else {players_t1[i]: gameid} for player in t2]

    for gameid in group_t2:
        if len(group_t2[gameid]) > 2:
            if gameid not in group_t1:
                players_t2 = group_t2[gameid]
                players_t1 = group_t1.get(gameid, [])
                
                for i in range(len(players_t2)):
                    if i < len(players_t1):
                        t1 = [player if player != players_t1[i] else {players_t2[i]: gameid} for player in t1]
                        t2 = [player if player != players_t2[i] else {players_t1[i]: gameid} for player in t2]

    return t1, t2



# Global variable for test data
_test_players = None

# Now we use the real player data from combined_player_data.json instead of the hardcoded test data
async def main():
    global _test_players
    # Use test_players if it was set by another module, otherwise get random players
    real_players = _test_players or get_random_players(count=10)
    
    if not real_players:
        print("Could not load player data, using test data instead")
        real_players = [
            {'user_id': 'player1', 'tier': 'platinum', 'rank': 'II', 'wr': 56, 'role': ['mid','top','Jungle']},
            {'user_id': 'player2', 'tier': 'gold', 'rank': 'II', 'role': ['support','mid'], 'wr': 73},
            {'user_id': 'player3', 'tier': 'platinum', 'rank': 'IV', 'wr': 77, 'role': ['bottom','top','Jungle','mid','support']},
            {'user_id': 'player4', 'tier': 'bronze', 'rank': 'III', 'wr': 78, 'role': ['Jungle']},
            {'user_id': 'player5', 'tier': 'gold', 'rank': 'I', 'wr': 69, 'role': ['top','Jungle','mid']},
            {'user_id': 'player6', 'tier': 'bronze', 'rank': 'I', 'wr': 86, 'role': ['top','Jungle']},
            {'user_id': 'player7', 'tier': 'gold', 'rank': 'IV', 'wr': 47, 'role': ['bottom','mid','top','Jungle','support']},
            {'user_id': 'player8', 'tier': 'platinum', 'rank': 'V', 'wr': 47, 'role': ['mid']},
            {'user_id': 'player9', 'tier': 'diamond', 'rank': 'II', 'wr': 75, 'role': ['mid','top','Jungle']},
            {'user_id': 'player10', 'tier': 'master', 'rank': 'II', 'wr': 93, 'role': ['top','Bottom','Jungle','support']}
        ]
    
    print("\n=== Using Real Player Data with Tier Assignment ===")
    # Display the players and their calculated tiers
    print("\nPlayers:")
    for player in real_players:
        print(f"{player['game_name']}: {player['tier']} (Tier Rating: {player['calculated_tier']:.2f})")
    
    # Run the matchmaking algorithm
    sorted_player = await intialSortingPlayer(players=real_players)
    print("\nSorted Players:")
    for player in sorted_player:
        print(f"{player['game_name']}: {player['tier']} {player['rank']}, Tier: {player.get('calculated_tier', 'N/A')}")
    
    # Process players for performance calculation
    player_performance = await performance(sorted_player)
    
    # Build teams
    team1, team2 = buildTeams(player_performance)
    
    # Display team assignments
    print("\n=== Team Assignments ===")
    print("\nTeam 1:")
    for player_assignment in team1:
        if isinstance(player_assignment, dict) and "assigned_to" in player_assignment:
            player = player_assignment["assigned_to"]
            role = player_assignment.get("team_role", "Unknown")
            print(f"{player['game_name']} ({player['tier']}): Role = {role}")
    
    print("\nTeam 2:")
    for player_assignment in team2:
        if isinstance(player_assignment, dict) and "assigned_to" in player_assignment:
            player = player_assignment["assigned_to"]
            role = player_assignment.get("team_role", "Unknown")
            print(f"{player['game_name']} ({player['tier']}): Role = {role}")
            
    # Reset test_players for next run
    _test_players = None
    
    return team1, team2

# Function to set test players from another module
def set_test_players(players):
    global _test_players
    _test_players = players


import asyncio

if __name__ == "__main__":
    asyncio.run(main())

async def setup(bot):
    pass