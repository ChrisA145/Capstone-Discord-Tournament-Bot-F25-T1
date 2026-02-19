import discord
from discord import app_commands
from discord.ext import commands
from model.dbc_model import Tournament_DB, Player

class PlayerDetails(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="playersinfo", description="validating a player")
    async def player(self, interaction: discord.Interaction):
        db = Tournament_DB()
        confirm_result = Player.fetch(db, interaction)
        await interaction.response.send_message(f"your account {confirm_result.discord_id} is created")
        db.close_db()

async def setup(bot):
    await bot.add_cog(PlayerDetails(bot))