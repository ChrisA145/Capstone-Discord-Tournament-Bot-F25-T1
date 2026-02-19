# KSU Esports Tournament Bot - Setup Guide

This guide will walk you through setting up and configuring the KSU Esports Tournament Discord bot from scratch. Follow these steps in order to ensure a smooth installation and configuration.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before installing the bot, make sure you have the following:

1. **Discord Bot Token**
   - Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Navigate to the "Bot" tab and click "Add Bot"
   - Copy the token for later use
   - Enable the following Privileged Gateway Intents:
     - Presence Intent
     - Server Members Intent
     - Message Content Intent

2. **Riot API Key** (for retrieving player data)
   - Register at the [Riot Developer Portal](https://developer.riotgames.com/)
   - Obtain an API key

3. **Python 3.9+** installed on your system

4. **Discord Server** with administrator permissions

## Installation

### Option 1: Standard Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ksu_Esports_Tournament-.git
   cd ksu_Esports_Tournament-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Docker Installation

If you prefer using Docker, a Dockerfile is provided in the repository.

1. **Build the Docker image**:
   ```bash
   docker build -t ksu-esports-bot .
   ```

## Configuration

### Setting Up Environment Variables

1. **Create a `.env` file** in the root directory:
   ```bash
   touch .env
   ```

2. **Add the following configuration** to the `.env` file:
   ```
   # Discord Settings
   DISCORD_APITOKEN=your_discord_bot_token
   DISCORD_GUILD=your_guild_id
   
   # Database Settings
   DATABASE_NAME=ksu_tournament.db
   
   # Channel IDs
   TOURNAMENT_CH=your_tournament_announcements_channel_id
   CHANNEL_PLAYER=your_player_channel_id
   CHANNEL_CONFIG=your_config_channel_id
   PRIVATE_CH=your_private_channel_id
   FEEDBACK_CH=your_feedback_channel_id
   
   # API Settings
   RIOT_API_KEY=your_riot_api_key
   API_URL=https://na1.api.riotgames.com/lol
   
   # OpenAI Settings (Optional)
   OPEN_AI_KEY=your_openai_key
   ```

3. **Replace the placeholder values** with your actual configuration:
   - `your_discord_bot_token`: The token from the Discord Developer Portal
   - `your_guild_id`: Your Discord server's ID (Right-click server → Copy ID)
   - Channel IDs: Right-click on channels → Copy ID
   - `your_riot_api_key`: Your Riot Games API key

### Bot Permissions

1. **Generate an invite link** using the Discord Developer Portal:
   - Go to the OAuth2 → URL Generator
   - Select the following scopes:
     - bot
     - applications.commands
   - Select the following bot permissions:
     - Administrator (or more granular permissions if preferred)

2. **Invite the bot** to your server using the generated URL

### Database Setup

The bot will automatically create necessary database tables on first run, but you can initialize them manually:

```bash
python -c "from model.dbc_model import Tournament_DB, Player, Game, Matches, MVP_Votes; db = Tournament_DB(); Player.createTable(db); Game.createTable(db); Matches.createTable(db); MVP_Votes.createTable(db)"
```

## Running the Bot

### Starting the Bot

1. **Activate the virtual environment** (if not already activated):
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

2. **Run the bot**:
   ```bash
   python tournament.py
   ```

### Docker Run

If you're using Docker:

```bash
docker run --env-file .env -v $(pwd)/data:/app/data ksu-esports-bot
```

## Bot Commands

### Admin Commands

- **/run_matchmaking** - Create balanced teams based on player data
- **/swap_team_players** - Swap players between teams for better balance
- **/display_teams** - Display current teams for a specific match
- **/announce_teams** - Announce teams to a channel (dropdown selection)
- **/record_match_result** - Record which team won a match
- **/view_player_tier** - View a player's tier/rank information
- **/adjust_player_tier** - Manually adjust a player's tier value
- **/reset_player_tier** - Reset a player's manual tier adjustment
- **/list_players** - View registered players and their information
- **/player_match_history** - View a player's match history

### Player Commands

- **/signup** - Register for the tournament
- **/role** - Set role preferences
- **/vote_mvp** - Vote for the MVP in a match

## Channel Setup

Create the following channels in your Discord server:

1. **Tournament Announcements** (public)
   - For announcing teams and tournament information
   - Set this channel ID as `TOURNAMENT_CH` in your .env file

2. **Player Registration** (public)
   - Where players can sign up for tournaments
   - Set this channel ID as `CHANNEL_PLAYER` in your .env file

3. **Admin Channel** (private)
   - For tournament administration
   - Set this channel ID as `PRIVATE_CH` in your .env file

4. **Feedback Channel** (public)
   - For players to provide feedback
   - Set this channel ID as `FEEDBACK_CH` in your .env file

## Docker Deployment

### Docker Compose

For easier deployment, you can use Docker Compose. Create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  bot:
    build: .
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

Run with:
```bash
docker-compose up -d
```

### Updating the Bot

1. **Pull the latest changes**:
   ```bash
   git pull
   ```

2. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Restart the bot**:
   ```bash
   python tournament.py
   ```

### Docker Update

If using Docker:
```bash
docker-compose down
git pull
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

1. **Bot doesn't respond to commands**
   - Check if the bot is online in your Discord server
   - Verify the bot token in the `.env` file
   - Ensure the bot has the necessary permissions
   - Check the console output for error messages

2. **Database errors**
   - Verify the database path is correct
   - Check file permissions
   - Make sure the database file is not corrupted

3. **Riot API errors**
   - Verify your Riot API key is valid and not expired
   - Check API rate limits
   - Ensure the region is correctly configured

4. **Channel not found errors**
   - Verify channel IDs in the `.env` file
   - Make sure the bot has access to the channels
   - Check if the channel format is correct (numeric ID recommended)

### Logs

Check the logs in the `Log/` directory for detailed error information.

### Getting Help

If you encounter issues not covered in this guide:
1. Check the error logs
2. Consult the [documentation](./design_document.md)
3. Contact the development team

## Security Considerations

1. **API Keys**: Keep your `.env` file secure and never commit it to version control
2. **Bot Permissions**: Use the minimum required permissions for the bot
3. **Database**: Backup your database regularly

## Maintenance

1. **Database Backups**:
   ```bash
   cp ksu_tournament.db ksu_tournament_backup_$(date +%F).db
   ```

2. **Log Rotation**:
   - Archive or delete old logs periodically to save space

## Advanced Configuration

### Custom Role Colors

You can customize the role colors in the bot's code:

1. Edit `controller/matchmaking_controller.py` and `controller/team_display_controller.py`
2. Modify the `role_colors` dictionary to change the emojis/colors for each role

### Matchmaking Algorithm Tuning

The genetic matchmaking algorithm can be tuned to match your tournament's needs:

1. Edit `controller/genetic_match_making.py`
2. Modify the weights in the fitness function:
   - `team_balance_score` weight (default: 0.7)
   - `role_matchup_score` weight (default: 0.3)
3. Adjust population size and generations for different player pool sizes

## Conclusion

Your KSU Esports Tournament Discord bot should now be fully set up and ready to use. The bot provides a comprehensive set of tools for running League of Legends tournaments, including player registration, team formation, match result tracking, and MVP voting.

For more detailed information about the bot's architecture and functionality, please refer to the [Design Document](./design_document.md).