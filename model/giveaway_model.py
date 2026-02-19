import random
import discord

class GiveawayModel:
    def __init__(self):
        self.selected_members = []

    def get_filtered_members(self, guild: discord.Guild, role: discord.Role = None):
        """Return members from the guild that are not bots or administrators."""
        if role:
            self.selected_members = [member for member in role.members if not (member.bot or member.guild_permissions.administrator)]
        else:
            self.selected_members = [member for member in guild.members if not (member.bot or member.guild_permissions.administrator)]

        return self.selected_members

    def pick_winners(self, winners_count: int):
        """Randomly pick winners from the filtered members."""
        if len(self.selected_members) < winners_count:
            return []

        winners = random.sample(self.selected_members, winners_count)
        return [winner.display_name for winner in winners]