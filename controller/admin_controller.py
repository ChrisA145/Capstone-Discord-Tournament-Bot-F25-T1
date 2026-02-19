import discord, asyncio
from discord import app_commands
from discord.ext import commands
from config import settings
from model.dbc_model import Tournament_DB, Player, Game

logger = settings.logging.getLogger("discord")


class Admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # This file has been refactored with commands moved to:
    # - checkin_controller.py (checkin_game)
    # - player_management.py (list_players, player_match_history, simulate_checkins)
    # - matchmaking_controller.py (simulate_volunteers, run_matchmaking)
    # - match_results_controller.py (record_match_results, record_match_result)
    # - tier_management.py (view_player_tier, adjust_player_tier, reset_player_tier)


async def setup(bot):
    await bot.add_cog(Admin_commands(bot))