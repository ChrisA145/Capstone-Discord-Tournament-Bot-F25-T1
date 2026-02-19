# KSU Esports Tournament Test Documentation

This document provides a comprehensive overview of all tests in the KSU Esports Tournament project, including both unit tests and integration tests.

## System Tests

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| Start Discord Bot | Verify bot initialization | Run `tournament.py` file or use a powershell command `python tournament.py` | DB, Tables (player, player_game_info) are created, channels created | DB, Tables (player, player_game_info) are created, channels created | Pass | |
| Player join discord bot server | Verify welcome workflow | Player accesses the discord bot server invite link and joins the server | If player joins server for first time, they receive a message with registration form | If player joins server for first time, they receive a message with registration form | Pass | Player has option to register or ignore |

## Unit Tests - Match Making

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_load_player_data` | Test loading player data | 1. Mock loading player data<br>2. Test error handling | Data loads successfully or returns empty on error | Data loads successfully or returns empty on error | Pass | |
| `test_calculate_player_tier` | Verify tier calculation | Test tier calculation for various ranks | Tiers calculate correctly based on rank | Tiers calculate correctly based on rank | Pass | |
| `test_get_random_players_from_specific_rank` | Test player selection from specific rank | Get random players from gold rank | Returns correct number of players from gold rank if available, otherwise supplements with other ranks | Returns correct number of players, satisfying rank requirements | Pass | |
| `test_get_random_players_from_all_ranks` | Test random player selection | Get random players from all ranks | Returns players with a mix of tiers | Returns players with a mix of tiers | Pass | |
| `test_get_random_players_empty_data` | Test handling empty data | Test with empty player data | Returns empty list | Returns empty list | Pass | |
| `test_intialSortingPlayer` | Test player sorting | Sort players by tier, rank, and win rate | Players are sorted correctly | Players are sorted correctly | Pass | |
| `test_performance` | Verify performance calculation | Calculate player performance | Role-based performance values added to each player | Role-based performance values added to each player | Pass | |
| `test_relativePerformance` | Test relative performance calculation | Calculate relative performance based on roles | Correct performance values for each role | Correct performance values for each role | Pass | |
| `test_teamPerformance` | Test team performance calculation | Calculate team performance based on player roles | Returns sum of all role performances | Returns sum of all role performances | Pass | |
| `test_possible_assighn_role` | Test role assignment | Assign role based on player preferences and available roles | Returns best available role | Returns best available role | Pass | |
| `test_isPlayerRoleprefered` | Test role preference | Compare role preferences between players | Returns true if first player prefers the role | Returns true if first player prefers the role | Pass | |
| `test_assignPlayer_toTeam` | Test player team assignment | Assign players to teams based on roles | Players assigned to appropriate teams with optimal roles | Players assigned to appropriate teams with optimal roles | Pass | |
| `test_buildTeams` | Test team building | Build balanced teams from players | Two balanced teams are created | Two balanced teams are created | Pass | |
| `test_verify_swap_teams` | Test team swapping | Verify and swap team members | Teams should be modified to avoid grouping | Teams are modified to avoid grouping | Pass | |
| `test_set_test_players` | Test setting test players | Set test players for main function | Global variable should be set | Global variable is set | Pass | |

## Unit Tests - Team Swap

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_swap_players_success` | Test player swapping | Swap two players between teams in the database | Players successfully swapped between teams | Players successfully swapped between teams | Pass | |
| `test_swap_players_not_found` | Test error handling for missing players | Attempt to swap players that don't exist | Returns false indicating failure | Returns false indicating failure | Pass | |
| `test_swap_players_with_exception` | Test exception handling | Simulate a database error during swap | Returns false indicating failure | Returns false indicating failure | Pass | |
| `test_swap_team_players_command_match_not_found` | Test match not found scenario | Try to swap players with invalid match ID | Appropriate error message displayed | Appropriate error message displayed | Pass | |
| `test_swap_team_players_command_match_completed` | Test completed match scenario | Try to swap players in a completed match | Error message indicating match has results | Error message indicating match has results | Pass | |
| `test_swap_team_players_no_permission` | Test permission checking | Try to use command without admin permission | Permission denied message | Permission denied message | Pass | |
| `test_swap_team_players_with_exception` | Test exception handling in command | Simulate an exception during command execution | Error message displayed | Error message displayed | Pass | |

## Unit Tests - Database Connection

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_db_connect` | Test database connection | Create database connection | Connection created successfully | Connection created successfully | Pass | |
| `test_create_player_table` | Test table creation | Create player table | Table created successfully | Table created successfully | Pass | |
| `test_register_and_fetch_player` | Test player registration and retrieval | Register player and fetch their info | Player record exists after registration | Player record exists after registration | Pass | |
| `test_register_game` | Test game registration | Register game information for player | Game info registered successfully | Game info registered successfully | Pass | |
| `test_register_player_with_duplicate` | Test duplicate handling | Register same player twice | Updates existing record without error | Updates existing record without error | Pass | |
| `test_get_all_player` | Test fetching all players | Get all registered players | Returns list of all players | Returns list of all players | Pass | |
| `test_get_role_preference` | Test role preference | Get player's role preferences | Returns correct role preferences | Returns correct role preferences | Pass | |
| `test_get_player_tier` | Test tier retrieval | Get player's tier | Returns correct tier | Returns correct tier | Pass | |
| `test_calculate_manual_tier` | Test tier calculation | Calculate manual tier based on tier/rank | Returns correct manual tier value | Returns correct manual tier value | Pass | Tests various tier/rank combinations |
| `test_player_find_by_name` | Test player lookup by name | Find player by game name | Returns correct player ID | Returns correct player ID | Pass | Case insensitive search |
| `test_player_toxicity_points` | Test toxicity tracking | Add and retrieve toxicity points | Toxicity points updated and retrieved correctly | Toxicity points updated and retrieved correctly | Pass | |
| `test_fetch_by_id` | Test fetching player by ID | Fetch player data by ID | Returns correct player data | Returns correct player data | Pass | |
| `test_isMemberExist` | Test member existence check | Check if member exists in DB | Returns true if member exists | Returns true if member exists | Pass | |
| `test_game_update_player_tier` | Test tier update | Update player's tier | Tier updated successfully | Tier updated successfully | Pass | |
| `test_mvp_votes_basic_operations` | Test MVP voting | Record and count MVP votes | Votes recorded and counted correctly | Votes recorded and counted correctly | Pass | |
| `test_matches_get_next_match_id` | Test match ID generation | Get sequential match IDs | Returns sequential IDs | Returns sequential IDs | Pass | Tests the enhanced ID generation system |

## Unit Tests - API

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_get_summoner_info` | Test Riot API summoner info retrieval | Get summoner info by name | Returns summoner details | Returns summoner details | Pass | |
| `test_get_account_level` | Test account level retrieval | Get account level | Returns correct account level | Returns correct account level | Pass | |
| `test_get_summoner_rank` | Test rank retrieval | Get summoner rank | Returns correct rank | Returns correct rank | Pass | |
| `test_validate_player_info` | Test player info validation | Validate player information | Valid information is accepted, invalid is rejected | Valid information is accepted, invalid is rejected | Pass | |

## Unit Tests - Cached Details

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_create_cache_file` | Test cache creation | Create new cache file | Cache file created successfully | Cache file created successfully | Pass | |
| `test_hash_key_generation` | Test key hashing | Generate hash key for cache | Returns consistent hash | Returns consistent hash | Pass | |
| `test_save_and_get_cache` | Test saving and retrieving from cache | Save data to cache and retrieve it | Returns cached data correctly | Returns cached data correctly | Pass | |
| `test_cache_expiry` | Test cache expiration | Test cache after expiry period | Expired cache not returned | Expired cache not returned | Pass | |
| `test_get_nonexistent_cache` | Test missing cache handling | Request non-existent cache | Returns None | Returns None | Pass | |
| `test_cache_serialization` | Test complex data serialization | Cache complex data types | Data correctly serialized and retrieved | Data correctly serialized and retrieved | Pass | |
| `test_remove_cache` | Test cache removal | Remove cache entry | Cache entry deleted | Cache entry deleted | Pass | |
| `test_cache_with_float_expiry` | Test float expiry time | Use float for cache expiry time | Cache handles float expiry correctly | Cache handles float expiry correctly | Pass | |
| `test_file_path_generation` | Test cache file path generation | Generate cache file path | Path generated correctly | Path generated correctly | Pass | |
| `test_hash_consistency` | Test hash consistency | Generate hash multiple times for same key | Hash remains consistent | Hash remains consistent | Pass | |
| `test_path_normalization` | Test path normalization | Test with different path formats | Paths normalized correctly | Paths normalized correctly | Pass | |

## Unit Tests - Discord Events

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_database_access_on_member_join` | Test database access on member join | Mock member join event | Database checked for member existence | Database checked for member existence | Pass | |
| `test_on_member_remove` | Test member removal | Mock member leave event | Member removed from database | Member removed from database | Pass | |

## Unit Tests - Genetic Matchmaking

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_generate_initial_population` | Test initial population generation | Generate initial population | Population of specified size created | Population of specified size created | Pass | |
| `test_calculate_fitness` | Test fitness calculation | Calculate fitness for teams | Fitness calculated correctly | Fitness calculated correctly | Pass | |
| `test_select_parents` | Test parent selection | Select parents for breeding | Parents selected based on fitness | Parents selected based on fitness | Pass | |
| `test_crossover` | Test genetic crossover | Perform crossover between parents | New team combinations created | New team combinations created | Pass | |
| `test_mutate` | Test mutation | Apply mutation to teams | Teams modified according to mutation rate | Teams modified according to mutation rate | Pass | |
| `test_evolve` | Test evolution process | Run multiple generations of evolution | Teams improve over generations | Teams improve over generations | Pass | |
| `test_team_balance` | Test team balance | Verify team balance after genetic algorithm | Teams have similar skill levels | Teams have similar skill levels | Pass | |
| `test_role_distribution` | Test role distribution | Check role distribution in final teams | Players assigned to appropriate roles | Players assigned to appropriate roles | Pass | |
| `test_respect_preferences` | Test preference handling | Check if player preferences are respected | Player role preferences prioritized | Player role preferences prioritized | Pass | |
| `test_handle_invalid_input` | Test invalid input handling | Provide invalid input | Graceful error handling | Graceful error handling | Pass | |
| `test_algorithm_convergence` | Test algorithm convergence | Run algorithm until convergence | Algorithm converges to stable solution | Algorithm converges to stable solution | Pass | |
| `test_genetic_vs_random` | Compare genetic vs random | Compare genetic algorithm to random assignment | Genetic algorithm produces better results | Genetic algorithm produces better results | Pass | |
| `test_large_player_pool` | Test with large player pool | Run with large number of players | Scales effectively with large player count | Scales effectively with large player count | Pass | |
| `test_specific_scenarios` | Test specific edge cases | Test with edge case player distributions | Handles edge cases correctly | Handles edge cases correctly | Pass | |
| `test_generate_matchups` | Test matchup generation | Generate matchups for tournament | Valid matchups created | Valid matchups created | Pass | |

## Integration Tests

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_full_tournament_flow` | Test complete tournament workflow | Run complete tournament cycle | Tournament progresses through all stages correctly | Tournament progresses through all stages correctly | Pass | |

## Running Tests

To run all tests:
```bash
pytest
```

To run specific test files:
```bash
pytest unit_testing/test_match_making.py
```

To run a specific test:
```bash
pytest unit_testing/test_match_making.py::test_get_random_players_from_specific_rank
```

To run tests with coverage:
```bash
pytest --cov=.
```

## Unit Tests - Discord Commands

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_checkin_admin` | Test admin checkin command | Execute checkin command as admin | Check-in starts successfully | Check-in starts successfully | Pass | |
| `test_checkin_non_admin` | Test checkin permissions | Execute checkin command as non-admin | Permission denied message | Permission denied message | Pass | |
| `test_view_player_tier_admin` | Test tier viewing | Admin views player tier | Tier information displayed | Tier information displayed | Pass | |
| `test_view_player_tier_invalid_player` | Test tier view error handling | Admin views nonexistent player | Error message displayed | Error message displayed | Pass | |
| `test_view_player_tier_non_admin` | Test tier view permissions | Non-admin tries to view tier | Permission denied message | Permission denied message | Pass | |
| `test_toxicity_update_admin` | Test toxicity tracking | Admin adds toxicity point | Toxicity point added | Toxicity point added | Pass | |
| `test_toxicity_update_invalid_player` | Test toxicity error handling | Admin adds toxicity to nonexistent player | Error message displayed | Error message displayed | Pass | |
| `test_toxicity_update_non_admin` | Test toxicity permissions | Non-admin tries to add toxicity | Permission denied message | Permission denied message | Pass | |
| `test_get_toxicity` | Test toxicity retrieval | Check player toxicity level | Correct toxicity level shown | Correct toxicity level shown | Pass | |
| `test_get_toxicity_player_not_found` | Test toxicity retrieval error | Check nonexistent player | Error message displayed | Error message displayed | Pass | |

## Unit Tests - Import/Export

| Test | Purpose | Steps | Expected Result | Actual Result | Status | Comments |
|------|---------|-------|-----------------|---------------|--------|----------|
| `test_export_players` | Test player data export | Export player data to Google Sheets | Data exported successfully | Data exported successfully | Pass | |
| `test_import_players` | Test player data import | Import player data from Google Sheets | Data imported successfully | Data imported successfully | Pass | |
| `test_import_invalid_data` | Test import error handling | Import invalid data format | Error message displayed | Error message displayed | Pass | |
| `test_unauthorized_export` | Test export permissions | Non-admin attempts export | Permission denied message | Permission denied message | Pass | |
| `test_unauthorized_import` | Test import permissions | Non-admin attempts import | Permission denied message | Permission denied message | Pass | |

## Test Coverage Summary

Current test coverage:
- Overall: ~78%
- Controller modules: ~80% 
- Model modules: ~90%
- Common utilities: ~75%
- Discord Events: ~70%
- Commands: ~80%

Areas with improved coverage:
- Discord event handlers
- Admin commands
- Player management
- Team management
- Toxicity tracking
- Import/Export functionality
- Database model (dbc_model.py)
- Match ID generation
- MVP voting system

Areas still needing improved coverage:
- View modules
- Edge case handling in tournament workflows