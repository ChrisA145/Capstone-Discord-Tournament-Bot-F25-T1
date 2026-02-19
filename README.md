# 🏆 KSU Esports Tournament Bot

A comprehensive and feature-rich Discord bot designed to manage League of Legends tournaments at Kennesaw State University (KSU). This bot integrates with the Riot Games API, Discord, Google Sheets, and SQLite to automate player management, matchmaking, stat tracking, MVP voting, and more.

---

##  Features

- **Environment Configuration** via `.env` for secure and customizable settings
- **Player Statistics Management** using SQLite and synchronized Google Sheets
- **Riot Account Integration** with real-time summoner rank fetching
- **Advanced Genetic Matchmaking System** considering rank, tier, role preferences, and team balance
- **Sequential Match ID System** (match_1, match_2, etc.) for tracking multiple matchmaking runs
- **Team Display and Announcement** with role matchups, performance metrics, and image generation
- **Export/Import Players** to/from Google Sheets with timestamp or custom sheet names
- **MVP Voting System** allowing players to vote for most valuable players
- **Role Assignment** with optimization for player preferences and team balance
- **Admin Commands** for tournament management and player oversight

---

##  Project Structure
```
ksu_Esports_Tournament/
├── common/                # Shared utilities and API functions
│   ├── cached_details.py  # Caching logic
│   ├── common_scripts.py  # Utility functions
│   ├── database_connection.py # DB connection handling
│   ├── riot_api.py        # Riot Games API integration
│   └── images/            # Image assets for team displays
├── config/                # Configuration management
│   └── settings.py        # Global settings and environment vars
├── controller/            # Discord command logic
│   ├── admin_controller.py # Admin commands
│   ├── match_making.py    # Standard matchmaking logic
│   ├── genetic_match_making.py # Advanced genetic matchmaking
│   ├── team_display_controller.py # Team display/announcement
│   ├── player_signup.py   # Player registration
│   └── [other controller files] # Various command modules
├── model/                 # Database models
│   ├── dbc_model.py       # Main database models
│   ├── button_state.py    # UI button state handling
│   └── [other model files] # Additional models
├── view/                  # UI components
│   ├── signUp_view.py     # Signup UI
│   ├── team_announcement_image.py # Team image generation
│   └── [other view files] # Various UI components
├── tournament.py          # Main bot entry point
├── web_server.py          # Simple web viewer for database
├── requirements.txt       # Python dependencies
├── google_export.md       # Google Sheets setup guide
└── README.md              # Project documentation
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/team2-swe/ksu_Esports_Tournament-.git
cd ksu_Esports_Tournament-
```

### 2. Environment Configuration
- Copy the provided `.env.template` file to a new file named `.env`:
```bash
Mac
cp .env.template .env
Windows
copy .env.template .env
```
- Then edit the `.env` file to fill in your specific values.
- The template includes all required fields with example values:

```
# Discord Configuration
DISCORD_APITOKEN=your_discord_bot_token_here
DISCORD_GUILD=your_discord_server_id_here

# Database Configuration
DATABASE_NAME=tournament.db

# Channel IDs
TOURNAMENT_CH=tournament_general
FEEDBACK_CH=feedback_channel
# CHANNEL_CONFIG must be a valid JSON string with this structure:
# Format: {"Category": {"channel_name": {"role_key": "RoleName"}, ...}}
# Use actual role names that exist in your Discord server (like "Admin" or "Moderator")
# You can use "@everyone" for the default role that everyone can see
CHANNEL_CONFIG={"Tournament": {"announcements": {"admin": "Admin", "everyone": "@everyone"}, "registration": {"everyone": "@everyone"}, "team-info": {"everyone": "@everyone"}, "results": {"everyone": "@everyone"}, "admin": {"admin": "Admin"}}}
CHANNEL_PLAYER=t_announcement
PRIVATE_CH=admin_channel

# Webhook Configuration
WEBHOOK_URL=your_webhook_url_here

# Riot Games API
API_KEY=your_riot_api_key_here
API_URL=https://na1.api.riotgames.com/lol
RIOT_API_KEY=your_riot_api_key_here  # Can be the same as API_KEY

# API Task Control (Optional)
STOP_API_TASK=false
START_API_TASK=true

# OpenAI Configuration (Optional - for advanced team matchmaking)
OPEN_AI_KEY=your_openai_api_key_here
prompt="Your OpenAI prompt for team matchmaking here"

# Google Sheets Integration (Optional)
GOOGLE_SHEET_ID=your_google_sheet_id_here
CELL_RANGE=Sheet1
LOL_SERVICE_PATH=./service_account.json
```

> **Important:** The DISCORD_APITOKEN is sensitive information. Never commit your actual .env file to the repository.

### 3. Generate Discord Bot Token
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application > Bot tab > Reset Token > Copy token
- Enable "Server Members Intent" under Privileged Gateway Intents
- Paste the token into `.env` as DISCORD_APITOKEN

### 4. Obtain Server (Guild) ID
- Enable Developer Mode in Discord settings
- Right-click your server > Copy ID > Add to `.env` as DISCORD_GUILD

### 5. Riot Games API Key
- Visit [Riot Developer Portal](https://developer.riotgames.com)
- Register for a personal key 
- Add the key to `.env` as API_KEY

### 6. Google Sheets API Setup (Optional)
- Follow the instructions in `google_export.md` to set up Google Sheets integration
- This enables the `/export_players` and `/import_players` commands

### 7. Install Python Dependencies
```bash

# (Optional but strongly recommended) Create and activate a virtual environment

# Create a virtual environment named "venv"
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# Install the project dependencies
pip install -r requirements.txt

```
Ensure you are using Python 3.8 or later.

### 8. Run the Bot
```bash
python tournament.py
```

If successful, the terminal will display: `Logged into server as [BotName]`

---

##  Command Overview

| Command                                                  | Description |
|----------------------------------------------------------|-------------|
| `/display_teams [match_id]`                              | Shows teams for a specific match with role assignments |
| `/announce_teams [channel] [format]`                     | Announces teams to a channel as text or image |
| `/run_matchmaking [players_per_game] [selection_method]` | Generates balanced teams using genetic algorithm |
| `/export_players [custom_name]`                          | Exports player data to Google Sheets |
| `/import_players [sheet_name]`                           | Imports player data from Google Sheets |
| `/simulate_volunteers [count]`                           | Simulates volunteers for sitting out |
| `/record_match_result [match_id] [winning_team]`         | Record match results |
| `/player_match_history [user]`                           | Shows player details |
| `/pref [role1] [role2] [role3] [role4] [role5]`          | Set role preferences |
| `/role`                                                  | Updates role preferences |
| `/stats [user]`                                          | View detailed player stats and rank |
| `/help`                                                  | Display help information |

---
## Background Tasks
A periodic job runs automatically in the background every 2 hours
**Automatic Tier Update**
parameter is configured in .env
Based on configured vlaue of MIN_GAME_PLAYED=10, MIN_GAME_WINRATE=0.62, MAX_GAME_LOST=15
   - Tier promoted 
        condition: player_game_played >= MIN_GAME_PLAYED and player_winRate >= MIN_GAME_WINRATE
   - Demote player tier
         condition: player_game_played >= MAX_GAME_LOST

---
## Matchmaking System

### Check-in and Game Formation Process

The tournament follows this workflow:

1. **Player Check-in**
   - Admin initiates check-in with `/checkin_game [timeout]` command
   - A check-in button appears in the tournament channel
   - Players click the button to check in within the time limit (default: 15 minutes)
   - Players who aren't registered will be prompted to register and set preferences
   - Check-in status is tracked until timeout or matchmaking begins

2. **Managing Check-ins**
   - Starting a new check-in will reset the previous check-in pool
   - Players can't remove themselves once checked in (they must notify an admin)
   - There is no direct command to remove a specific player from the check-in pool
   - **Workaround for player removal**:
     - If a player needs to leave after checking in, restart the check-in process
     - Use `/checkin_game` command again with a shorter timeout
     - Have remaining players check in again
   - The `/simulate_volunteers [count]` command can randomly select players to sit out when too many players are checked in

3. **Game Generation**
   - The matchmaking system automatically adapts to the number of players checked in:
     - If exactly 10 players are checked in, a single standard 5v5 game will be generated
     - With more than 10 players, multiple games can be created
     - For example, with 20 players, two separate 5v5 games will be formed
   - Players can volunteer to sit out if the number doesn't divide evenly
   - The system ensures each game is balanced independently
   - Each game receives a unique sequential match ID (match_1, match_2, etc.)
   - Admins can view and manage all active games through the bot interface

The bot uses two matchmaking approaches:

### Standard Matchmaking Logic
- Basic team formation based on player tiers and roles
- Simple balancing of teams based on calculated player performance

### Genetic Algorithm Matchmaking
- Advanced matchmaking using genetic algorithms for optimal team balance
- Considers:
  - **Player Tier**: Ranked tier from Iron to Challenger
  - **Role Preferences**: Player's preferred positions
  - **Manual Tier**: Optional custom tier assignment
  - **Win Rate**: Player's win percentage
- Uses fitness functions to evaluate team balance
- Performs up to 300 generations to find optimal team compositions
- Teams are stored with sequential match IDs (match_1, match_2, etc.)

#### Genetic Matchmaking Workflow

The genetic algorithm matchmaking flow consists of these key steps:

1. **Player Data Preparation**
   - `fetch_player_data()`: Loads player data from database (or test data if unavailable)
   - `calculate_player_tier()`: Converts LoL ranks into numerical tier values
   - `initial_sorting_player()`: Sorts players by tier, rank, and win ratio

2. **Performance Calculation**
   - `calculate_performance()`: Calculates performance metrics for each player
   - Factors in player's tier, manual tier, win rate, and role preferences
   - Creates a `roleBasedPerformance` object for each player containing performance values for each role
   - Applies role preference penalties (each position down from preferred role gets a 5% penalty)

3. **Genetic Algorithm Core**
   - `genetic_algorithm()`: Runs the main evolutionary process
   - Uses adaptive parameters that increase for small player pools
   - Maintains a population of potential team arrangements (chromosomes)
   - Runs for up to 300 generations or stops early if no improvement for 50 generations

4. **Chromosome Representation**
   - Each chromosome is a permutation of player indices
   - First half represents Team 1, second half represents Team 2
   - `decode_chromosome()`: Converts chromosome into two team compositions

5. **Fitness Evaluation**
   - `calculate_fitness()`: Scores each potential team arrangement
   - Balances two objectives:
     - Overall team balance (70% weight): How even are the teams' total skill levels?
     - Role matchup balance (30% weight): How close in skill are players in the same role?

6. **Genetic Operators**
   - `tournament_selection()`: Selects parent chromosomes based on fitness
   - `order_crossover()`: Creates child solutions by combining parts of two parent chromosomes
   - `swap_mutation()`: Introduces random changes to maintain genetic diversity

7. **Role Assignment**
   - `assign_team_roles()`: Assigns optimal roles to each player in a team
   - Prioritizes roles with largest skill differences between players
   - Uses a greedy algorithm to maximize overall team effectiveness
   - Ensures each standard role (top, jungle, mid, bottom, support) is filled exactly once

8. **Results & Storage**
   - `save_matchmaking_results()`: Saves the final teams to the database with a unique match ID
   - Teams are stored with player IDs, team assignments, and a sequential match identifier

#### Performance Metrics & Balancing

The system calculates player performance using:

1. **Base Skill Factor**: Derived from the player's rank (Iron to Challenger)
2. **Role-Specific Performance**: Modified by role preference order
3. **Manual Tier Adjustment**: Admin-assigned tier values can override calculated tiers
4. **Win Rate Influence**: Player's win percentage factors into performance

The fitness function aims to:
- Create teams with similar total performance values
- Match players of similar skill levels in the same role on opposing teams
- Respect player role preferences as much as possible

This advanced genetic algorithm approach consistently produces more balanced teams than random or naive sorting methods, especially for complex situations with varied ranks and specific role preferences.

---

## Team Display & Announcement

The bot offers multiple ways to display teams:

### Text Display
- Shows team members with their ranks, roles, and assigned positions
- Provides performance metrics and role matchup information
- Available via `/display_teams` command

### Image Generation
- Creates visually appealing team matchup images
- Displays player ranks, names, and role assignments
- Shows head-to-head role matchups
- Available via `/announce_teams` command with format option

### Match Selection
- Dropdown menu to select which match to display/announce
- Supports multiple match IDs from different matchmaking runs

---

##  Google Sheets Integration

The bot can sync player data with Google Sheets:

### Export Features
- Export all player data to Google Sheets
- Choose custom sheet names or use timestamp-based naming
- Access via `/export_players [custom_name]` command

### Import Features
- Import player data from Google Sheets
- Update player information in bulk
- Access via `/import_players [sheet_name]` command

See `google_export.md` for detailed setup instructions.

---

##  Database Structure

The bot uses SQLite with the following main tables:

- **player**: Core player information
- **game**: Player game statistics
- **Matches**: Match information with sequential IDs
- **MVP_Votes**: Player MVP voting records
- **playerGameDetail**: Detailed player game information
- **Counters**: Sequential counters for match IDs

---


### Installation Instructions
1. Follow the Setup Instructions section above to set up the bot
2. Invite the bot to your server using the OAuth2 URL from Discord Developer Portal
3. Ensure the bot has proper permissions (manage roles, send messages, embed links, etc.)
4. Set up the required channels in your `.env` file
5. Start the bot with `python tournament.py`

### Admin-Only Commands
| Command | Description | Access |
|---------|-------------|--------|
| `/run_matchmaking [players_per_game] [selection_method]` | Start the matchmaking process | Admin only |
| `/announce_teams [channel] [format]` | Announce created teams | Admin only |
| `/display_teams [match_id]` | Display teams for a specific match | Admin only |
| `/export_players [custom_name]` | Export player data to Google Sheets | Admin only |
| `/import_players [sheet_name]` | Import player data from Google Sheets | Admin only |
| `/swap_players [match_id] [player1] [player2]` | Swap two players between teams | Admin only |
| `/record_match_result [match_id] [winning_team]` | Record match results | Admin only |
| `/set_toxicity [player] [points]` | Set toxicity points for a player | Admin only |
| `/set_tier [player] [tier]` | Manually set a player's tier | Admin only |
| `/checkin_start [time]` | Start the check-in process | Admin only |
| `/simulate_volunteers [count]` | Simulate volunteers for sitting out | Admin only |
| `/giveaway [prize] [entries]` | Run a giveaway raffle | Admin only |

### Configuration Options
All configuration is done through the `.env` file. The main options are:

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_APITOKEN` | Your Discord bot token | Yes |
| `DISCORD_GUILD` | Your Discord server ID | Yes |
| `DATABASE_NAME` | Name of the SQLite database file | Yes |
| `TOURNAMENT_CH` | Channel ID for tournament announcements | Yes |
| `FEEDBACK_CH` | Channel ID for feedback messages | Yes |
| `CHANNEL_CONFIG` | Comma-separated channel names to create | Yes |
| `CHANNEL_PLAYER` | Channel ID for player-related messages | Yes |
| `PRIVATE_CH` | Channel ID for admin-only messages | Yes |
| `API_KEY` | Riot Games API key | Yes |
| `API_URL` | Riot Games API URL | Yes |
| `GOOGLE_SHEET_ID` | Google Sheet ID for import/export | Optional |
| `CELL_RANGE` | Cell range in Google Sheet | Optional |
| `LOL_SERVICE_PATH` | Path to Google service account JSON | Optional |

## 🐛 Known Issues and Limitations

### Known Bugs
- Database locking can occur when multiple operations happen simultaneously
  - **Workaround**: Restart the bot to clear any hanging connections
- Team display may show duplicate players if multiple runs of matchmaking are done with the same match_id
  - **Fix**: Now using sequential match IDs to avoid conflicts
- Google Sheets export occasionally times out with large player pools
  - **Workaround**: Export in smaller batches or use a more stable internet connection
- "NOT NULL constraint failed: game.game_name" error
  - **Fix**: Game object instantiation corrected to properly handle game_name in API controller
- Missing setup function in test controllers
  - **Fix**: All controller files now include proper setup functions
- Typos in log messages ("tage_id", "puui", and "game detail")
  - **Fix**: Corrected typos in API controller and common_view.py for clearer log messages

### Undeveloped Features
- Automatic team balancing based on past performance
- Player ranking system based on performance

### Compatibility and Requirements
- Requires Python 3.8 or later
- Discord.py library v2.0.0 or higher
- SQLite database (included with Python)
- Stable internet connection for Riot API and Discord connectivity
- For Google Sheets functionality: Google Cloud account and proper API setup

## 🔧 Troubleshooting Tips
- Riot API error? Verify your API key is valid and not expired
- Commands unresponsive? Check the bot log at `Log/info.log`
- Google Sheets integration not working? Verify service account setup
- Match display issues? Check that teams were properly created with `/run_matchmaking`
- Database locked errors? Restart the bot to clear any hanging connections
- Discord permission issues? Ensure the bot has proper permissions in the server

---

##  Future Development

### Planned Improvements
- Improve image generation with more customization options
- Expand Google Sheets integration for match results
- Add tournament bracket management
- Implement historical player performance tracking
- Create a web dashboard for tournament management
- Support for multiple games beyond League of Legends
- Automated match result verification
- Add ability for admins to selectively remove players from check-in pool
- Implement player opt-out functionality after check-in


---

