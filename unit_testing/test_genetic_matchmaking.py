import pytest
import asyncio
import sys
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.genetic_match_making import GeneticMatchMaking


@pytest.fixture
def sample_players():
    """Sample players for testing"""
    return [
        {'user_id': 'player1', 'game_name': 'Player1', 'tier': 'platinum', 'rank': 'II', 'wr': 56, 'role': ['mid', 'top', 'jungle']},
        {'user_id': 'player2', 'game_name': 'Player2', 'tier': 'gold', 'rank': 'II', 'role': ['support', 'mid'], 'wr': 73},
        {'user_id': 'player3', 'game_name': 'Player3', 'tier': 'platinum', 'rank': 'IV', 'wr': 77, 'role': ['bottom', 'top', 'jungle', 'mid', 'support']},
        {'user_id': 'player4', 'game_name': 'Player4', 'tier': 'bronze', 'rank': 'III', 'wr': 78, 'role': ['jungle']},
        {'user_id': 'player5', 'game_name': 'Player5', 'tier': 'gold', 'rank': 'I', 'wr': 69, 'role': ['top', 'jungle', 'mid']},
        {'user_id': 'player6', 'game_name': 'Player6', 'tier': 'bronze', 'rank': 'I', 'wr': 86, 'role': ['top', 'jungle']},
        {'user_id': 'player7', 'game_name': 'Player7', 'tier': 'gold', 'rank': 'IV', 'wr': 47, 'role': ['bottom', 'mid', 'top', 'jungle', 'support']},
        {'user_id': 'player8', 'game_name': 'Player8', 'tier': 'platinum', 'rank': 'V', 'wr': 47, 'role': ['mid']},
        {'user_id': 'player9', 'game_name': 'Player9', 'tier': 'diamond', 'rank': 'II', 'wr': 75, 'role': ['mid', 'top', 'jungle']},
        {'user_id': 'player10', 'game_name': 'Player10', 'tier': 'master', 'rank': 'II', 'wr': 93, 'role': ['top', 'bottom', 'jungle', 'support']}
    ]


@pytest.fixture
def matchmaker():
    """Create a matchmaker instance with mocked database connections"""
    with patch('controller.genetic_match_making.Tournament_DB') as mock_db, \
         patch('controller.genetic_match_making.Game') as mock_game, \
         patch('controller.genetic_match_making.Player') as mock_player:
        
        matchmaker = GeneticMatchMaking()
        
        # Mock the database connections
        mock_db.return_value.cursor = MagicMock()
        mock_db.return_value.connection = MagicMock()
        mock_game.return_value.cursor = MagicMock()
        mock_player.return_value.cursor = MagicMock()
        
        yield matchmaker


@pytest.mark.asyncio
async def test_calculate_player_tier(matchmaker):
    """Test calculating player tier"""
    # Mock the imported function
    with patch('controller.match_making.calculate_player_tier', return_value=3.5):
        # Test with a player that doesn't have calculated_tier
        player = {'tier': 'gold', 'rank': 'II'}
        result = await matchmaker.calculate_player_tier(player)
        
        # Check the result has calculated_tier
        assert 'calculated_tier' in result
        assert result['calculated_tier'] == 3.5
        
        # Test with a player that already has calculated_tier
        player_with_tier = {'tier': 'gold', 'rank': 'II', 'calculated_tier': 4.0}
        result = await matchmaker.calculate_player_tier(player_with_tier)
        
        # Should not change the existing calculated_tier
        assert result['calculated_tier'] == 4.0


@pytest.mark.asyncio
async def test_initial_sorting_player(matchmaker, sample_players):
    """Test initial sorting of players"""
    # Test with sample players
    sorted_players = await matchmaker.initial_sorting_player(sample_players)
    
    # Verify players are sorted correctly
    assert sorted_players[0]['tier'] == 'master'  # Master should be first
    
    # Empty players list
    empty_result = await matchmaker.initial_sorting_player([])
    assert empty_result == []


@pytest.mark.asyncio
async def test_calculate_performance(matchmaker, sample_players):
    """Test calculation of player performance metrics"""
    # Patch calculate_player_tier to avoid external dependencies
    with patch.object(matchmaker, 'calculate_player_tier', new_callable=AsyncMock) as mock_calc:
        # Mock calculated_tier to pass through or assign a value
        mock_calc.side_effect = lambda p: {**p, 'calculated_tier': p.get('calculated_tier', 3.0)}
        
        # Run the function
        result = await matchmaker.calculate_performance(sample_players)
        
        # Verify all players have roleBasedPerformance
        assert all('roleBasedPerformance' in player for player in result)
        
        # Check a few players in detail
        assert result[0]['roleBasedPerformance']['mid'] > 0
        assert result[0]['roleBasedPerformance']['top'] > 0
        
        # Test with manual tier
        player_with_manual = {'tier': 'gold', 'rank': 'I', 'manual_tier': 7.5, 'role': ['top']}
        result_manual = await matchmaker.calculate_performance([player_with_manual])
        
        # Verify manual tier takes precedence
        assert result_manual[0]['roleBasedPerformance']['top'] > 0


def test_team_performance(matchmaker):
    """Test calculation of team performance"""
    # Create a test team with roleBasedPerformance
    test_team = [
        {'roleBasedPerformance': {'top': 1.2, 'mid': 1.0}},
        {'roleBasedPerformance': {'jungle': 0.9, 'top': 0.7}},
        {'roleBasedPerformance': {'bottom': 1.1}}
    ]
    
    # Calculate performance
    result = matchmaker.team_performance(test_team)
    
    # Should sum all values in roleBasedPerformance
    expected = 1.2 + 1.0 + 0.9 + 0.7 + 1.1
    assert result == expected
    
    # Test with empty team
    assert matchmaker.team_performance([]) == 0
    
    # Test with team without roleBasedPerformance
    team_no_perf = [{'tier': 'gold'}, {'tier': 'silver'}]
    assert matchmaker.team_performance(team_no_perf) == 0


def test_decode_chromosome(matchmaker, sample_players):
    """Test chromosome decoding into teams"""
    # Create a sample chromosome (indices into players list)
    chromosome = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    team_size = 5
    
    # Patch assign_team_roles to simplify test
    with patch.object(matchmaker, 'assign_team_roles', lambda team: team):
        team1, team2 = matchmaker.decode_chromosome(chromosome, sample_players, team_size)
        
        # Verify teams are split correctly from chromosome indices
        assert len(team1) == team_size
        assert len(team2) == team_size
        
        assert team1[0]['user_id'] == sample_players[0]['user_id']
        assert team2[0]['user_id'] == sample_players[5]['user_id']


def test_assign_team_roles(matchmaker):
    """Test optimal role assignment to team members"""
    # Test team with roleBasedPerformance
    test_team = [
        {'user_id': 'p1', 'roleBasedPerformance': {'top': 1.5, 'mid': 1.0, 'jungle': 0.8}},
        {'user_id': 'p2', 'roleBasedPerformance': {'support': 1.3, 'bottom': 0.7}},
        {'user_id': 'p3', 'roleBasedPerformance': {'jungle': 1.1, 'mid': 0.9}},
        {'user_id': 'p4', 'roleBasedPerformance': {'bottom': 1.2, 'support': 0.6}},
        {'user_id': 'p5', 'roleBasedPerformance': {'top': 0.9, 'mid': 1.2, 'support': 1.0}}
    ]
    
    # Assign roles
    result = matchmaker.assign_team_roles(test_team)
    
    # Verify each player has an assigned role
    assert all('assigned_role' in player for player in result)
    
    # Test with forced roles
    test_team_incomplete = [
        {'user_id': 'p1', 'roleBasedPerformance': {'top': 1.5}},
        {'user_id': 'p2', 'roleBasedPerformance': {'support': 1.3}},
        {'user_id': 'p3', 'roleBasedPerformance': {'jungle': 1.1}}
    ]
    
    result_incomplete = matchmaker.assign_team_roles(test_team_incomplete)
    # Verify all players have assigned roles even if there are not enough preferences
    assert all('assigned_role' in player for player in result_incomplete)


def test_calculate_fitness(matchmaker, sample_players):
    """Test fitness calculation for a chromosome"""
    # Create a sample chromosome
    chromosome = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    # Add calculated_tier to each player
    players_with_tier = [
        {**player, 'calculated_tier': 3.0} for player in sample_players
    ]
    
    # Patch decode_chromosome to return known teams
    team1 = [
        {'user_id': 'p1', 'tier': 'gold', 'rank': 'II', 'assigned_role': 'top', 'roleBasedPerformance': {'top': 1.2}},
        {'user_id': 'p2', 'tier': 'silver', 'rank': 'I', 'assigned_role': 'jungle', 'roleBasedPerformance': {'jungle': 1.1}},
        {'user_id': 'p3', 'tier': 'platinum', 'rank': 'III', 'assigned_role': 'mid', 'roleBasedPerformance': {'mid': 1.3}},
        {'user_id': 'p4', 'tier': 'gold', 'rank': 'IV', 'assigned_role': 'bottom', 'roleBasedPerformance': {'bottom': 1.0}},
        {'user_id': 'p5', 'tier': 'gold', 'rank': 'I', 'assigned_role': 'support', 'roleBasedPerformance': {'support': 1.1}}
    ]
    
    team2 = [
        {'user_id': 'p6', 'tier': 'gold', 'rank': 'II', 'assigned_role': 'top', 'roleBasedPerformance': {'top': 1.2}},
        {'user_id': 'p7', 'tier': 'silver', 'rank': 'I', 'assigned_role': 'jungle', 'roleBasedPerformance': {'jungle': 1.1}},
        {'user_id': 'p8', 'tier': 'platinum', 'rank': 'IV', 'assigned_role': 'mid', 'roleBasedPerformance': {'mid': 1.3}},
        {'user_id': 'p9', 'tier': 'gold', 'rank': 'III', 'assigned_role': 'bottom', 'roleBasedPerformance': {'bottom': 1.0}},
        {'user_id': 'p10', 'tier': 'gold', 'rank': 'II', 'assigned_role': 'support', 'roleBasedPerformance': {'support': 1.1}}
    ]
    
    with patch.object(matchmaker, 'decode_chromosome', return_value=(team1, team2)), \
         patch.object(matchmaker, 'team_performance', side_effect=[5.7, 5.7]), \
         patch.object(matchmaker, 'calculate_role_matchup_score', return_value=0.9):
        
        # Calculate fitness
        fitness = matchmaker.calculate_fitness(chromosome, players_with_tier)
        
        # Verify fitness is calculated
        assert fitness > 0
        
        # Perfect balance should give high fitness
        assert fitness > 90


def test_calculate_role_matchup_score(matchmaker):
    """Test calculation of role matchup score"""
    team1 = [
        {'assigned_role': 'top', 'tier': 'gold', 'rank': 'II'},
        {'assigned_role': 'jungle', 'tier': 'silver', 'rank': 'I'},
        {'assigned_role': 'mid', 'tier': 'platinum', 'rank': 'III'},
        {'assigned_role': 'bottom', 'tier': 'gold', 'rank': 'IV'},
        {'assigned_role': 'support', 'tier': 'gold', 'rank': 'I'}
    ]
    
    team2 = [
        {'assigned_role': 'top', 'tier': 'gold', 'rank': 'II'},  # Exact match
        {'assigned_role': 'jungle', 'tier': 'silver', 'rank': 'I'},  # Exact match
        {'assigned_role': 'mid', 'tier': 'platinum', 'rank': 'IV'},  # Small difference
        {'assigned_role': 'bottom', 'tier': 'gold', 'rank': 'III'},  # Small difference
        {'assigned_role': 'support', 'tier': 'gold', 'rank': 'II'}  # Small difference
    ]
    
    score = matchmaker.calculate_role_matchup_score(team1, team2)
    
    # Score should be high since teams are close in rank
    assert score > 0.8
    
    # Test with very different teams
    team3 = [
        {'assigned_role': 'top', 'tier': 'challenger', 'rank': 'I'},
        {'assigned_role': 'jungle', 'tier': 'diamond', 'rank': 'I'},
        {'assigned_role': 'mid', 'tier': 'master', 'rank': 'III'},
        {'assigned_role': 'bottom', 'tier': 'diamond', 'rank': 'II'},
        {'assigned_role': 'support', 'tier': 'platinum', 'rank': 'I'}
    ]
    
    team4 = [
        {'assigned_role': 'top', 'tier': 'iron', 'rank': 'IV'},
        {'assigned_role': 'jungle', 'tier': 'bronze', 'rank': 'III'},
        {'assigned_role': 'mid', 'tier': 'silver', 'rank': 'IV'},
        {'assigned_role': 'bottom', 'tier': 'bronze', 'rank': 'II'},
        {'assigned_role': 'support', 'tier': 'iron', 'rank': 'V'}
    ]
    
    score2 = matchmaker.calculate_role_matchup_score(team3, team4)
    
    # Score should be low since teams are very different
    assert score2 < 0.5


def test_tournament_selection(matchmaker):
    """Test tournament selection of chromosomes"""
    population = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15]
    ]
    
    fitnesses = [50, 70, 60, 90]
    
    # Mock random.sample to always return the same selection
    with patch('random.sample', return_value=[(population[3], fitnesses[3]), (population[1], fitnesses[1]), (population[0], fitnesses[0])]):
        selected = matchmaker.tournament_selection(population, fitnesses)
        
        # Should pick the chromosome with highest fitness in tournament
        assert selected == population[3]


def test_order_crossover(matchmaker):
    """Test order crossover operation"""
    parent1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    parent2 = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    
    # Mock random selections for consistent testing
    with patch('random.sample', return_value=[2, 5]):
        child = matchmaker.order_crossover(parent1, parent2)
        
        # Verify the child has all values from 0-9
        assert sorted(child) == list(range(10))
        
        # Verify the middle section from parent1 is preserved
        assert child[2:6] == parent1[2:6]


def test_swap_mutation(matchmaker):
    """Test swap mutation operation"""
    chromosome = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    # Force mutation to occur
    with patch('random.random', return_value=0.05), \
         patch('random.sample', return_value=[2, 7]):
        mutated = matchmaker.swap_mutation(chromosome)
        
        # Verify two positions were swapped
        assert mutated[2] == chromosome[7]
        assert mutated[7] == chromosome[2]
        
        # All other positions should remain the same
        for i in range(len(chromosome)):
            if i != 2 and i != 7:
                assert mutated[i] == chromosome[i]
    
    # Ensure no mutation occurs when random.random returns > mutation_rate
    with patch('random.random', return_value=0.2):
        not_mutated = matchmaker.swap_mutation(chromosome)
        assert not_mutated == chromosome


@pytest.mark.asyncio
async def test_fetch_player_data(matchmaker):
    """Test fetching player data from database"""
    # Mock database queries
    player_db_mock = matchmaker.player_db
    game_db_mock = matchmaker.game_db
    
    # Mock get_all_player to return sample data
    player_records = [
        (123, "Player1", "tag1"),
        (456, "Player2", "tag2")
    ]
    player_db_mock.get_all_player = MagicMock(return_value=player_records)
    
    # Mock the cursor to return game data
    game_data = ("gold", "II", '{"top": true, "mid": false}', 10, 5, 0.67)
    game_db_mock.cursor.fetchone = MagicMock(return_value=game_data)
    
    # Call the method
    result = await matchmaker.fetch_player_data()
    
    # Verify results
    assert len(result) == 2
    assert result[0]['user_id'] == 123
    assert result[0]['tier'] == 'gold'
    assert result[0]['rank'] == 'II'


@pytest.mark.asyncio
async def test_load_players_from_json(matchmaker):
    """Test loading players from JSON file"""
    # Mock get_random_players function
    with patch('controller.match_making.get_random_players', return_value=[{'user_id': 'test', 'tier': 'gold'}]):
        result = await matchmaker.load_players_from_json(count=5)
        
        # Verify results
        assert len(result) == 1
        assert result[0]['user_id'] == 'test'
        assert result[0]['tier'] == 'gold'


@pytest.mark.asyncio
async def test_save_matchmaking_results(matchmaker):
    """Test saving matchmaking results to database"""
    team1 = [
        {'user_id': 123, 'game_name': 'Player1', 'assigned_role': 'top'},
        {'user_id': 456, 'game_name': 'Player2', 'assigned_role': 'jungle'}
    ]
    
    team2 = [
        {'user_id': 789, 'game_name': 'Player3', 'assigned_role': 'mid'},
        {'user_id': 101, 'game_name': 'Player4', 'assigned_role': 'bottom'}
    ]
    
    # Mock Matches.get_next_match_id
    with patch('model.dbc_model.Matches') as mock_matches:
        mock_matches.return_value.get_next_match_id.return_value = 1
        
        # Call the method
        team_id = await matchmaker.save_matchmaking_results(team1, team2)
        
        # Verify results
        assert team_id == "match_1"
        
        # Verify database operations
        assert matchmaker.db.cursor.execute.call_count == 4  # 2 for team1, 2 for team2
        matchmaker.db.connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_run_matchmaking(matchmaker, sample_players):
    """Test running the entire matchmaking process"""
    # Mock all the dependent methods
    with patch.object(matchmaker, 'fetch_player_data', new_callable=AsyncMock) as mock_fetch, \
         patch.object(matchmaker, 'calculate_player_tier', new_callable=AsyncMock) as mock_calc_tier, \
         patch.object(matchmaker, 'initial_sorting_player', new_callable=AsyncMock) as mock_sort, \
         patch.object(matchmaker, 'calculate_performance', new_callable=AsyncMock) as mock_calc_perf, \
         patch.object(matchmaker, 'genetic_algorithm') as mock_ga, \
         patch.object(matchmaker, 'decode_chromosome') as mock_decode:
        
        # Configure mocks
        mock_fetch.return_value = sample_players
        mock_calc_tier.side_effect = lambda p: {**p, 'calculated_tier': 3.0}
        mock_sort.return_value = sample_players
        mock_calc_perf.return_value = sample_players
        
        test_chromosome = list(range(10))
        mock_ga.return_value = (test_chromosome, 95.0)
        
        team1 = sample_players[:5]
        team2 = sample_players[5:]
        mock_decode.return_value = (team1, team2)
        
        # Call the method
        result_team1, result_team2 = await matchmaker.run_matchmaking()
        
        # Verify correct methods were called in sequence
        mock_fetch.assert_called_once()
        mock_ga.assert_called_once()
        mock_decode.assert_called_once_with(test_chromosome, sample_players, team_size=5)
        
        # Verify results
        assert result_team1 == team1
        assert result_team2 == team2


if __name__ == "__main__":
    pytest.main()