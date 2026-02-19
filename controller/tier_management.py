import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Game

logger = settings.logging.getLogger("discord")

class TierManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="view_player_tier", description="View a player's manual tier value")
    @app_commands.describe(player_name="The summoner name of the player to look up")
    async def view_player_tier(self, interaction: discord.Interaction, player_name: str):
        if interaction.user.guild_permissions.administrator:
            db = Tournament_DB()
            game_db = Game(db_name=settings.DATABASE_NAME)
            
            try:
                # Find player ID from name
                db.cursor.execute("SELECT user_id, game_name, tag_id FROM player WHERE game_name LIKE ?", (f"%{player_name}%",))
                player_data = db.cursor.fetchone()

                if not player_data:
                    await interaction.response.send_message(f"Player '{player_name}' not found", ephemeral=True)
                    return

                user_id, game_name, tag_id = player_data
                
                # Get player's tier information
                db.cursor.execute(
                    "SELECT tier, rank, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (user_id,)
                )
                tier_data = db.cursor.fetchone()
                
                if not tier_data:
                    await interaction.response.send_message(f"No tier data found for player '{game_name}'", ephemeral=True)
                    return
                
                tier, rank, manual_tier = tier_data
                
                # If manual tier is None, calculate it now
                if manual_tier is None:
                    if tier and rank:
                        manual_tier = game_db.calculate_manual_tier(tier, rank)
                        game_db.update_manual_tier(user_id, manual_tier)
                    else:
                        manual_tier = 0.0
                
                # Create embed
                embed = discord.Embed(
                    title=f"Player Tier: {game_name}",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="Player ID",
                    value=f"{user_id} (Tag: {tag_id})",
                    inline=False
                )
                
                embed.add_field(
                    name="Rank",
                    value=f"{tier.capitalize() if tier else 'Unranked'} {rank if rank else ''}",
                    inline=True
                )
                
                embed.add_field(
                    name="Manual Tier Value",
                    value=f"{manual_tier} / 10.0",
                    inline=True
                )
                
                # Add information about tier meaning
                tier_info = (
                    "**Tier Scale:** 0-10\n"
                    "0-1: Iron/Bronze\n"
                    "1-3: Bronze/Silver\n"
                    "3-5: Silver/Gold\n"
                    "5-6.5: Gold/Platinum\n"
                    "6.5-8.5: Platinum/Diamond\n"
                    "8.5-10: Master+"
                )
                
                embed.add_field(
                    name="Tier Scale",
                    value=tier_info,
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as ex:
                logger.error(f"Error viewing player tier: {ex}")
                await interaction.response.send_message(f"Error viewing player tier: {str(ex)}")
            finally:
                db.close_db()
                game_db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)
    
    @app_commands.command(name="adjust_player_tier", description="Manually adjust a player's tier value")
    @app_commands.describe(
        player_name="The summoner name of the player to adjust",
        new_tier_value="New manual tier value (0-10)",
        reason="Optional reason for the adjustment"
    )
    async def adjust_player_tier(self, 
                              interaction: discord.Interaction, 
                              player_name: str, 
                              new_tier_value: float,
                              reason: str = None):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)
            db = Tournament_DB()
            game_db = Game(db_name=settings.DATABASE_NAME)
            
            try:
                # Validate input
                if new_tier_value < 0 or new_tier_value > 10:
                    await interaction.followup.send(f"Tier value must be between 0 and 10", ephemeral=True)
                    return
                
                # Find player ID from name
                db.cursor.execute("SELECT user_id, game_name FROM player WHERE game_name LIKE ?", (f"%{player_name}%",))
                player_data = db.cursor.fetchone()

                if not player_data:
                    await interaction.followup.send(f"Player '{player_name}' not found", ephemeral=True)
                    return

                user_id, game_name = player_data
                
                # Get current tier
                db.cursor.execute(
                    "SELECT tier, rank, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (user_id,)
                )
                tier_data = db.cursor.fetchone()
                
                current_manual_tier = None
                if tier_data:
                    tier, rank, current_manual_tier = tier_data
                    
                    # If manual tier is None, calculate it now
                    if current_manual_tier is None and tier and rank:
                        current_manual_tier = game_db.calculate_manual_tier(tier, rank)
                        
                # Update the manual tier
                success = game_db.update_manual_tier(user_id, new_tier_value)
                
                if success:
                    # Create success embed
                    embed = discord.Embed(
                        title=f"Player Tier Adjusted",
                        description=f"Successfully adjusted tier for **{game_name}**",
                        color=discord.Color.green()
                    )
                    
                    if current_manual_tier is not None:
                        embed.add_field(
                            name="Previous Tier Value",
                            value=f"{current_manual_tier} / 10.0",
                            inline=True
                        )
                    
                    embed.add_field(
                        name="New Tier Value",
                        value=f"{new_tier_value} / 10.0",
                        inline=True
                    )
                    
                    if reason:
                        embed.add_field(
                            name="Reason",
                            value=reason,
                            inline=False
                        )
                    
                    embed.set_footer(text=f"Player ID: {user_id} | Adjusted by: {interaction.user.display_name}")
                    
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(
                        f"Failed to update tier for player '{game_name}'. Make sure they have at least one game record.",
                        ephemeral=True
                    )
                
            except Exception as ex:
                logger.error(f"Error adjusting player tier: {ex}")
                await interaction.followup.send(f"Error adjusting player tier: {str(ex)}")
            finally:
                db.close_db()
                game_db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)

    @app_commands.command(name="reset_player_tier", description="Reset a player's manual tier to the default calculated value")
    @app_commands.describe(player_name="The summoner name of the player to reset")
    async def reset_player_tier(self, interaction: discord.Interaction, player_name: str):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(thinking=True)
            db = Tournament_DB()
            game_db = Game(db_name=settings.DATABASE_NAME)
            
            try:
                # Find player ID from name
                db.cursor.execute("SELECT user_id, game_name FROM player WHERE game_name LIKE ?", (f"%{player_name}%",))
                player_data = db.cursor.fetchone()

                if not player_data:
                    await interaction.followup.send(f"Player '{player_name}' not found", ephemeral=True)
                    return

                user_id, game_name = player_data
                
                # Get current tier and rank
                db.cursor.execute(
                    "SELECT tier, rank, manual_tier FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (user_id,)
                )
                tier_data = db.cursor.fetchone()
                
                if not tier_data:
                    await interaction.followup.send(f"No tier data found for player '{game_name}'", ephemeral=True)
                    return
                
                tier, rank, current_manual_tier = tier_data
                
                if not tier or not rank:
                    await interaction.followup.send(
                        f"Cannot reset tier for player '{game_name}'. Missing tier or rank information.", 
                        ephemeral=True
                    )
                    return
                
                # Calculate the default manual tier based on tier and rank
                new_manual_tier = game_db.calculate_manual_tier(tier, rank)
                
                # Update the manual tier
                success = game_db.update_manual_tier(user_id, new_manual_tier)
                
                if success:
                    # Create success embed
                    embed = discord.Embed(
                        title=f"Player Tier Reset",
                        description=f"Successfully reset tier for **{game_name}** to default value",
                        color=discord.Color.green()
                    )
                    
                    if current_manual_tier is not None:
                        embed.add_field(
                            name="Previous Manual Tier",
                            value=f"{current_manual_tier} / 10.0",
                            inline=True
                        )
                    
                    embed.add_field(
                        name="New Default Tier",
                        value=f"{new_manual_tier} / 10.0",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="Based On",
                        value=f"{tier.capitalize()} {rank}",
                        inline=True
                    )
                    
                    embed.set_footer(text=f"Player ID: {user_id} | Reset by: {interaction.user.display_name}")
                    
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(
                        f"Failed to reset tier for player '{game_name}'.",
                        ephemeral=True
                    )
                
            except Exception as ex:
                logger.error(f"Error resetting player tier: {ex}")
                await interaction.followup.send(f"Error resetting player tier: {str(ex)}")
            finally:
                db.close_db()
                game_db.close_db()
        else:
            await interaction.response.send_message("Sorry, you don't have required permission to use this command",
                                                  ephemeral=True)


async def setup(bot):
    await bot.add_cog(TierManagement(bot))