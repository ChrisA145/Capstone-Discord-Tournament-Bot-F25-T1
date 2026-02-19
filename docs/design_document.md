# KSU Esports Tournament Discord Bot - Design Document

## 1. System Architecture Overview

The bot follows a Model-View-Controller (MVC) architecture pattern:

- **Model**: Database schemas and data access methods (`model/`)
- **View**: Discord UI components and display logic (`view/`)
- **Controller**: Command logic and business rules (`controller/`)

### 1.1 Technology Stack

- **Language**: Python
- **Discord API**: discord.py library
- **Database**: SQLite via custom wrapper (similar to Peewee ORM)
- **Additional APIs**: Riot Games API (for player data)
- **AI Integration**: OpenAI for team formation alternatives

## 2. Database Design

### 2.1 Primary Tables

1. **player**: Stores Discord user ID and basic player info
   - `user_id` (PK): Discord user ID
   - `game_name`: In-game name
   - `game_id`: Game-specific ID
   - `tag_id`: Game-specific tag
   - `isAdmin`: Admin status flag

2. **game**: Stores player game statistics and preferences
   - `user_id` (FK): References player
   - `game_name`: Name of game
   - `tier`: Rank tier (bronze, silver, gold, etc.)
   - `rank`: Division (I, II, III, IV)
   - `role`: JSON string of role preferences
   - `wins`, `losses`: Game statistics
   - `manual_tier`: Numerical skill rating (0-10)
   - `wr`: Win rate (auto-calculated)

3. **matches**: Records match participation and results
   - `user_id` (FK): References player
   - `game_name`: Game name
   - `win`, `loss`: Match outcome
   - `teamUp`: Team assignment (team1, team2, volunteer, participation)
   - `teamId`: Unique match identifier
   - `date_played`: Timestamp

4. **mvp_votes**: Records MVP voting data
   - `vote_id` (PK): Auto-increment ID
   - `match_id`: References match
   - `voter_id` (FK): User who voted
   - `player_id` (FK): Player voted for
   - `vote_date`: Timestamp of vote

### 2.2 Database Connection Pattern

The system uses a custom SQLite wrapper class (`Tournament_DB`) that provides:
- Connection management
- Query execution
- Error handling and logging

## 3. Control Flow

### 3.1 Bot Initialization Flow

1. **Application Entry** (`tournament.py`):
   - Configures Discord intents and creates bot client
   - Initializes database connection
   - Creates required database tables
   - Registers event handlers

2. **Discord Connection** (`on_ready`):
   - Logs into Discord servers
   - Creates/caches necessary channels
   - Loads controller modules (cogs)
   - Syncs slash commands

### 3.2 Command Registration Flow

1. All controllers are implemented as Discord.py Cogs
2. Each cog is automatically loaded during initialization
3. Commands are registered using `@app_commands.command()` decorators
4. Command parameters use `@app_commands.describe()` for help text

### 3.3 Player Registration Flow

1. User invokes sign-up command
2. System collects game name and tag ID
3. Data is stored in `player` table
4. Optional API call to fetch rank data
5. Rank data stored in `game` table

### 3.4 Matchmaking Flow

1. **Command Invocation** (`/run_matchmaking`):
   - Admin invokes matchmaking command with parameters
   - System fetches all registered players from database

2. **Player Selection**:
   - Determines how many players needed per game (default: 10)
   - If players % 10 != 0, selects players to "sit out"
   - Selection methods: random, rank-based, or volunteer

3. **Team Formation** (`genetic_match_making.py`):
   - For each pool of players (10 per game):
     - Calculate player performance metrics
     - Use genetic algorithm to create balanced teams
     - Optimize for minimizing team performance difference

4. **Database Recording**:
   - Assigns unique match ID to each game
   - Records each player's team assignment in `matches` table
   - Players sitting out get "participation" status

5. **Result Presentation**:
   - Creates and sends Discord embeds for each team
   - Displays player info, roles, team balance metrics
   - Provides match ID for result recording

### 3.5 Match Results Flow

1. **Result Recording** (`/record_match_result`):
   - Admin records match outcome (winning team)
   - Updates `matches` table with win/loss status
   - Updates player statistics in `game` table
   - Presents option to start MVP voting

2. **MVP Voting**:
   - Admin initiates voting for a specific match
   - System fetches players from winning team
   - Creates voting UI for tournament participants
   - Collects and tallies votes in `mvp_votes` table
   - Displays results after voting period

## 4. Discord UI Components

### 4.1 Discord Embeds

Embeds are rich message objects that provide structured display of information:

```python
embed = discord.Embed(
    title="Title of the embed",
    description="Description text",
    color=discord.Color.blue()  # Sets the embed color
)

# Add fields
embed.add_field(name="Field title", value="Field content", inline=True)

# Add footer
embed.set_footer(text="Footer text")

# Send embed
await interaction.response.send_message(embed=embed)
```

**Key embed uses in the bot**:
- Team displays in matchmaking
- Match results presentation
- MVP voting and results displays

### 4.2 UI Components (Views)

The bot uses Discord's UI components for interactive elements:

1. **Select Menus**:
   - Used for player selection (volunteer sitting out)
   - Used for MVP voting

2. **Buttons**:
   - Used for confirming actions
   - Used for recording match results
   - Used for initiating MVP voting

3. **Custom Views**:
   - `MatchResultView`: UI for recording match outcomes
   - `VolunteerSelectionView`: UI for selecting players to sit out
   - `MVPVoteView`: UI for MVP voting

### 4.3 Component Implementation Pattern

Discord UI components follow this pattern:
1. Define a class inheriting from `discord.ui.View`
2. Add UI items (buttons, selects) in `__init__`
3. Define callback functions for user interactions
4. Handle state changes and updates in callbacks
5. Pass the view to message send/edit methods

## 5. Key Algorithms

### 5.1 Matchmaking Algorithm

The system offers two matchmaking approaches:

1. **Basic Matchmaking** (`match_making.py`):
   - Sorts players by rank and win rate
   - Assigns relative performance values based on roles and rank
   - Builds teams by assigning players to maximize balance

2. **Genetic Matchmaking** (`genetic_match_making.py`):
   - Uses genetic algorithm to find optimal team compositions
   - Creates "chromosomes" representing player assignments
   - Uses fitness function to evaluate team balance
   - Applies crossover and mutation to find better solutions
   - Returns best solution after multiple generations

### 5.2 Player Performance Calculation

Player skill and performance is calculated based on:
1. Player's rank tier (iron through challenger)
2. Player's division (I-IV)
3. Role preferences (primary roles weighted higher)
4. Win rate and historical performance
5. Optional manual tier override (0-10 scale)

This creates a relative performance value used for team balancing.

## 6. Error Handling

### 6.1 Error Handling Pattern

The codebase uses consistent error handling:

```python
try:
    # Operation logic
except Exception as ex:
    logger.error(f"Operation failed: {ex}")
    # User feedback (if applicable)
```

### 6.2 Database Error Handling

Database operations follow this pattern:
1. Begin transaction
2. Execute operations in try block
3. Catch exceptions and log errors
4. Commit on success, don't commit on failure
5. Always close database connection in finally block

## 7. Logging

The system uses Python's standard logging module:
- Log levels: DEBUG, INFO, WARNING, ERROR
- Outputs to console and log files
- Includes timestamps, module info, and log level
- Configuration defined in `config/settings.py`

## 8. Key Feature Implementation Details

### 8.1 MVP Voting System

1. **Initialization**:
   - Creates `MVP_Votes` table to track voting
   - Adds methods for recording and retrieving votes

2. **Voting Flow**:
   - Admin initiates voting after match result recorded
   - System identifies winning team members
   - Creates dropdown UI showing only winning team players
   - Users vote through dropdown, limited to one vote each
   - Votes stored with timestamp, voter ID, player ID

3. **Result Calculation**:
   - Counts votes for each player
   - Identifies player with most votes as MVP
   - Displays results in formatted embed

### 8.2 Player Sitting Out Mechanism

For tournaments with players not divisible by team size:
1. Excess players are selected to "sit out"
2. Selection can be random, lowest-ranked, or volunteer-based
3. Players sitting out still receive participation credit
4. System records these players with `teamUp="participation"`

### 8.3 Role Assignment

1. Players can specify preferred roles in order
2. System attempts to assign players to primary roles
3. Performance calculations consider role preference
4. Players get performance penalty for non-preferred roles

## 9. Configuration System

The bot uses a central configuration file (`config/settings.py`):
1. Loads environment variables from `.env` file
2. Defines constants for Discord settings
3. Configures logging parameters
4. Sets paths for database and controller files

## 10. Available Commands

### 10.1 Admin Commands
- **/run_matchmaking** - Create balanced teams based on player data
- **/swap_team_players** - Swap players between teams for better balance
- **/display_teams** - Display current teams for a specific match
- **/announce_teams** - Announce teams to a channel (default: tournament channel)
- **/record_match_result** - Record which team won a match
- **/view_player_tier** - View a player's tier/rank information
- **/adjust_player_tier** - Manually adjust a player's tier value
- **/reset_player_tier** - Reset a player's manual tier adjustment
- **/list_players** - View registered players and their information
- **/player_match_history** - View a player's match history

### 10.2 Player Commands
- **/signup** - Register for the tournament
- **/role** - Set role preferences
- **/vote_mvp** - Vote for the MVP in a match

## 11. Code Extension Guide

### 11.1 Adding a New Command

1. Identify appropriate controller file
2. Add command using decorator pattern:
   ```python
   @app_commands.command(name="command_name", description="Command description")
   @app_commands.describe(param1="Description of param1")
   async def command_name(self, interaction: discord.Interaction, param1: str):
       # Command implementation
   ```

### 11.2 Team Swapping System

The bot includes a team swapping feature that allows admins to manually swap players between teams:

1. **Command**: `/swap_team_players <match_id>`
2. **Controller**: `team_swap_controller.py`
3. **View**: `team_swap_view.py`
4. **Database Operations**:
   - Queries match data and player assignments
   - Updates `Matches` table to swap team assignments (`teamUp` values)
5. **Interface**:
   - Displays teams with player information
   - Provides dropdowns to select players from each team
   - Calculates team balance before and after swaps
   - Provides visual feedback of the swap results

### 11.3 Adding a New Database Table

1. Create a new class in `model/dbc_model.py`
2. Implement `createTable` method with SQL schema
3. Add necessary query methods
4. Initialize table creation in `tournament.py`

### 11.4 Creating a New UI Component

1. Create a class inheriting from `discord.ui.View`
2. Add buttons/selects in constructor
3. Implement callback methods for interactions
4. Use the view in command responses

## 12. Sequence Diagrams

### 12.1 Matchmaking Process

```
Admin                    Bot                        Database
  |                       |                            |
  | /run_matchmaking      |                            |
  |---------------------->|                            |
  |                       | fetch_players()            |
  |                       |--------------------------->|
  |                       |<---------------------------|
  |                       |                            |
  |                       | select_players_to_sit_out()|
  |                       |--------------------------->|
  |                       |                            |
  |                       | form_balanced_teams()      |
  |                       |----------------------------|
  |                       |                            |
  |                       | save_match_data()          |
  |                       |--------------------------->|
  |                       |<---------------------------|
  |                       |                            |
  | match results (embeds)|                            |
  |<----------------------|                            |
```

### 12.2 MVP Voting Process

```
Admin               Bot                  Database             Players
  |                  |                      |                    |
  | record_result    |                      |                    |
  |----------------->|                      |                    |
  |                  | save_result()        |                    |
  |                  |--------------------->|                    |
  |                  |<---------------------|                    |
  |                  |                      |                    |
  | start_mvp_voting |                      |                    |
  |----------------->|                      |                    |
  |                  | get_winning_team()   |                    |
  |                  |--------------------->|                    |
  |                  |<---------------------|                    |
  |                  |                      |                    |
  |                  | create_voting_ui()   |                    |
  |                  |-------------------------------------------->|
  |                  |                      |                    |
  |                  |                      |    cast_vote()     |
  |                  |<--------------------------------------------|
  |                  | record_vote()        |                    |
  |                  |--------------------->|                    |
  |                  |<---------------------|                    |
  |                  |                      |                    |
  |                  | tally_results()      |                    |
  |                  |--------------------->|                    |
  |                  |<---------------------|                    |
  | voting_results   |                      |                    |
  |<-----------------|                      |                    |
```

### 12.3 Team Swap Process

```
Admin               Bot                  Database
  |                  |                      |
  | swap_team_players|                      |
  |----------------->|                      |
  |                  | get_match_data()     |
  |                  |--------------------->|
  |                  |<---------------------|
  |                  |                      |
  |                  | create_swap_ui()     |
  |<-----------------|                      |
  |                  |                      |
  | select_players   |                      |
  |----------------->|                      |
  |                  | swap_players()       |
  |                  |--------------------->|
  |                  |<---------------------|
  |                  |                      |
  |                  | update_team_display()|
  |<-----------------|                      |
  |                  |                      |
  | confirm/cancel   |                      |
  |----------------->|                      |
  |                  | finalize_swap()      |
  |<-----------------|                      |
```

### 12.4 Team Display and Announcement Process

```
Admin               Bot                  Database             Channel
  |                  |                      |                    |
  | display_teams    |                      |                    |
  |----------------->|                      |                    |
  |                  | get_match_data()     |                    |
  |                  |--------------------->|                    |
  |                  |<---------------------|                    |
  |                  |                      |                    |
  |                  | create_team_embeds() |                    |
  |                  |----------------------|                    |
  |                  |                      |                    |
  | team display     |                      |                    |
  |<-----------------|                      |                    |
  |                  |                      |                    |
  | announce_teams   |                      |                    |
  |----------------->|                      |                    |
  |                  | get_match_data()     |                    |
  |                  |--------------------->|                    |
  |                  |<---------------------|                    |
  |                  |                      |                    |
  |                  | team announcement    |                    |
  |                  |-------------------------------------->|
  |                  |                      |                    |
  | confirmation     |                      |                    |
  |<-----------------|                      |                    |
```

## 13. File Structure Reference

```
KSU_Esports_Tournament/
├── common/
│   ├── cached_details.py      # Caches Discord channels
│   ├── common_scripts.py      # Shared utility functions
│   ├── database_connection.py # DB connection singleton
│   └── riot_api.py            # Riot Games API interface
├── config/
│   └── settings.py            # Configuration constants
├── controller/
│   ├── admin_controller.py    # Admin commands
│   ├── checkin_controller.py  # Player check-in 
│   ├── events.py              # Event handlers
│   ├── genetic_match_making.py # Genetic algorithm
│   ├── match_making.py        # Basic matchmaking
│   ├── match_results_controller.py # Match results
│   ├── matchmaking_controller.py # Matchmaking commands
│   ├── mvp_voting_controller.py # MVP voting system
│   ├── player_signup.py       # Player registration
│   ├── team_swap_controller.py # Team swapping
│   └── team_display_controller.py # Team display and announcement
├── model/
│   ├── button_state.py        # Button state tracking
│   ├── checkin_model.py       # Check-in data model
│   └── dbc_model.py           # Core database models
├── view/
│   ├── common_view.py         # Shared UI components
│   ├── signUp_view.py         # Sign-up UI
│   ├── match_results_view.py  # Match results UI
│   ├── mvp_vote_view.py       # MVP voting UI
│   └── team_swap_view.py      # Team swapping UI
└── tournament.py              # Main application entry
```