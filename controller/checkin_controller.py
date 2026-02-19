import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from view.checkIn_view import CheckinView
from config import settings
from common.cached_details import Details_Cached

logger = settings.logging.getLogger("discord")

class CheckinController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin_game", description="Start check-in for the next game")
    @app_commands.describe(timeout="Check-in duration in seconds (default: 900 seconds/15 minutes)")
    async def checkin(self, interaction: discord.Interaction, timeout: int = 900):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command", 
                ephemeral=True
            )
            return

        # Defer the response immediately to prevent timeouts
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = interaction.guild.id
            channelName = settings.TOURNAMENT_CH
            logger.info(f"Starting check-in with timeout value: {timeout} seconds")

            # Create the check-in UI first
            game_checkin_view = CheckinView(timeout=timeout)
            
            # Find the channel to send the check-in UI
            target_channel = None
            
            # Try direct search method
            for channel in interaction.guild.channels:
                if channel.name == channelName and isinstance(channel, discord.TextChannel):
                    target_channel = channel
                    logger.info(f"Found target channel directly: {channel.name} with ID {channel.id}")
                    break
            
            # Fallback to cached channel ID
            if target_channel is None:
                channel_id = await Details_Cached.get_channel_id(channelName, guild_id)
                if channel_id:
                    target_channel = interaction.guild.get_channel(channel_id)
                    if target_channel:
                        logger.info(f"Found target channel from cache: {target_channel.name} with ID {target_channel.id}")
            
            # If channel not found, inform user
            if target_channel is None:
                available_channels = ', '.join([ch.name for ch in interaction.guild.channels if isinstance(ch, discord.TextChannel)])
                await interaction.followup.send(
                    f"Could not find channel named '{channelName}'. Available channels: {available_channels}",
                    ephemeral=True
                )
                return
            
            # Send check-in view to the target channel
            try:
                message = await target_channel.send(view=game_checkin_view)
                game_checkin_view.message = message
                game_checkin_view.channel = target_channel
                
                # Confirm to admin that check-in has started
                await interaction.followup.send(
                    f"✅ Check-in started in {target_channel.mention}!\n"
                    f"• Duration: {timeout//60} minutes\n"
                    f"• Check-in will close automatically when the time expires",
                    ephemeral=True
                )
                
                # Schedule deletion after timeout
                await asyncio.sleep(timeout)
                
                try:
                    # Try to delete the message when check-in expires
                    await message.delete()
                    logger.info(f"Check-in message deleted after timeout of {timeout} seconds")
                except discord.NotFound:
                    # Message might have been deleted already
                    logger.info("Check-in message already deleted")
                except Exception as ex:
                    logger.error(f"Error deleting check-in message: {ex}")
                
            except discord.Forbidden:
                await interaction.followup.send(
                    f"Error: Bot doesn't have permission to send messages in {target_channel.mention}",
                    ephemeral=True
                )
            
        except Exception as ex:
            logger.error(f"Error in checkin_game command: {ex}")
            await interaction.followup.send(
                f"An error occurred while setting up check-in: {str(ex)}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(CheckinController(bot))