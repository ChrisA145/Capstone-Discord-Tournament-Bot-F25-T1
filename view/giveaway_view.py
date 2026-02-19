import discord
from model.giveaway_model import GiveawayModel


class GiveawayView:
    @staticmethod
    async def send_confirmation_message(ctx, prize, winners):
        """Send the confirmation message with the details."""
        confirm_message = f"Do you want to proceed with the giveaway?\nPrize: {prize}\nNumber of winners: {winners}"
        
        # Create submit and cancel buttons
        submit_button = discord.ui.Button(label="Submit", style=discord.ButtonStyle.green)
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red)

        # Attach the callback functions to the buttons
        submit_button.callback = lambda interaction: GiveawayView.submit_callback(interaction, prize, winners)
        cancel_button.callback = GiveawayView.cancel_callback

        # Create a view and add buttons to it
        view = discord.ui.View()
        view.add_item(submit_button)
        view.add_item(cancel_button)

        await ctx.send(confirm_message, view=view)

    @staticmethod
    async def submit_callback(interaction, prize, winners):
        """Handle the submission of the giveaway."""
        # prize_winners = await interaction.message.embeds[0].description.split("\n")
        winners_list = GiveawayView.pick_winners(interaction.guild, prize, winners)

        if winners_list:
            for winner in winners_list:
                await interaction.response.send_message(f"The winner of the prize {prize} is {winner}.")
        else:
            await interaction.response.send_message(f"Not enough members to select {winners} winners.")

    @staticmethod
    async def cancel_callback(interaction):
        """Handle the cancellation of the giveaway."""
        await interaction.response.send_message("The giveaway was canceled.")

    @staticmethod
    def pick_winners(guild, prize, winners_count):
        """Select winners from the guild members."""
        # Assuming `model` is passed or is part of a larger context
        model = GiveawayModel()  
        filtered_members = model.get_filtered_members(guild)
        winners = model.pick_winners(winners_count)
        return winners