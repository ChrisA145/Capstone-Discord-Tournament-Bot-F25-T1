import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Player, Game, MVP_Votes
from view.mvp_vote_view import MVPVoteView, create_mvp_results_embed

logger = settings.logging.getLogger("discord")

class MVPVotingController(commands.Cog):
    """Controller for managing MVP voting"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Tournament_DB()
        self.mvp_votes_db = MVP_Votes(db_name=settings.DATABASE_NAME)
        self.player_db = Player(db_name=settings.DATABASE_NAME)
        self.active_voting_sessions = {}
    
    @app_commands.command(name="start_mvp_voting", description="Start MVP voting for a match")
    @app_commands.describe(match_id="The ID of the completed match to vote for")
    async def start_mvp_voting(self, interaction: discord.Interaction, match_id: str):
        """Start MVP voting for a completed match"""
        # Check if the user is an admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to start MVP voting.",
                ephemeral=True
            )
            return
            
        try:
            # Check if the match exists and has a winner
            winning_team = self._get_winning_team(match_id)
            
            if not winning_team:
                await interaction.response.send_message(
                    f"Match {match_id} either doesn't exist or doesn't have a winning team recorded yet.",
                    ephemeral=True
                )
                return
                
            # Get the players from the winning team
            winning_players = self._get_winning_players(match_id, winning_team)
            
            if not winning_players:
                await interaction.response.send_message(
                    f"No players found for the winning team in match {match_id}.",
                    ephemeral=True
                )
                return
                
            # Create voting message
            embed = discord.Embed(
                title=f"MVP Voting for Match {match_id}",
                description="Vote for the Most Valuable Player from the winning team!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="Winning Team",
                value=winning_team,
                inline=False
            )
            
            player_list = "\n".join([f"• {name}" for _, name in winning_players])
            embed.add_field(
                name="Players",
                value=player_list,
                inline=False
            )
            
            embed.set_footer(text="Click on the dropdown below to vote. You can only vote once.")
            
            # Check if there's already an active voting session for this match
            if match_id in self.active_voting_sessions:
                await interaction.response.send_message(
                    f"Voting is already in progress for match {match_id}.",
                    ephemeral=True
                )
                return
                
            # Create voting view
            view = MVPVoteView(match_id, winning_players, self.mvp_votes_db, self.player_db)
            
            # Send the voting message
            await interaction.response.send_message(
                content="MVP Voting has started! Please select your MVP from the dropdown below:",
                embed=embed,
                view=view
            )
            
            # Store the message reference for later updates
            view.message = await interaction.original_response()
            
            # Add to active voting sessions
            self.active_voting_sessions[match_id] = view
            
            # Set a reminder to close voting after 5 minutes
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                # Remove from active sessions if still there
                if match_id in self.active_voting_sessions:
                    self.active_voting_sessions.pop(match_id, None)
                
                # Check if voting is still active
                if not view.is_finished():
                    # Get vote counts from database
                    vote_results = self.mvp_votes_db.get_vote_count(match_id)
                    
                    # Finalize MVP and update their count
                    mvp_result = self.mvp_votes_db.finalize_mvp_voting(match_id)
                
                if mvp_result:
                    winner_id, winner_name, new_mvp_count, vote_count = mvp_result
                    
                    # Create results embed
                    results_embed = create_mvp_results_embed(
                        match_id, 
                        vote_results, 
                        self.db,
                        title="MVP Voting Results",
                        description="The voting has concluded! Here are the results:"
                    )
                    
                    # Get total number of votes
                    self.db.cursor.execute(
                        "SELECT COUNT(*) FROM MVP_Votes WHERE match_id = ?",
                        (match_id,)
                    )
                    total_votes = self.db.cursor.fetchone()[0]
                    
                    # Add MVP accolade information
                    results_embed.add_field(
                        name="🏆 MVP Achievement 🏆",
                        value=f"{winner_name} has now been MVP {new_mvp_count} time{'s' if new_mvp_count != 1 else ''}!",
                        inline=False
                    )
                    
                    results_embed.set_footer(text=f"Total votes: {total_votes}")
                    
                    # Send results and disable the voting view
                    await interaction.followup.send(
                        content=f"MVP voting has ended! Congratulations to {winner_name} for being the MVP!",
                        embed=results_embed
                    )
                else:
                    # Create basic results embed without MVP accolade
                    results_embed = create_mvp_results_embed(
                        match_id, 
                        vote_results, 
                        self.db,
                        title="MVP Voting Results",
                        description="The voting has concluded! Here are the results:"
                    )
                    
                    # Get total number of votes
                    self.db.cursor.execute(
                        "SELECT COUNT(*) FROM MVP_Votes WHERE match_id = ?",
                        (match_id,)
                    )
                    total_votes = self.db.cursor.fetchone()[0]
                    
                    results_embed.set_footer(text=f"Total votes: {total_votes}")
                    
                    # Send results and disable the voting view
                    await interaction.followup.send(
                        content="MVP voting has ended!",
                        embed=results_embed
                    )
                
                # Try to disable the view
                try:
                    view.stop()
                    await interaction.edit_original_response(view=None)
                except:
                    pass
            except asyncio.CancelledError:
                # Voting was ended early, handled in end_mvp_voting
                pass
            except Exception as ex:
                logger.error(f"Error in voting timer: {ex}")
                
        except Exception as ex:
            logger.error(f"Error starting MVP voting: {ex}")
            await interaction.followup.send(f"Error starting MVP voting: {str(ex)}")
    
    @app_commands.command(name="end_mvp_voting", description="End MVP voting early for a match")
    @app_commands.describe(match_id="The ID of the match to end voting for")
    async def end_mvp_voting(self, interaction: discord.Interaction, match_id: str):
        """End MVP voting early for a match"""
        # Check if the user is an admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to end MVP voting.",
                ephemeral=True
            )
            return
            
        try:
            # Check if there's an active voting session for this match
            if match_id not in self.active_voting_sessions:
                await interaction.response.send_message(
                    f"No active voting session found for match {match_id}.",
                    ephemeral=True
                )
                return
                
            # Get the voting view
            view = self.active_voting_sessions[match_id]
            
            # Close the voting UI
            await view.close_voting()
            
            # Get vote counts from database
            vote_results = self.mvp_votes_db.get_vote_count(match_id)
            
            # Finalize MVP and update their count
            mvp_result = self.mvp_votes_db.finalize_mvp_voting(match_id)
            
            # Remove from active sessions
            self.active_voting_sessions.pop(match_id, None)
            
            if mvp_result:
                winner_id, winner_name, new_mvp_count, vote_count = mvp_result
                
                # Create results embed
                results_embed = create_mvp_results_embed(
                    match_id, 
                    vote_results, 
                    self.db,
                    title="MVP Voting Results",
                    description=f"Voting ended early by admin. Here are the results:"
                )
                
                # Get total number of votes
                self.db.cursor.execute(
                    "SELECT COUNT(*) FROM MVP_Votes WHERE match_id = ?",
                    (match_id,)
                )
                total_votes = self.db.cursor.fetchone()[0]
                
                # Add MVP accolade information
                results_embed.add_field(
                    name="🏆 MVP Achievement 🏆",
                    value=f"{winner_name} has now been MVP {new_mvp_count} time{'s' if new_mvp_count != 1 else ''}!",
                    inline=False
                )
                
                results_embed.set_footer(text=f"Total votes: {total_votes} • Voting ended early by admin")
                
                # Send results
                await interaction.response.send_message(
                    content=f"MVP voting has ended early! Congratulations to {winner_name} for being the MVP!",
                    embed=results_embed
                )
            else:
                # No votes or something went wrong
                await interaction.response.send_message(
                    "MVP voting has ended, but there were no valid results to display.",
                    ephemeral=True
                )
                
        except Exception as ex:
            logger.error(f"Error ending MVP voting: {ex}")
            await interaction.response.send_message(f"Error ending MVP voting: {str(ex)}", ephemeral=True)
    
    @app_commands.command(name="vote_mvp", description="Vote for the MVP of a match")
    @app_commands.describe(
        match_id="The ID of the match to vote for",
        player_name="The name of the player to vote for"
    )
    async def vote_mvp(self, interaction: discord.Interaction, match_id: str, player_name: str):
        """Vote for the MVP of a match"""
        voter_id = interaction.user.id
        
        try:
            # Check if the match exists and has a winner
            winning_team = self._get_winning_team(match_id)
            
            if not winning_team:
                await interaction.response.send_message(
                    f"Match {match_id} either doesn't exist or doesn't have a winning team recorded yet.",
                    ephemeral=True
                )
                return
                
            # Check if user has already voted
            if self.mvp_votes_db.has_voted(match_id, voter_id):
                await interaction.response.send_message(
                    "You have already voted for this match. Each player can only vote once.",
                    ephemeral=True
                )
                return
                
            # Find the player by name
            player_matches = self._find_player_by_name(match_id, winning_team, player_name)
            
            if not player_matches:
                await interaction.response.send_message(
                    f"No player found with name '{player_name}' on the winning team.",
                    ephemeral=True
                )
                return
                
            if len(player_matches) > 1:
                # Multiple matches, let user select the correct one
                player_list = "\n".join([f"• {name}" for _, name in player_matches])
                await interaction.response.send_message(
                    f"Multiple players match '{player_name}'. Please be more specific:\n{player_list}",
                    ephemeral=True
                )
                return
                
            # We have a single player match
            player_id, full_player_name = player_matches[0]
            
            # Record the vote
            success = self.mvp_votes_db.record_vote(match_id, voter_id, player_id)
            
            if success:
                await interaction.response.send_message(
                    f"You voted for {full_player_name} as MVP for match {match_id}!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Error recording your vote. Please try again.",
                    ephemeral=True
                )
                
        except Exception as ex:
            logger.error(f"Error voting for MVP: {ex}")
            await interaction.response.send_message(f"Error voting for MVP: {str(ex)}", ephemeral=True)
    
    @app_commands.command(name="view_mvp_results", description="View the MVP results for a match")
    @app_commands.describe(match_id="The ID of the match to view MVP results for")
    async def view_mvp_results(self, interaction: discord.Interaction, match_id: str):
        """View the MVP voting results for a match"""
        try:
            # Get vote results
            vote_results = self.mvp_votes_db.get_vote_count(match_id)
            
            if not vote_results:
                await interaction.response.send_message(
                    f"No MVP votes found for match {match_id}.",
                    ephemeral=True
                )
                return
                
            # Create results embed
            results_embed = create_mvp_results_embed(match_id, vote_results, self.db)
            
            # Get total number of votes
            self.db.cursor.execute(
                "SELECT COUNT(*) FROM MVP_Votes WHERE match_id = ?",
                (match_id,)
            )
            total_votes = self.db.cursor.fetchone()[0]
            
            # Get winner and their MVP count
            winner_id = vote_results[0][0] if vote_results else None
            if winner_id:
                player_db = Player(db_name=settings.DATABASE_NAME)
                mvp_count = player_db.get_mvp_count(winner_id)
                
                # Get player name
                self.db.cursor.execute(
                    "SELECT game_name FROM player WHERE user_id = ?",
                    (winner_id,)
                )
                name_result = self.db.cursor.fetchone()
                winner_name = name_result[0] if name_result else "Unknown Player"
                
                # Add MVP count information
                results_embed.add_field(
                    name="MVP History",
                    value=f"{winner_name} has been MVP {mvp_count} time{'s' if mvp_count != 1 else ''}!",
                    inline=False
                )
            
            results_embed.set_footer(text=f"Total votes: {total_votes}")
            
            # Send results
            await interaction.response.send_message(
                embed=results_embed
            )
                
        except Exception as ex:
            logger.error(f"Error viewing MVP results: {ex}")
            await interaction.response.send_message(f"Error viewing MVP results: {str(ex)}", ephemeral=True)
            
    @app_commands.command(name="list_active_mvp_votes", description="List all active MVP voting sessions")
    async def list_active_mvp_votes(self, interaction: discord.Interaction):
        """List all active MVP voting sessions"""
        # Check if the user is an admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to list active MVP voting sessions.",
                ephemeral=True
            )
            return
            
        try:
            if not self.active_voting_sessions:
                await interaction.response.send_message(
                    "There are no active MVP voting sessions.",
                    ephemeral=True
                )
                return
                
            # Create an embed to display active sessions
            embed = discord.Embed(
                title="Active MVP Voting Sessions",
                description="Here are all the currently active MVP voting sessions:",
                color=discord.Color.blue()
            )
            
            for match_id, view in self.active_voting_sessions.items():
                # Get vote counts so far
                vote_results = self.mvp_votes_db.get_vote_count(match_id)
                total_votes = len(vote_results) if vote_results else 0
                
                # Add field for each match
                embed.add_field(
                    name=f"Match: {match_id}",
                    value=f"Total votes: {total_votes}\nUse `/end_mvp_voting {match_id}` to end voting",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
                
        except Exception as ex:
            logger.error(f"Error listing MVP voting sessions: {ex}")
            await interaction.response.send_message(f"Error listing MVP voting sessions: {str(ex)}", ephemeral=True)
    
    @app_commands.command(name="view_player_mvps", description="View how many times a player has been MVP")
    @app_commands.describe(player_name="The name of the player to check")
    async def view_player_mvps(self, interaction: discord.Interaction, player_name: str):
        """View how many times a player has been MVP"""
        try:
            # Find the player by name
            self.db.cursor.execute(
                "SELECT user_id, game_name, mvp_count FROM player WHERE game_name LIKE ?",
                (f"%{player_name}%",)
            )
            player_matches = self.db.cursor.fetchall()
            
            if not player_matches:
                await interaction.response.send_message(
                    f"No player found with name '{player_name}'.",
                    ephemeral=True
                )
                return
                
            if len(player_matches) > 1:
                # Multiple matches, show list of players
                embed = discord.Embed(
                    title="Multiple Players Found",
                    description=f"Found multiple players matching '{player_name}'. Here are their MVP counts:",
                    color=discord.Color.blue()
                )
                
                for player_id, name, mvp_count in player_matches:
                    embed.add_field(
                        name=name,
                        value=f"MVP Count: {mvp_count}",
                        inline=True
                    )
                
                await interaction.response.send_message(embed=embed)
                return
                
            # We have a single player match
            player_id, full_player_name, mvp_count = player_matches[0]
            
            # Create player stats embed
            embed = discord.Embed(
                title=f"MVP Stats for {full_player_name}",
                color=discord.Color.gold()
            )
            
            # Add MVP count information
            embed.add_field(
                name="🏆 MVP History 🏆",
                value=f"{full_player_name} has been MVP {mvp_count} time{'s' if mvp_count != 1 else ''}!",
                inline=False
            )
            
            # Get additional player stats if available
            self.db.cursor.execute(
                "SELECT tier, rank, wins, losses FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                (player_id,)
            )
            stats_result = self.db.cursor.fetchone()
            
            if stats_result:
                tier, rank, wins, losses = stats_result
                
                if tier and rank:
                    embed.add_field(
                        name="Rank",
                        value=f"{tier.capitalize()} {rank}",
                        inline=True
                    )
                
                if wins is not None and losses is not None:
                    total_games = wins + losses
                    win_rate = (wins / total_games * 100) if total_games > 0 else 0
                    
                    embed.add_field(
                        name="Record",
                        value=f"{wins}W - {losses}L ({win_rate:.1f}% WR)",
                        inline=True
                    )
            
            await interaction.response.send_message(embed=embed)
                
        except Exception as ex:
            logger.error(f"Error viewing player MVPs: {ex}")
            await interaction.response.send_message(f"Error viewing player MVPs: {str(ex)}", ephemeral=True)
            
    def _get_winning_team(self, match_id):
        """Get the winning team for a match
        
        Args:
            match_id: The match ID to check
            
        Returns:
            The winning team name or None if match doesn't exist or has no winner
        """
        try:
            self.db.cursor.execute(
                "SELECT COUNT(*) FROM Matches WHERE teamId = ? AND win = 'yes'",
                (match_id,)
            )
            winner_count = self.db.cursor.fetchone()[0]
            
            if winner_count == 0:
                return None
                
            # Get the winning team
            self.db.cursor.execute(
                "SELECT teamUp FROM Matches WHERE teamId = ? AND win = 'yes' LIMIT 1",
                (match_id,)
            )
            winning_team = self.db.cursor.fetchone()[0]
            
            return winning_team
        except Exception as ex:
            logger.error(f"Error getting winning team: {ex}")
            return None
            
    def _get_winning_players(self, match_id, winning_team):
        """Get players from the winning team
        
        Args:
            match_id: The match ID
            winning_team: The winning team name
            
        Returns:
            List of (player_id, player_name) tuples
        """
        try:
            self.db.cursor.execute(
                """
                SELECT m.user_id, p.game_name 
                FROM Matches m 
                JOIN player p ON m.user_id = p.user_id 
                WHERE m.teamId = ? AND m.teamUp = ?
                """,
                (match_id, winning_team)
            )
            return self.db.cursor.fetchall()
        except Exception as ex:
            logger.error(f"Error getting winning players: {ex}")
            return []
            
    def _find_player_by_name(self, match_id, winning_team, player_name):
        """Find players by name on the winning team
        
        Args:
            match_id: The match ID
            winning_team: The winning team name
            player_name: Name to search for
            
        Returns:
            List of matching (player_id, player_name) tuples
        """
        try:
            self.db.cursor.execute(
                """
                SELECT p.user_id, p.game_name 
                FROM player p 
                JOIN Matches m ON p.user_id = m.user_id 
                WHERE m.teamId = ? AND m.teamUp = ? AND p.game_name LIKE ?
                """,
                (match_id, winning_team, f"%{player_name}%")
            )
            return self.db.cursor.fetchall()
        except Exception as ex:
            logger.error(f"Error finding player by name: {ex}")
            return []


async def setup(bot):
    await bot.add_cog(MVPVotingController(bot))