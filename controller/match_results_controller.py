import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Player, Game
from view.match_results_view import (
    MatchResultView, 
    create_mvp_voting_button,
    create_multiple_mvp_voting_buttons
)

logger = settings.logging.getLogger("discord")

class MatchResultsController(commands.Cog):
    """Controller for managing match results"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="record_match_results", description="Record the outcomes of multiple matches")
    async def record_match_results(self, interaction: discord.Interaction):
        """Command to record results for multiple matches at once"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        # Get recent matches that don't have results yet
        db = Tournament_DB()
        try:
            # Look for matches without win/loss recorded
            db.cursor.execute("""
                SELECT DISTINCT teamId, MAX(date_played) 
                FROM Matches 
                WHERE win IS NULL AND loss IS NULL
                GROUP BY teamId
                ORDER BY teamId ASC
                LIMIT 10
            """)

            recent_matches = db.cursor.fetchall()

            if not recent_matches:
                await interaction.response.send_message("No pending matches found to record results for.")
                db.close_db()
                return

            # Prepare match data for the view
            match_results = []

            for i, (match_id, _) in enumerate(recent_matches):
                match_results.append({
                    "match_id": match_id,
                    "pool_idx": i
                })

            # Create view for match results
            view = MatchResultView(match_results)

            # Send initial message
            response = await interaction.response.send_message(
                content=f"Found {len(match_results)} matches needing results.\n"
                        f"Select a match and then click the team that won.",
                view=view
            )

            # Store message reference for later updates
            view.message = await interaction.original_response()

            # Wait for the view to complete
            await view.wait()

            # Process the results
            results_processed = self._process_match_results(db, view.processed_results)

            # Send final confirmation
            if results_processed > 0:
                # Create view with buttons to start MVP voting
                def create_callback(mid):
                    async def callback(inter):
                        await self._start_mvp_voting(inter, mid)
                    return callback
                
                mvp_view = create_multiple_mvp_voting_buttons(
                    view.processed_results.keys(),
                    create_callback
                )
                
                await interaction.followup.send(
                    f"Successfully recorded results for {results_processed} matches and updated player stats. Would you like to start MVP voting?",
                    view=mvp_view
                )

        except Exception as ex:
            logger.error(f"Error recording match results: {ex}")
            await interaction.followup.send(f"Error recording match results: {str(ex)}")
        finally:
            db.close_db()

    @app_commands.command(name="record_match_result", description="Record the outcome of a single match")
    @app_commands.describe(
        match_id="The ID of the match (from run_matchmaking command)",
        winning_team="The number of the winning team (1 or 2)"
    )
    async def record_match_result(self, interaction: discord.Interaction, match_id: str, winning_team: int):
        """Command to record the result of a single match"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        if winning_team not in [1, 2]:
            await interaction.response.send_message("Winning team must be either 1 or 2", ephemeral=True)
            return

        db = Tournament_DB()
        try:
            # Verify the match exists
            db.cursor.execute("SELECT COUNT(*) FROM Matches WHERE teamId = ?", (match_id,))
            count = db.cursor.fetchone()[0]

            if count == 0:
                await interaction.response.send_message(f"Match ID {match_id} not found", ephemeral=True)
                return

            # Process the match result
            results = {match_id: winning_team}
            players_updated = self._process_match_results(db, results)

            # Create callback for MVP voting button
            async def mvp_callback(inter):
                await self._start_mvp_voting(inter, match_id)
                
            # Create view with button to start MVP voting
            mvp_view = create_mvp_voting_button(match_id, mvp_callback)
            
            # Send confirmation
            await interaction.response.send_message(
                f"Match {match_id} result recorded: Team {winning_team} wins!\n"
                f"Updated stats for {players_updated} players.",
                view=mvp_view
            )

        except Exception as ex:
            logger.error(f"Error recording match result: {ex}")
            await interaction.response.send_message(f"Error recording match result: {str(ex)}")
        finally:
            db.close_db()

    def _process_match_results(self, db, match_results):
        """Process match results and update database
        
        Args:
            db: Database connection
            match_results: Dictionary mapping match_id to winning_team
            
        Returns:
            Number of results processed
        """
        results_processed = 0
        players_updated = 0
        
        for match_id, winning_team in match_results.items():
            # Update winners
            winning_team_name = f"team{winning_team}"
            losing_team_name = f"team{3 - winning_team}"  # If winning_team is 1, losing is 2 and vice versa

            # Update winners
            db.cursor.execute(
                "UPDATE Matches SET win = 'yes', loss = 'no' WHERE teamId = ? AND teamUp = ?",
                (match_id, winning_team_name)
            )
            winners_updated = db.cursor.rowcount
            logger.info(f"Updated {winners_updated} winners for match {match_id}, team {winning_team_name}")

            # Update losers
            db.cursor.execute(
                "UPDATE Matches SET win = 'no', loss = 'yes' WHERE teamId = ? AND teamUp = ?",
                (match_id, losing_team_name)
            )
            losers_updated = db.cursor.rowcount
            logger.info(f"Updated {losers_updated} losers for match {match_id}, team {losing_team_name}")
            
            # Update all other players in this match (e.g., volunteers or participation) to mark match as completed
            db.cursor.execute(
                "UPDATE Matches SET win = 'n/a', loss = 'n/a' WHERE teamId = ? AND win IS NULL AND loss IS NULL",
                (match_id,)
            )
            others_updated = db.cursor.rowcount
            logger.info(f"Updated {others_updated} other players for match {match_id} to mark as completed")

            # Get player stats to update
            db.cursor.execute(
                "SELECT user_id, teamUp FROM Matches WHERE teamId = ?",
                (match_id,)
            )
            players = db.cursor.fetchall()

            # Update player stats in the Game table
            for player_id, team in players:
                # Get current player stats
                db.cursor.execute(
                    "SELECT wins, losses FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (player_id,)
                )
                result = db.cursor.fetchone()

                if result:
                    current_wins, current_losses = result

                    # Set default values if None
                    current_wins = current_wins if current_wins is not None else 0
                    current_losses = current_losses if current_losses is not None else 0

                    # Update based on match result
                    if team == winning_team_name:
                        new_wins = current_wins + 1
                        update_query = """
                            UPDATE game SET wins = ?
                            WHERE user_id = ? AND game_date = (
                                SELECT MAX(game_date) FROM game WHERE user_id = ?
                            )
                        """
                        db.cursor.execute(update_query, (new_wins, player_id, player_id))
                    elif team == losing_team_name:  # Exclude participation players
                        new_losses = current_losses + 1
                        update_query = """
                            UPDATE game SET losses = ?
                            WHERE user_id = ? AND game_date = (
                                SELECT MAX(game_date) FROM game WHERE user_id = ?
                            )
                        """
                        db.cursor.execute(update_query, (new_losses, player_id, player_id))
                    
                    players_updated += 1

            # Make sure to commit changes after each match is processed
            db.connection.commit()
            logger.info(f"Committed changes for match {match_id}")

            results_processed += 1

        # Final commit for any remaining changes
        db.connection.commit()
        logger.info(f"Final commit complete, processed {results_processed} matches")
        
        return players_updated

    async def _start_mvp_voting(self, interaction, match_id):
        """Start MVP voting for a match
        
        Args:
            interaction: Discord interaction
            match_id: ID of the match to start voting for
        """
        try:
            mvp_cog = self.bot.get_cog("MVPVotingController")
            if mvp_cog:
                # Access the start_mvp_voting command's callback directly
                cmd = mvp_cog.start_mvp_voting
                # Call the callback with the appropriate context
                await cmd.callback(mvp_cog, interaction, match_id)
            else:
                await interaction.response.send_message(
                    "MVP voting module not available. Please contact an administrator.",
                    ephemeral=True
                )
        except Exception as ex:
            logger.error(f"Error starting MVP voting: {ex}")
            await interaction.response.send_message(
                f"Error starting MVP voting: {str(ex)}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(MatchResultsController(bot))