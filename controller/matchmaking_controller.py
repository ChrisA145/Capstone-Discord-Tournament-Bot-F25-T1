import discord
import asyncio
import random
import json
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Game
from controller.genetic_match_making import GeneticMatchMaking

logger = settings.logging.getLogger("discord")

class MatchmakingController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    class VolunteerSelectionView(discord.ui.View):
        def __init__(self, players, needed_count, timeout=300):
            super().__init__(timeout=timeout)
            self.players = players
            self.needed_count = needed_count
            self.selected_players = []
            self.is_complete = False

            # Add player select menu
            self._add_player_select()
            self._add_action_buttons()

        def _add_player_select(self):
            # Create a select menu with player options
            options = []
            for player in self.players[:25]:  # Discord has a 25-option limit
                player_name = player.get('game_name', str(player.get('user_id')))
                tier = player.get('tier', 'unknown').capitalize()
                rank = player.get('rank', '')

                option = discord.SelectOption(
                    label=f"{player_name}",
                    description=f"{tier} {rank}",
                    value=str(player.get('user_id')),
                    default=player.get('user_id') in [p.get('user_id') for p in self.selected_players]
                )
                options.append(option)

            # Create select menu
            select = discord.ui.Select(
                placeholder="Select players to sit out...",
                min_values=0,
                max_values=min(len(options), self.needed_count),
                options=options
            )

            # Add callback
            select.callback = self.select_callback

            # Add select to view
            self.add_item(select)

        def _add_action_buttons(self):
            # Add a "Done" button
            done_button = discord.ui.Button(
                label=f"Confirm Selection ({len(self.selected_players)}/{self.needed_count})",
                style=discord.ButtonStyle.primary,
                disabled=len(self.selected_players) != self.needed_count,
                row=1
            )
            done_button.callback = self.done_callback
            self.add_item(done_button)

            # Add a "Random" button
            random_button = discord.ui.Button(
                label="Select Randomly",
                style=discord.ButtonStyle.danger,
                row=1
            )
            random_button.callback = self.random_callback
            self.add_item(random_button)

        async def select_callback(self, interaction):
            # Get selected player IDs from select menu
            selected_ids = [int(value) for value in interaction.data['values']]

            # Update selected players list
            self.selected_players = [p for p in self.players if p.get('user_id') in selected_ids]

            # Clear and rebuild the view
            self.clear_items()
            self._add_player_select()
            self._add_action_buttons()

            # Update the message
            await interaction.response.edit_message(
                content=f"Select {self.needed_count} volunteers to sit out (receiving participation points).\n"
                        f"Currently selected: {len(self.selected_players)}/{self.needed_count}",
                view=self
            )

        async def done_callback(self, interaction):
            if len(self.selected_players) == self.needed_count:
                self.is_complete = True
                self.stop()

                # Create a list of selected player names
                player_names = [f"{p.get('game_name')} ({p.get('tier', '').capitalize()} {p.get('rank', '')})"
                                for p in self.selected_players]

                await interaction.response.edit_message(
                    content=f"Selection complete! {self.needed_count} volunteers will sit out and receive participation points:\n" +
                            "\n".join([f"- {name}" for name in player_names]),
                    view=None
                )
            else:
                await interaction.response.send_message(
                    f"Please select exactly {self.needed_count} players before confirming.",
                    ephemeral=True
                )

        async def random_callback(self, interaction):
            # Select players randomly
            self.selected_players = random.sample(self.players, self.needed_count)
            self.is_complete = True
            self.stop()

            # Create a list of selected player names
            player_names = [f"{p.get('game_name')} ({p.get('tier', '').capitalize()} {p.get('rank', '')})"
                            for p in self.selected_players]

            await interaction.response.edit_message(
                content=f"Randomly selected {self.needed_count} players to sit out and receive participation points:\n" +
                        "\n".join([f"- {name}" for name in player_names]),
                view=None
            )

    @app_commands.command(name="simulate_volunteers", description="Simulate volunteers for sitting out")
    @app_commands.describe(count="Number of volunteers needed")
    async def simulate_volunteers(self, interaction: discord.Interaction, count: int = 4):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()

            try:
                # Get all players
                db.cursor.execute("""
                    SELECT p.user_id, p.game_name, p.tag_id, g.tier, g.rank 
                    FROM player p
                    JOIN game g ON p.user_id = g.user_id
                    GROUP BY p.user_id
                    HAVING MAX(g.game_date)
                """)

                all_players = []
                for record in db.cursor.fetchall():
                    user_id, game_name, tag_id, tier, rank = record
                    all_players.append({
                        'user_id': user_id,
                        'game_name': game_name,
                        'tier': tier.lower() if tier else 'default',
                        'rank': rank if rank else ''
                    })

                if len(all_players) < count:
                    await interaction.response.send_message(
                        f"Not enough players registered. Need at least {count} players, but only have {len(all_players)}."
                    )
                    return

                # Mark some players as "volunteering"
                volunteers = random.sample(all_players, count)

                # Create a volunteer table for demo
                volunteer_embed = discord.Embed(
                    title=f"Simulated Volunteers ({count} players)",
                    color=discord.Color.green(),
                    description="These players have volunteered to sit out and receive participation points."
                )

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
                
                for i, player in enumerate(volunteers):
                    name = player.get('game_name')
                    tier = player.get('tier', 'unknown').capitalize()
                    rank = player.get('rank', '')
                    
                    # Try to get roles
                    db.cursor.execute(
                        "SELECT role FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                        (player.get('user_id'),)
                    )
                    role_result = db.cursor.fetchone()
                    
                    # Format roles with colors
                    colored_roles = []
                    if role_result and role_result[0]:
                        try:
                            roles = json.loads(role_result[0])
                            if isinstance(roles, list):
                                for role in roles:
                                    role_lower = role.lower()
                                    role_emoji = role_colors.get(role_lower, "⬜")
                                    colored_roles.append(f"{role_emoji} {role.capitalize()}")
                        except:
                            pass
                    
                    role_str = '  '.join(colored_roles) if colored_roles else 'None'
                    
                    value_str = f"**Rank:** {tier} {rank}"
                    if colored_roles:
                        value_str += f"\n**Roles:** {role_str}"

                    volunteer_embed.add_field(
                        name=f"Player {i + 1}: {name}",
                        value=value_str,
                        inline=True
                    )

                # Record volunteers in database with "volunteer" status
                session_id = f"volunteer_session_{int(asyncio.get_event_loop().time())}"
                # Get the next match ID for the volunteer session
                from model.dbc_model import Matches
                matches_db = Matches(db_name=settings.DATABASE_NAME)
                volunteer_match_num = matches_db.get_next_match_id()
                for player in volunteers:
                    user_id = player.get('user_id')
                    if user_id:
                        query = "INSERT INTO Matches(user_id, teamUp, teamId, match_num) VALUES(?, ?, ?, ?)"
                        db.cursor.execute(query, (user_id, "volunteer", session_id, volunteer_match_num))

                db.connection.commit()
                db.close_db()

                await interaction.response.send_message(
                    content=f"Simulated {count} volunteers for sitting out.",
                    embed=volunteer_embed
                )

            except Exception as ex:
                logger.error(f"Error simulating volunteers: {ex}")
                await interaction.response.send_message(f"Error simulating volunteers: {str(ex)}")
                db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)

    @app_commands.command(name="run_matchmaking", description="Run matchmaking with registered players")
    @app_commands.describe(
        players_per_game="Number of players per game (default: 10)",
        selection_method="How to select players who sit out: random, rank, or volunteer (default: random)"
    )
    async def run_matchmaking(
            self,
            interaction: discord.Interaction,
            players_per_game: int = 10,
            selection_method: str = "random"
    ):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)

            try:
                # Get all eligible players
                db = Tournament_DB()
                
                all_players = []

                try:
                    # Get all players with game data
                    db.cursor.execute("""
                        SELECT p.user_id, p.game_name, p.tag_id, g.tier, g.rank, g.role, g.wins, g.losses, g.wr, g.manual_tier
                        FROM player p
                        JOIN game g ON p.user_id = g.user_id
                        GROUP BY p.user_id
                        HAVING MAX(g.game_date)
                        ORDER BY 
                            CASE 
                                WHEN g.tier = 'challenger' THEN 1
                                WHEN g.tier = 'grandmaster' THEN 2
                                WHEN g.tier = 'master' THEN 3
                                WHEN g.tier = 'diamond' THEN 4
                                WHEN g.tier = 'emerald' THEN 5
                                WHEN g.tier = 'platinum' THEN 6
                                WHEN g.tier = 'gold' THEN 7
                                WHEN g.tier = 'silver' THEN 8
                                WHEN g.tier = 'bronze' THEN 9
                                WHEN g.tier = 'iron' THEN 10
                                ELSE 11
                            END, 
                            CASE 
                                WHEN g.rank = 'I' THEN 1
                                WHEN g.rank = 'II' THEN 2
                                WHEN g.rank = 'III' THEN 3
                                WHEN g.rank = 'IV' THEN 4
                                ELSE 5
                            END
                    """)

                    player_records = db.cursor.fetchall()

                    for record in player_records:
                        user_id, game_name, tag_id, tier, rank, role_json, wins, losses, wr, manual_tier = record

                        # Parse role preferences
                        roles = []
                        if role_json:
                            try:
                                roles = json.loads(role_json)
                                if not isinstance(roles, list):
                                    roles = [str(roles)]
                            except:
                                roles = [str(role_json)]

                        player = {
                            'user_id': user_id,
                            'game_name': game_name,
                            'tag_id': tag_id,
                            'tier': tier.lower() if tier else 'default',
                            'rank': rank if rank else 'V',
                            'role': roles,
                            'wins': wins if wins is not None else 0,
                            'losses': losses if losses is not None else 0,
                            'wr': float(wr) * 100 if wr is not None else 50.0,
                            'manual_tier': manual_tier
                        }

                        all_players.append(player)

                except Exception as ex:
                    logger.error(f"Error fetching players: {ex}")
                    await interaction.followup.send(f"Error fetching players: {str(ex)}")
                    db.close_db()
                    return

                # Calculate how many games we can run and if we need players to sit out
                total_players = len(all_players)

                if total_players < players_per_game:
                    await interaction.followup.send(
                        f"Not enough players for matchmaking. Need at least {players_per_game} players, but only have {total_players}."
                    )
                    db.close_db()
                    return

                game_count = total_players // players_per_game
                extra_players = total_players % players_per_game

                await interaction.followup.send(
                    f"Found {total_players} registered players.\n"
                    f"Can create {game_count} games with {players_per_game} players each.\n"
                    f"{extra_players} players will sit out and receive participation points."
                )

                # If we have extra players, determine who sits out
                players_to_exclude = []
                participation_players = []

                if extra_players > 0:
                    selection_method = selection_method.lower()

                    if selection_method == "rank":
                        # Use lowest ranked players
                        lowest_ranked_players = all_players[-extra_players:]
                        for player in lowest_ranked_players:
                            players_to_exclude.append(player['user_id'])
                            participation_players.append(player)

                        await interaction.followup.send(
                            f"**Using rank-based selection:** {extra_players} lowest-ranked players will sit out but receive participation points."
                        )

                    elif selection_method == "volunteer":
                        # Use interactive volunteer selection
                        await interaction.followup.send(
                            f"Please select {extra_players} volunteers to sit out (they will receive participation points)."
                        )

                        # Create volunteer selection view
                        view = self.VolunteerSelectionView(all_players, extra_players)
                        volunteer_msg = await interaction.followup.send(
                            content=f"Select {extra_players} volunteers to sit out (receiving participation points).\n"
                                    f"Currently selected: 0/{extra_players}",
                            view=view
                        )

                        # Wait for selection to complete
                        await view.wait()

                        if view.is_complete:
                            participation_players = view.selected_players
                            for player in participation_players:
                                players_to_exclude.append(player['user_id'])
                        else:
                            # Fallback to random if view timed out
                            random_players = random.sample(all_players, extra_players)
                            for player in random_players:
                                players_to_exclude.append(player['user_id'])
                                participation_players.append(player)

                            await interaction.followup.send(
                                f"Volunteer selection timed out. Falling back to random selection."
                            )

                    else:  # Default to random
                        # Randomly select players to sit out
                        random_players = random.sample(all_players, extra_players)
                        for player in random_players:
                            players_to_exclude.append(player['user_id'])
                            participation_players.append(player)

                        await interaction.followup.send(
                            f"**Using random selection:** {extra_players} randomly selected players will sit out but receive participation points."
                        )

                # Remove excluded players
                filtered_players = [p for p in all_players if p['user_id'] not in players_to_exclude]

                # Split players into pools based on skill
                filtered_players.sort(key=lambda p: (
                    {'challenger': 1, 'grandmaster': 2, 'master': 3, 'diamond': 4, 'emerald': 5,
                     'platinum': 6, 'gold': 7, 'silver': 8, 'bronze': 9, 'iron': 10}.get(p['tier'], 11),
                    {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}.get(p['rank'], 5),
                    -p.get('wr', 0)
                ))

                # Create pools for skill-based games
                pools = []
                for i in range(game_count):
                    start_idx = i * players_per_game
                    end_idx = start_idx + players_per_game
                    pool = filtered_players[start_idx:end_idx]
                    pools.append(pool)

                # Run matchmaking for each pool
                results = []
                matchmaker = GeneticMatchMaking()

                for pool_idx, pool in enumerate(pools):
                    # Get the next match ID
                    from model.dbc_model import Matches
                    matches_db = Matches(db_name=settings.DATABASE_NAME)
                    match_num = matches_db.get_next_match_id()
                    match_id = f"match_{match_num}"

                    # Split pool into balanced teams
                    team1, team2 = [], []

                    # Process players with performance metrics
                    processed_players = await matchmaker.calculate_performance(pool)

                    # Run matchmaking
                    best_chromosome, best_fitness = matchmaker.genetic_algorithm(
                        processed_players,
                        population_size=100,
                        generations=100,
                        team_size=players_per_game // 2
                    )

                    if best_chromosome:
                        team1, team2 = matchmaker.decode_chromosome(
                            best_chromosome,
                            processed_players,
                            team_size=players_per_game // 2
                        )
                    else:
                        # Fallback: simple alternating assignment
                        for i, player in enumerate(pool):
                            if i % 2 == 0:
                                team1.append(player)
                            else:
                                team2.append(player)

                    # Record match in database
                    for player in team1:
                        user_id = player.get('user_id')
                        if user_id:
                            query = "INSERT INTO Matches(user_id, teamUp, teamId, match_num) VALUES(?, ?, ?, ?)"
                            db.cursor.execute(query, (user_id, "team1", match_id, match_num))

                    for player in team2:
                        user_id = player.get('user_id')
                        if user_id:
                            query = "INSERT INTO Matches(user_id, teamUp, teamId, match_num) VALUES(?, ?, ?, ?)"
                            db.cursor.execute(query, (user_id, "team2", match_id, match_num))

                    # Calculate team metrics
                    team1_perf = matchmaker.team_performance(team1)
                    team2_perf = matchmaker.team_performance(team2)
                    diff = abs(team1_perf - team2_perf)
                    
                    # Calculate role matchup score for display
                    role_matchup_score = matchmaker.calculate_role_matchup_score(team1, team2)
                    role_matchup_percent = round(role_matchup_score * 100)

                    # Create embeds for the teams
                    team1_embed = discord.Embed(
                        title=f"Game {pool_idx + 1} - Team 1 (Match ID: {match_id})",
                        color=discord.Color.blue(),
                        description=f"Game {pool_idx + 1} of {game_count}\nRole Matchup Balance: {role_matchup_percent}%"
                    )

                    team2_embed = discord.Embed(
                        title=f"Game {pool_idx + 1} - Team 2 (Match ID: {match_id})",
                        color=discord.Color.red(),
                        description=f"Game {pool_idx + 1} of {game_count}\nRole Matchup Balance: {role_matchup_percent}%"
                    )

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
                    
                    # Add players to embeds
                    for i, player in enumerate(team1):
                        name = player.get('game_name', player.get('user_id', 'Unknown'))
                        tier = player.get('tier', 'Unknown').capitalize()
                        rank = player.get('rank', '')
                        roles = player.get('role', [])
                        
                        # Format roles with colors
                        colored_roles = []
                        for role in roles:
                            role_lower = role.lower()
                            role_emoji = role_colors.get(role_lower, "⬜")
                            colored_roles.append(f"{role_emoji} {role.capitalize()}")
                        
                        role_str = '  '.join(colored_roles) if colored_roles else 'None'

                        # Use the assigned_role from genetic algorithm if available
                        if "assigned_role" in player:
                            assigned_role = player["assigned_role"]
                        else:
                            # Fallback to first role preference
                            assigned_role = roles[0] if roles else "TBD"
                            logger.warning(f"Player {name} missing assigned_role, using first preference")
                        
                        assigned_role_lower = assigned_role.lower()
                        assigned_emoji = role_colors.get(assigned_role_lower, role_colors["tbd"])
                        colored_assigned = f"{assigned_emoji} {assigned_role.capitalize()}"

                        team1_embed.add_field(
                            name=f"Player {i + 1}: {name}",
                            value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}\n**Assigned:** {colored_assigned}",
                            inline=True
                        )

                    for i, player in enumerate(team2):
                        name = player.get('game_name', player.get('user_id', 'Unknown'))
                        tier = player.get('tier', 'Unknown').capitalize()
                        rank = player.get('rank', '')
                        roles = player.get('role', [])
                        
                        # Format roles with colors
                        colored_roles = []
                        for role in roles:
                            role_lower = role.lower()
                            role_emoji = role_colors.get(role_lower, "⬜")
                            colored_roles.append(f"{role_emoji} {role.capitalize()}")
                        
                        role_str = '  '.join(colored_roles) if colored_roles else 'None'

                        # Use the assigned_role from genetic algorithm if available
                        if "assigned_role" in player:
                            assigned_role = player["assigned_role"]
                        else:
                            # Fallback to first role preference
                            assigned_role = roles[0] if roles else "TBD"
                            logger.warning(f"Player {name} missing assigned_role, using first preference")
                        
                        assigned_role_lower = assigned_role.lower()
                        assigned_emoji = role_colors.get(assigned_role_lower, role_colors["tbd"])
                        colored_assigned = f"{assigned_emoji} {assigned_role.capitalize()}"

                        team2_embed.add_field(
                            name=f"Player {i + 1}: {name}",
                            value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}\n**Assigned:** {colored_assigned}",
                            inline=True
                        )

                    # Add metrics to embeds
                    team1_embed.set_footer(text=f"Team 1 Performance: {team1_perf:.2f}")
                    team2_embed.set_footer(text=f"Team 2 Performance: {team2_perf:.2f}")

                    # Create role matchup comparison
                    standard_roles = ["top", "jungle", "mid", "bottom", "support"]
                    role_matchup_text = "**Role Matchups:**\n"
                    
                    # Get role emoji mapping
                    role_emoji_map = {
                        "top": "🟥 Top",
                        "jungle": "🟩 Jungle",
                        "mid": "🟨 Mid", 
                        "bottom": "🟦 Bottom",
                        "support": "🟪 Support"
                    }
                    
                    for role in standard_roles:
                        team1_player = next((p for p in team1 if p.get("assigned_role") == role), None)
                        team2_player = next((p for p in team2 if p.get("assigned_role") == role), None)
                        
                        if team1_player and team2_player:
                            team1_name = team1_player.get('game_name', 'Unknown')
                            team2_name = team2_player.get('game_name', 'Unknown')
                            team1_tier = team1_player.get('tier', 'default').capitalize()
                            team2_tier = team2_player.get('tier', 'default').capitalize()
                            team1_rank = team1_player.get('rank', '')
                            team2_rank = team2_player.get('rank', '')
                            
                            role_display = role_emoji_map.get(role, role.capitalize())
                            role_matchup_text += f"{role_display}: {team1_name} ({team1_tier} {team1_rank}) vs {team2_name} ({team2_tier} {team2_rank})\n"
                    
                    # Instructions for recording match outcome
                    instructions = (
                        f"**Matchmaking - Game {pool_idx + 1} of {game_count}**\n"
                        f"Match ID: `{match_id}`\n"
                        f"Team Performance Difference: {diff:.2f}\n"
                        f"Role Matchup Balance: {role_matchup_percent}%\n\n"
                        f"{role_matchup_text}\n"
                        f"To record match results, use: `/record_match_result {match_id} <winning_team>`\n"
                        f"where <winning_team> is either 1 or 2."
                    )

                    results.append({
                        "match_id": match_id,
                        "pool_idx": pool_idx,
                        "embeds": [team1_embed, team2_embed],
                        "instructions": instructions
                    })

                # Record participation points for excluded players
                if participation_players:
                    participation_id = f"participation_{int(asyncio.get_event_loop().time())}"
                    # Get the next match ID for the participation session
                    from model.dbc_model import Matches
                    matches_db = Matches(db_name=settings.DATABASE_NAME)
                    participation_match_num = matches_db.get_next_match_id()
                    for player in participation_players:
                        user_id = player.get('user_id')
                        if user_id:
                            query = "INSERT INTO Matches(user_id, teamUp, teamId, match_num) VALUES(?, ?, ?, ?)"
                            db.cursor.execute(query, (user_id, "participation", participation_id, participation_match_num))

                # Commit all changes to database
                db.connection.commit()
                db.close_db()

                # Send results for each game
                for result in results:
                    await interaction.followup.send(content=result["instructions"], embeds=result["embeds"])

                # If there were participation players, show them too
                if participation_players:
                    participation_embed = discord.Embed(
                        title="Players Receiving Participation Points",
                        color=discord.Color.green(),
                        description=f"{len(participation_players)} players are sitting out but will receive participation points."
                    )

                    for i, player in enumerate(participation_players):
                        name = player.get('game_name', player.get('user_id', 'Unknown'))
                        tier = player.get('tier', 'Unknown').capitalize()
                        rank = player.get('rank', '')
                        roles = player.get('role', [])
                        
                        # Format roles with colors
                        colored_roles = []
                        for role in roles:
                            role_lower = role.lower()
                            role_emoji = role_colors.get(role_lower, "⬜")
                            colored_roles.append(f"{role_emoji} {role.capitalize()}")
                        
                        role_str = '  '.join(colored_roles) if colored_roles else 'None'

                        participation_embed.add_field(
                            name=f"Player {i + 1}: {name}",
                            value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}",
                            inline=True
                        )

                    await interaction.followup.send(embed=participation_embed)

            except Exception as ex:
                logger.error(f"Error running matchmaking: {ex}")
                await interaction.followup.send(f"Error running matchmaking: {str(ex)}")
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)

async def setup(bot):
    await bot.add_cog(MatchmakingController(bot))