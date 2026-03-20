import discord
import asyncio
import json
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Game, Matches
from view.team_swap_view import TeamSwapView

logger = settings.logging.getLogger("discord")

class TeamSwapController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="swap_team_players", description="Swap players between teams in a match")
    @app_commands.describe(match_id="The ID of the match to swap players in (e.g. match_1)")
    async def swap_team_players(self, interaction: discord.Interaction, match_id: str):
        """
        Admin command to swap players between teams in a match
        """
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)
            
            try:
                # Get match data
                db = Tournament_DB()
                
                # Check if match_id exists
                db.cursor.execute(
                    "SELECT COUNT(*) FROM Matches WHERE teamId = ?",
                    (match_id,)
                )
                match_count = db.cursor.fetchone()[0]
                
                if match_count == 0:
                    await interaction.followup.send(f"Match ID '{match_id}' not found.")
                    db.close_db()
                    return
                
                # Check if match results have been recorded
                db.cursor.execute(
                    "SELECT COUNT(*) FROM Matches WHERE teamId = ? AND win IS NOT NULL",
                    (match_id,)
                )
                result_count = db.cursor.fetchone()[0]
                
                if result_count > 0:
                    await interaction.followup.send(
                        f"Match '{match_id}' already has results recorded. Cannot swap players in completed matches."
                    )
                    db.close_db()
                    return
                
                # Get team 1 players
                db.cursor.execute("""
                    SELECT m.user_id, p.game_name, g.tier, g.rank, g.role, g.manual_tier
                    FROM Matches m
                    JOIN player p ON m.user_id = p.user_id
                    LEFT JOIN (
                        SELECT user_id, tier, rank, role, manual_tier, MAX(game_date) as max_date
                        FROM game
                        GROUP BY user_id
                    ) g ON m.user_id = g.user_id
                    WHERE m.teamId = ? AND m.teamUp = 'team1'
                """, (match_id,))
                
                team1_players = []
                for record in db.cursor.fetchall():
                    user_id, game_name, tier, rank, role_json, manual_tier = record
                    
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
                        'tier': tier.lower() if tier else 'default',
                        'rank': rank if rank else '',
                        'role': roles,
                        'manual_tier': manual_tier
                    }
                    team1_players.append(player)
                
                # Get team 2 players
                db.cursor.execute("""
                    SELECT m.user_id, p.game_name, g.tier, g.rank, g.role, g.manual_tier
                    FROM Matches m
                    JOIN player p ON m.user_id = p.user_id
                    LEFT JOIN (
                        SELECT user_id, tier, rank, role, manual_tier, MAX(game_date) as max_date
                        FROM game
                        GROUP BY user_id
                    ) g ON m.user_id = g.user_id
                    WHERE m.teamId = ? AND m.teamUp = 'team2'
                """, (match_id,))
                
                team2_players = []
                for record in db.cursor.fetchall():
                    user_id, game_name, tier, rank, role_json, manual_tier = record
                    
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
                        'tier': tier.lower() if tier else 'default',
                        'rank': rank if rank else '',
                        'role': roles,
                        'manual_tier': manual_tier
                    }
                    team2_players.append(player)
                
                db.close_db()
                
                if not team1_players or not team2_players:
                    await interaction.followup.send(
                        f"Match '{match_id}' doesn't have two complete teams. Cannot perform swap."
                    )
                    return
                
                # Send team information with swap interface
                view = TeamSwapView(team1_players, team2_players, match_id)
                await view.initialize_display(interaction)
                
            except Exception as ex:
                logger.error(f"Error in swap_team_players: {ex}")
                await interaction.followup.send(f"Error processing team swap: {str(ex)}")
                
        else:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
    
    async def swap_players(self, match_id, player1_id, player2_id):
        """
        Swap two players between teams in the database
        
        Args:
            match_id: The match ID
            player1_id: First player's user ID
            player2_id: Second player's user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Use _db if it exists (for testing), otherwise create a new connection
        if hasattr(self, '_db'):
            db = self._db
        else:
            db = Tournament_DB()
        
        try:
            # Get current team assignments
            db.cursor.execute(
                "SELECT teamUp FROM Matches WHERE teamId = ? AND user_id = ?",
                (match_id, player1_id)
            )
            player1_team = db.cursor.fetchone()
            
            db.cursor.execute(
                "SELECT teamUp FROM Matches WHERE teamId = ? AND user_id = ?",
                (match_id, player2_id)
            )
            player2_team = db.cursor.fetchone()
            
            if not player1_team or not player2_team:
                logger.error(f"Could not find both players in match {match_id}")
                if not hasattr(self, '_db'):  # Only close if we created it
                    db.close_db()
                return False
            
            logger.info(f"Swapping player {player1_id} from {player1_team[0]} with player {player2_id} from {player2_team[0]}")
            
            # Swap teams
            db.cursor.execute(
                "UPDATE Matches SET teamUp = ? WHERE teamId = ? AND user_id = ?",
                (player2_team[0], match_id, player1_id)
            )
            
            db.cursor.execute(
                "UPDATE Matches SET teamUp = ? WHERE teamId = ? AND user_id = ?",
                (player1_team[0], match_id, player2_id)
            )
            
            db.connection.commit()
            
            if not hasattr(self, '_db'):  # Only close if we created it
                db.close_db()
            
            logger.info(f"Successfully swapped players in match {match_id}")
            return True
            
        except Exception as ex:
            logger.error(f"Error swapping players: {ex}")
            if not hasattr(self, '_db'):  # Only close if we created it
                db.close_db()
            return False

async def setup(bot):
    await bot.add_cog(TeamSwapController(bot))