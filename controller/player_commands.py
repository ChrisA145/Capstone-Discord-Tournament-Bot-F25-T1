import discord
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Player

class PlayerDetails(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="playersinfo", description="validating a player")
    async def player(self, interaction: discord.Interaction):
        player_db = Player(db_name=settings.DATABASE_NAME)

        confirm_result = player_db.fetch(interaction)

        # ✅ Handle not found
        if not confirm_result:
            await interaction.response.send_message(
                "❌ You are not registered yet. Use /register first.",
                ephemeral=True
            )
            player_db.close_db()
            return

        # ✅ fetch returns tuple → use index
        user_id = confirm_result[0]

        await interaction.response.send_message(
            f"✅ Your account {user_id} is created"
        )

        player_db.close_db()


async def setup(bot):
    await bot.add_cog(PlayerDetails(bot))