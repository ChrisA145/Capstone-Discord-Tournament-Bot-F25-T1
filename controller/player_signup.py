import discord
from discord.ext import commands
from discord import app_commands
from controller.signup_shared_logic import SharedLogic

class PlayerSignUp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register", description="register players")
    async def player_signup(self, interaction : discord.Interaction):
        await SharedLogic.execute_signup_model(interaction)

async def setup(bot):
    await bot.add_cog(PlayerSignUp(bot))