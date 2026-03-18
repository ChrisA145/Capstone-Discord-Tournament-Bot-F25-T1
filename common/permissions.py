import discord
from discord import app_commands

role1 = "Admin"



def admin():
    async def check(interaction: discord.Interaction):

        for role in interaction.user.roles:
            if role.name == role1:
                return True

        await interaction.response.send_message(
            "You must be an Admin to use this command.",
            ephemeral=True
        )
        return False

    return app_commands.check(check)


