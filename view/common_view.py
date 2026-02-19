import discord
from discord.ui import *
from config import settings
import traceback
import asyncio
import time
from model import dbc_model
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

logger = settings.logging.getLogger("discord")


class RegisterModal(Modal, title="Registration"):
    def __init__(self, timeout: int = 550):
        super().__init__()
        self.timeout = timeout
        self.viewStart_time = time.time()
        self.game_name = TextInput(
            style=discord.TextStyle.long,
            label="Game Name:",
            max_length=500,
            required=True,
            placeholder="Game Name"
        )
        self.add_item(self.game_name)

        self.Tag_id = TextInput(
            style=discord.TextStyle.short,
            label="Your Tag ID",
            required=True,
            placeholder="Tag ID"
        )
        self.add_item(self.Tag_id)

    async def on_submit(self, interaction: discord.Interaction):
        """ this has a summary of checkin submission
            info:
                summary will be send to feedback channel
            Args:
                discord interaction (interaction: discord.Interaction)
        """
        logger.info(f"game name {Fore.RED}{self.game_name.value}{Style.RESET_ALL} and user id is {Fore.RED}{self.Tag_id.value}{Style.RESET_ALL}")
        try:
            db = dbc_model.Tournament_DB()
            dbc_model.Player.register(db, interaction=interaction, gamename=self.game_name.value.strip(),
                                      tagid=self.Tag_id.value.strip())
            db.close_db()
            embed = discord.Embed(title="Checkin Summary",
                                  description=f"Game Name: {self.game_name.value}\nTag ID: {self.Tag_id.value}",
                                  color=discord.Color.yellow())
            embed.set_author(name=self.user)
            await interaction.response.send_message(f"{self.user}, you have completed registration", embed=embed)

        except Exception as ex:
            print(f"it faild on {ex}")

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)
        return await super().on_submit(interaction)


class PreferenceSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Top Lane", value="top"),
            discord.SelectOption(label="Jungle", value="jungle"),
            discord.SelectOption(label="Mid Lane", value="mid"),
            discord.SelectOption(label="Bottom", value="bottom"),
            discord.SelectOption(label="Support", value="support"),
        ]
        super().__init__(options=options, placeholder="Select your preference in order (max 3)", max_values=3)

    async def callback(self, interaction: discord.Interaction):
        await self.view.selected_preferences(interaction, self.values)


class PlayerPrefRole(discord.ui.View):
    selected_pref = None

    def __init__(self, *, timeout=540):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.message = None

        # Add the role preferences dropdown directly without needing an initial selection
        self.add_item(PreferenceSelect())

    async def selected_preferences(self, interaction: discord.Interaction, choices):
        try:
            # Acknowledge the interaction first
            await interaction.response.defer()

            # Save the preferences
            self.selected_pref = choices

            # Update the database
            db = dbc_model.Tournament_DB()
            dbc_model.Game.update_pref(db, interaction, self.selected_pref)
            db.close_db()

            # Create a response embed
            roles_list = ", ".join([role.capitalize() for role in choices])
            embed = discord.Embed(
                title="Role Preferences Saved",
                description=f"Your role preferences have been saved: {roles_list}",
                color=discord.Color.green()
            )

            # Send confirmation as ephemeral message (only visible to the user)
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Delete the original message to clean up the chat
            try:
                # Try to delete using the stored message reference first
                if self.message:
                    await self.message.delete()
                else:
                    # If no stored message, use the interaction's message
                    await interaction.message.delete()
            except Exception as ex:
                logger.error(f"Error deleting message: {ex}")

            self.stop()
        except discord.errors.InteractionResponded:
            # If the interaction was already responded to, just continue with the logic
            logger.info("Interaction was already responded to, continuing with preference update")

            # Update the database
            db = dbc_model.Tournament_DB()
            dbc_model.Game.update_pref(db, interaction, self.selected_pref)
            db.close_db()

            # Try to delete the message
            try:
                if self.message:
                    await self.message.delete()
                else:
                    await interaction.message.delete()
            except Exception as ex:
                logger.error(f"Error deleting message in exception handler: {ex}")

            self.stop()

    # selected_role method removed - we only need role preferences now


class Checkin_RegisterModal(Modal, title="Registration"):
    def __init__(self, timeout: int = 550):
        super().__init__()
        self.timeout = timeout
        self.viewStart_time = time.time()
        self.game_name = TextInput(
            style=discord.TextStyle.long,
            label="game name:",
            max_length=500,
            required=True,
            placeholder="Game Name"
        )
        self.add_item(self.game_name)

        self.Tag_id = TextInput(
            style=discord.TextStyle.short,
            label="your tag id",
            required=True,
            placeholder="Tag ID"
        )
        self.add_item(self.Tag_id)

    async def on_submit(self, interaction: discord.Interaction):
        """ this has a summary of checkin submission
        info:
            summary will be send to feedback channel
        Args:
            discord interaction (interaction: discord.Interaction)
        """
        logger.info(f"game name {Fore.RED}{self.game_name.value}{Style.RESET_ALL} and user id is {Fore.RED}{self.Tag_id.value}{Style.RESET_ALL}")
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
        try:
            db = dbc_model.Tournament_DB()
            dbc_model.Player.register(db, interaction=interaction, gamename=self.game_name.value.strip(),
                                      tagid=self.Tag_id.value.strip())
            db.close_db()
            embed = discord.Embed(title="Checkin Summary",
                                  description=f"Game Name: {self.game_name.value}\n Tag ID:{self.Tag_id.value}",
                                  color=discord.Color.yellow())
            embed.set_author(name=self.user)

            await interaction.response.send_message(f"{self.user}, you have completed registration", ephemeral=True)

            role_pref_view = PlayerPrefRole()
            # await interaction.response.send_message(f"{self.user}, you have completed registration", embed=embed, ephemeral=True)
            message = await interaction.followup.send(view=role_pref_view)

            await asyncio.sleep(self.timeout)
            await message.delete()

        except Exception as ex:
            print(f"it is faild on {ex}")
