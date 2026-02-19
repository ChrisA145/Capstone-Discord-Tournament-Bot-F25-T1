import discord
import asyncio
import json
import random
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Player, Game
from controller.api import Api_Collection

logger = settings.logging.getLogger("discord")

class PlayerModel:
    @staticmethod
    def update_toxicity(interaction, player_name):
        """
        Add a toxicity point to the specified player.
        
        Args:
            interaction: The Discord interaction object
            player_name: The name of the player to add toxicity to
            
        Returns:
            bool: True if player was found and updated, False otherwise
        """
        try:
            db = Player()
            player_id = db.find_player_by_name(player_name)
            
            if player_id:
                new_points = db.add_toxicity_point(player_id)
                db.close_db()
                return True
            
            db.close_db()
            return False
        except Exception as ex:
            logger.error(f"update_toxicity failed with error {ex}")
            return False

class PlayerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list_players", description="List all registered players")
    async def list_players(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()
            try:
                # Get all players from database
                all_players = Player.get_all_player(db)

                if not all_players or len(all_players) == 0:
                    await interaction.response.send_message("No players registered yet.")
                    return

                # Create an embed to display players
                embed = discord.Embed(
                    title="League of Legends Players",
                    color=discord.Color.blue(),
                    description=f"Total Players: {len(all_players)}"
                )

                for i, player in enumerate(all_players):
                    user_id, game_name, tag_id = player

                    # Try to get player stats from game table
                    try:
                        db.cursor.execute(
                            "SELECT role, tier, rank, wins, losses, wr, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                            (user_id,)
                        )
                        game_data = db.cursor.fetchone()

                        if game_data:
                            role_data, tier, rank, wins, losses, win_rate, manual_tier = game_data

                            # Role color mapping (using League of Legends colors)
                            role_colors = {
                                "top": "🟥",      # Red
                                "jungle": "🟩",   # Green
                                "mid": "🟨",      # Yellow
                                "bottom": "🟦",   # Blue
                                "support": "🟪",  # Purple
                                "tbd": "⬜",      # White/empty
                                "forced": "⬛"     # Black/forced
                            }
                            
                            # Parse role preferences
                            role_str = "None"
                            if role_data:
                                try:
                                    roles = json.loads(role_data)
                                    if isinstance(roles, list):
                                        colored_roles = []
                                        for role in roles:
                                            role_lower = role.lower()
                                            role_emoji = role_colors.get(role_lower, "⬜")
                                            colored_roles.append(f"{role_emoji} {role.capitalize()}")
                                        role_str = "  ".join(colored_roles)
                                    else:
                                        role_str = str(roles)
                                except:
                                    role_str = str(role_data)

                            # Format tier and rank
                            tier_str = tier.capitalize() if tier else "Unranked"
                            rank_str = rank if rank else ""

                            # Calculate win rate if not provided
                            if win_rate is None and wins is not None and losses is not None:
                                total_games = wins + losses
                                if total_games > 0:
                                    win_rate = (wins / total_games) * 100
                                else:
                                    win_rate = 0

                            # Format stats string
                            stats = f"**Rank:** {tier_str} {rank_str}\n"
                            
                            # Add manual tier if available
                            if manual_tier is not None:
                                stats += f"**Manual Tier:** {manual_tier:.1f}/10\n"
                            
                            if wins is not None and losses is not None:
                                total_games = wins + losses
                                # Calculate win rate if not already provided
                                if win_rate is None and total_games > 0:
                                    win_rate = (wins / total_games) * 100
                                
                                win_rate_str = f" ({win_rate:.1f}%)" if win_rate is not None else ""
                                stats += f"**Record:** {wins}W {losses}L{win_rate_str}"

                            # Add player to embed (up to 15 players per embed)
                            if i < 15:
                                embed.add_field(
                                    name=f"{game_name}",
                                    value=f"**ID:** {tag_id}\n{stats}\n**Roles:** {role_str}",
                                    inline=True
                                )
                        else:
                            # Fallback if no game data exists
                            if i < 15:
                                embed.add_field(
                                    name=f"{game_name}",
                                    value=f"**ID:** {tag_id}\nNo game data available",
                                    inline=True
                                )
                    except Exception as ex:
                        logger.error(f"Error retrieving data for player {user_id}: {ex}")
                        if i < 15:
                            embed.add_field(
                                name=f"{game_name}",
                                value=f"**ID:** {tag_id}\nError retrieving player data",
                                inline=True
                            )

                await interaction.response.send_message(embed=embed)

                # If there are more than 15 players, send additional messages
                if len(all_players) > 15:
                    remaining_embeds = []
                    current_embed = None

                    for i in range(15, len(all_players)):
                        # Create a new embed every 15 players
                        if i % 15 == 0:
                            current_embed = discord.Embed(
                                title=f"League of Legends Players (Continued {i // 15 + 1})",
                                color=discord.Color.blue()
                            )
                            remaining_embeds.append(current_embed)

                        user_id, game_name, tag_id = all_players[i]

                        # Get player stats
                        try:
                            db.cursor.execute(
                                "SELECT role, tier, rank, wins, losses, wr, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                                (user_id,)
                            )
                            game_data = db.cursor.fetchone()

                            if game_data:
                                role_data, tier, rank, wins, losses, win_rate, manual_tier = game_data

                                # Role color mapping (using League of Legends colors)
                                role_colors = {
                                    "top": "🟥",      # Red
                                    "jungle": "🟩",   # Green
                                    "mid": "🟨",      # Yellow
                                    "bottom": "🟦",   # Blue
                                    "support": "🟪",  # Purple
                                    "tbd": "⬜",      # White/empty
                                    "forced": "⬛"     # Black/forced
                                }
                                
                                # Parse role preferences
                                role_str = "None"
                                if role_data:
                                    try:
                                        roles = json.loads(role_data)
                                        if isinstance(roles, list):
                                            colored_roles = []
                                            for role in roles:
                                                role_lower = role.lower()
                                                role_emoji = role_colors.get(role_lower, "⬜")
                                                colored_roles.append(f"{role_emoji} {role.capitalize()}")
                                            role_str = "  ".join(colored_roles)
                                        else:
                                            role_str = str(roles)
                                    except:
                                        role_str = str(role_data)

                                # Format tier and rank
                                tier_str = tier.capitalize() if tier else "Unranked"
                                rank_str = rank if rank else ""

                                # Calculate win rate if not provided
                                if win_rate is None and wins is not None and losses is not None:
                                    total_games = wins + losses
                                    if total_games > 0:
                                        win_rate = (wins / total_games) * 100
                                    else:
                                        win_rate = 0

                                # Format stats string
                                stats = f"**Rank:** {tier_str} {rank_str}\n"
                                
                                # Add manual tier if available
                                if manual_tier is not None:
                                    stats += f"**Manual Tier:** {manual_tier:.1f}/10\n"
                                    
                                if wins is not None and losses is not None:
                                    total_games = wins + losses
                                    # Calculate win rate if not already provided
                                    if win_rate is None and total_games > 0:
                                        win_rate = (wins / total_games) * 100
                                    
                                    win_rate_str = f" ({win_rate:.1f}%)" if win_rate is not None else ""
                                    stats += f"**Record:** {wins}W {losses}L{win_rate_str}"

                                current_embed.add_field(
                                    name=f"{game_name}",
                                    value=f"**ID:** {tag_id}\n{stats}\n**Roles:** {role_str}",
                                    inline=True
                                )
                            else:
                                current_embed.add_field(
                                    name=f"{game_name}",
                                    value=f"**ID:** {tag_id}\nNo game data available",
                                    inline=True
                                )
                        except Exception as ex:
                            logger.error(f"Error retrieving data for player {user_id}: {ex}")
                            current_embed.add_field(
                                name=f"{game_name}",
                                value=f"**ID:** {tag_id}\nError retrieving player data",
                                inline=True
                            )

                    for embed in remaining_embeds:
                        await interaction.followup.send(embed=embed)

            except Exception as ex:
                logger.error(f"Error listing players: {ex}")
                await interaction.response.send_message(f"Error listing players: {str(ex)}")
            finally:
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)

    @app_commands.command(name="player_match_history", description="View a player's match history")
    @app_commands.describe(player_name="The summoner name of the player to look up")
    async def player_match_history(self, interaction: discord.Interaction, player_name: str):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()
            try:
                # Find player ID from name
                db.cursor.execute("SELECT user_id FROM player WHERE game_name LIKE ?", (f"%{player_name}%",))
                result = db.cursor.fetchone()

                if not result:
                    await interaction.response.send_message(f"Player '{player_name}' not found", ephemeral=True)
                    return

                player_id = result[0]

                # Get player details
                db.cursor.execute("SELECT game_name, tag_id FROM player WHERE user_id = ?", (player_id,))
                player_data = db.cursor.fetchone()
                game_name, tag_id = player_data

                # Get player stats
                db.cursor.execute(
                    "SELECT tier, rank, role, wins, losses, wr, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (player_id,)
                )
                game_data = db.cursor.fetchone()

                if not game_data:
                    await interaction.response.send_message(f"No game data found for player '{player_name}'",
                                                            ephemeral=True)
                    return

                tier, rank, role_json, wins, losses, win_rate, manual_tier = game_data

                # Role color mapping (using League of Legends colors)
                role_colors = {
                    "top": "🟥",      # Red
                    "jungle": "🟩",   # Green
                    "mid": "🟨",      # Yellow
                    "bottom": "🟦",   # Blue
                    "support": "🟪",  # Purple
                    "tbd": "⬜",      # White/empty
                    "forced": "⬛"     # Black/forced
                }
                
                # Parse role preferences
                role_str = "None"
                if role_json:
                    try:
                        roles = json.loads(role_json)
                        if isinstance(roles, list):
                            colored_roles = []
                            for role in roles:
                                role_lower = role.lower()
                                role_emoji = role_colors.get(role_lower, "⬜")
                                colored_roles.append(f"{role_emoji} {role.capitalize()}")
                            role_str = "  ".join(colored_roles)
                        else:
                            role_str = str(roles)
                    except:
                        role_str = str(role_json)

                # Get match history
                db.cursor.execute(
                    """
                    SELECT m.teamId, m.teamUp, m.win, m.loss, m.date_played 
                    FROM Matches m
                    WHERE m.user_id = ?
                    ORDER BY m.date_played DESC
                    LIMIT 10
                    """,
                    (player_id,)
                )
                matches = db.cursor.fetchall()

                # Create player profile embed
                embed = discord.Embed(
                    title=f"Player Profile: {game_name} {tag_id}",
                    color=discord.Color.gold()
                )

                # Add player stats
                embed.add_field(
                    name="Rank",
                    value=f"{tier.capitalize() if tier else 'Unranked'} {rank if rank else ''}",
                    inline=True
                )

                # Add manual tier if available
                if manual_tier is not None:
                    embed.add_field(
                        name="Manual Tier",
                        value=f"{manual_tier:.1f} / 10.0",
                        inline=True
                    )

                embed.add_field(
                    name="Win/Loss",
                    value=f"{wins}W {losses}L" if wins is not None and losses is not None else "No record",
                    inline=True
                )

                if wins is not None and losses is not None:
                    total_games = wins + losses
                    if total_games > 0:
                        calculated_wr = (wins / total_games) * 100
                        embed.add_field(
                            name="Win Rate",
                            value=f"{calculated_wr:.1f}%",
                            inline=True
                        )

                embed.add_field(
                    name="Preferred Roles",
                    value=role_str,
                    inline=False
                )

                # Add match history
                if matches:
                    match_history = ""
                    for match in matches:
                        match_id, team, win, loss, date = match
                        result = "Win" if win == "yes" else "Loss" if loss == "yes" else "Unknown"
                        match_date = date if date else "Unknown date"
                        match_history += f"**{match_id}**: {result} (Team {team[-1]}) - {match_date}\n"

                    embed.add_field(
                        name="Recent Matches",
                        value=match_history if match_history else "No match history",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Recent Matches",
                        value="No match history found",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)

            except Exception as ex:
                logger.error(f"Error retrieving player history: {ex}")
                await interaction.response.send_message(f"Error retrieving player history: {str(ex)}")
            finally:
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)
                                                  
    @app_commands.command(name="simulate_checkins", description="Simulate League of Legends players checking in")
    @app_commands.describe(
        player_count="Number of players to simulate (default: 10)"
    )
    async def simulate_checkins(self, interaction: discord.Interaction, player_count: int = 10):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)
            db = Tournament_DB()

            # League of Legends specific data
            lanes = ["top", "jungle", "mid", "bottom", "support"]
            ranks = ["I", "II", "III", "IV"]

            # Delete existing simulated players to avoid duplicates
            try:
                db.cursor.execute("DELETE FROM player WHERE user_id >= 9000000")
                db.cursor.execute("DELETE FROM game WHERE user_id >= 9000000")
                db.connection.commit()
                logger.info("Cleared previous simulated players")
            except Exception as ex:
                logger.error(f"Error clearing previous players: {ex}")

            # Load player data from combined_player_data.json
            real_player_data = []
            try:
                with open('combined_player_data.json', 'r') as file:
                    player_data = json.load(file)
                    # Flatten the player data into a single list
                    for rank_tier, players in player_data.items():
                        for player in players:
                            player['rank_tier'] = rank_tier
                            real_player_data.append(player)
                
                # Shuffle and limit to the requested count
                random.shuffle(real_player_data)
                selected_players = real_player_data[:player_count]
                
                # Create a progress embed
                embed = discord.Embed(
                    title="Player Simulation Progress",
                    description=f"Processing {len(selected_players)} players from combined_player_data.json",
                    color=discord.Color.blue()
                )
                progress_message = await interaction.followup.send(embed=embed)
                
                # Import the API functionality
                from controller.api import Api_Collection
                
                # Track stats
                api_lookups_successful = 0
                api_lookups_failed = 0
                players_created = 0
                
                # Process each player
                for i, player_data in enumerate(selected_players):
                    player_id = 9000000 + i
                    summoner_name = player_data['name']
                    tag_id = player_data['tag'].replace('#', '') if player_data['tag'].startswith('#') else player_data['tag']
                    fallback_tier = player_data['rank_tier'].lower()
                    
                    # Update progress
                    embed.description = f"Processing player {i+1}/{len(selected_players)}: {summoner_name}#{tag_id}"
                    await interaction.edit_original_response(embed=embed)
                    
                    # Try to get stats from Riot API
                    api_data = None
                    try:
                        api_result = await Api_Collection.get_player_details(interaction, summoner_name, tag_id)
                        
                        if api_result and isinstance(api_result, list) and len(api_result) > 0:
                            tier = api_result[0].get('tier', '').lower()
                            rank = api_result[0].get('rank', '')
                            wins = api_result[0].get('wins', 0)
                            losses = api_result[0].get('losses', 0)
                            
                            # If we got valid data, use it
                            if tier and rank:
                                api_data = {
                                    'tier': tier,
                                    'rank': rank,
                                    'wins': wins,
                                    'losses': losses
                                }
                                api_lookups_successful += 1
                                
                                # Add to embed
                                embed.add_field(
                                    name=f"✅ {summoner_name}",
                                    value=f"{tier.capitalize()} {rank} - {wins}W {losses}L",
                                    inline=True
                                )
                    except Exception as ex:
                        logger.error(f"API error for {summoner_name}: {ex}")
                    
                    # If API failed, use fallback data
                    if not api_data:
                        api_lookups_failed += 1
                        
                        # Use fallback tier from JSON, random rank and win/loss
                        tier = fallback_tier
                        rank = random.choice(ranks)
                        wins = random.randint(10, 200)
                        losses = random.randint(10, 200)
                        
                        # Add to embed
                        embed.add_field(
                            name=f"📄 {summoner_name}",
                            value=f"{fallback_tier.capitalize()} {rank} (Fallback data)",
                            inline=True
                        )
                    else:
                        # Use API data
                        tier = api_data['tier']
                        rank = api_data['rank']
                        wins = api_data['wins']
                        losses = api_data['losses']
                    
                    # Update the embed periodically
                    if i % 5 == 0 or i == len(selected_players) - 1:
                        await interaction.edit_original_response(embed=embed)
                    
                    try:
                        # Insert player record
                        insert_query = "INSERT INTO player(user_id, game_name, tag_id) VALUES(?, ?, ?)"
                        db.cursor.execute(insert_query, (player_id, summoner_name, tag_id))

                        # Insert player preferences (1-3 lane preferences)
                        pref_count = random.randint(1, 3)
                        random_lanes = random.sample(lanes, k=pref_count)

                        # Calculate initial manual tier based on rank
                        game_db = Game(db_name=settings.DATABASE_NAME)
                        manual_tier = game_db.calculate_manual_tier(tier, rank)
                        
                        # Insert skills and preferences including manual tier
                        game_query = "INSERT INTO game(user_id, game_name, tier, rank, role, wins, losses, manual_tier) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
                        db.cursor.execute(
                            game_query,
                            (
                                player_id,
                                summoner_name,
                                tier,
                                rank,
                                json.dumps(random_lanes),
                                wins,
                                losses,
                                manual_tier
                            )
                        )
                        
                        players_created += 1
                    except Exception as ex:
                        logger.error(f"Error creating player {summoner_name}: {ex}")
                    
                    # Add a small delay to avoid rate limiting
                    await asyncio.sleep(0.2)
                
                # Commit changes
                db.connection.commit()
                
                # Final summary embed
                summary_embed = discord.Embed(
                    title="Player Simulation Complete",
                    description=f"Successfully created {players_created} simulated players",
                    color=discord.Color.green()
                )
                
                summary_embed.add_field(
                    name="API Lookups",
                    value=f"✅ Successful: {api_lookups_successful}\n❌ Failed: {api_lookups_failed}",
                    inline=False
                )
                
                summary_embed.add_field(
                    name="Data Sources",
                    value=f"🔹 Riot API: {api_lookups_successful} players\n🔸 JSON Fallback: {api_lookups_failed} players",
                    inline=False
                )
                
                await interaction.followup.send(embed=summary_embed)
                
            except Exception as ex:
                logger.error(f"Error in simulate_checkins: {ex}")
                db.connection.commit()
                db.close_db()
                await interaction.followup.send(f"Error simulating players: {ex}")
                return
                
            db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                 ephemeral=True)


    # This will add toxicity points to the player the admin chooses
    @app_commands.command(name="toxicity", description="Add 1 point to the player's toxicity level")
    @app_commands.describe(player="The player to add toxicity to")
    async def toxicity(self, interaction: discord.Interaction, player: str):
        # Check if the player is an admin and end if not
        if interaction.user.guild_permissions.administrator:
            try:
                # Call the method to update the database and check if it returns a success
                found_user = PlayerModel.update_toxicity(interaction, player.lower())
                if found_user:
                    await interaction.response.send_message(f"{player}'s toxicity point has been updated.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{player}, this username could not be found.", ephemeral=True)

            except Exception as e:
                logger.error(f'Toxicity command error: {e}')
                await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ This command is only for administrators.", ephemeral=True)
            return

    # Get a player's toxicity points
    @app_commands.command(name="get_toxicity", description="Get a player's current toxicity points")
    @app_commands.describe(player="The player to check")
    async def get_toxicity(self, interaction: discord.Interaction, player: str):
        try:
            db = Player()
            player_id = db.find_player_by_name(player.lower())
            
            if player_id:
                points = db.get_toxicity_points(player_id)
                db.close_db()
                await interaction.response.send_message(f"{player} has {points} toxicity point(s).", ephemeral=True)
            else:
                db.close_db()
                await interaction.response.send_message(f"{player}, this username could not be found.", ephemeral=True)
        except Exception as e:
            logger.error(f'Get toxicity command error: {e}')
            await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PlayerManagement(bot))