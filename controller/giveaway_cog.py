import discord
from discord.ext import commands
import random
from model.giveaway_model import GiveawayModel
from view.giveaway_view import GiveawayView

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = GiveawayModel()
        self.view = GiveawayView()

    @commands.command()
    async def giveaway(self, ctx, *, prize_winners: str, role: discord.Role = None):
        try:
            if len(prize_winners.strip()):
                # Parse the prize and number of winners
                if "," in prize_winners:
                    prize, winners = prize_winners.split(",", 1)
                    prize = prize.strip()
                    winners = int(winners.strip())
                else:
                    prize = prize_winners.strip()
                    winners = 2

                # Send the confirmation message with buttons
                await self.view.send_confirmation_message(ctx, prize, winners)

        except ValueError:
            await ctx.send("Please provide both details (prize and number of winners).")
        except Exception as e:
            await ctx.send(f"We encountered an error: {e}")

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(Giveaway(bot))