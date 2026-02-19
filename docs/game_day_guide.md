# KSU Esports Tournament - Game Day Guide


1. **Open Check-in**
   - Use the command: `/checkin_game`
   - Specify check-in duration (in minutes)


### 2. Running Matchmaking

1. **Start Matchmaking**
   - Use the command: `/run_matchmaking`
   - Options:
     - `players_per_game`: Choose between players per game or use default of 10
     - `sit_out_method`: How to select players if not divisible by 10 (`random`, `lowest_rank`, or `volunteer`)

2. **Review Initial Teams**
   - The bot will display the generated teams
   - Review role assignments against player preferences

3. **Optimize Teams (Optional)**
   - If team balance needs improvement: `/swap_team_players`
   - Select the match ID from the dropdown
   - Select players to swap between teams
   - Confirm the swap and check the new balance score

### 3. Team Announcements

1. **Preview Teams**
   - Review the final teams: `/display_teams`
   - Select the match ID from the dropdown

2. **Announce Teams**
   - When ready: `/announce_teams`
   - Select the match ID and the announcement channel
   - The bot will create and send team announcement images to the selected channel

3. **Coordinate Match Start**
   - Direct players to their match lobbies
   - Provide any additional tournament-specific instructions

### 4. Match Results and MVP Voting

1. **Record Match Results**
   - After matches complete: `/record_match_result`
   - Select the match ID
   - Select the winning team

2. **Initiate MVP Voting**
   - MVP voting will be offered automatically after recording results
   - Alternatively: `/start_mvp_voting`
   - Select the match ID

3. **Monitor and Close Voting**
   - Players vote using the dropdown in the tournament channel
   - Voting typically runs for 5 minutes
   - Optionally end mvp voting early using `/end_mvp_voting`
   - Results are announced automatically when voting closes

### 5. Tournament Wrap-up

1. **Check Player Stats**
   - Review player performance: `/list_players`
   - View individual player history: `/player_match_history`


### Administrative Commands
- `/run_matchmaking` - Create balanced teams
- `/swap_team_players` - Manually adjust team compositions
- `/display_teams` - View current teams
- `/announce_teams` - Send team announcements to a channel
- `/record_match_result` - Record which team won
- `/start_mvp_voting` - Start MVP voting for a match
- `/list_players` - View all registered players
- `/adjust_player_tier` - Manually adjust a player's skill rating

