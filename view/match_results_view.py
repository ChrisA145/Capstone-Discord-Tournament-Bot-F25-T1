import discord
import asyncio
from config import settings

logger = settings.logging.getLogger("discord")

class MatchResultView(discord.ui.View):
    """Discord UI view for recording match results"""
    def __init__(self, match_results, timeout=300):
        super().__init__(timeout=timeout)
        self.match_results = match_results
        self.processed_results = {}
        self.message = None

        # Add UI components
        self._add_match_select()
        self._add_team_buttons()

    def _add_match_select(self):
        """Add dropdown for match selection"""
        # Create options for each match
        options = []
        for match_data in self.match_results:
            match_id = match_data['match_id']
            pool_idx = match_data['pool_idx']
            is_processed = match_id in self.processed_results

            option = discord.SelectOption(
                label=f"Match {match_id}",
                description=f"Game #{pool_idx + 1}",
                value=match_id,
                default=False,
                emoji="✅" if is_processed else "⏱️"
            )
            options.append(option)

        # Create select menu
        select = discord.ui.Select(
            placeholder="Select match to record result...",
            options=options
        )

        # Add callback
        select.callback = self.match_select_callback

        # Add to view
        self.add_item(select)

    def _add_team_buttons(self):
        """Add buttons for team selection"""
        # Team 1 button
        team1_button = discord.ui.Button(
            label="Team 1 Wins",
            style=discord.ButtonStyle.success,
            row=1
        )
        team1_button.callback = self.create_team_callback(1)
        self.add_item(team1_button)

        # Team 2 button
        team2_button = discord.ui.Button(
            label="Team 2 Wins",
            style=discord.ButtonStyle.danger,
            row=1
        )
        team2_button.callback = self.create_team_callback(2)
        self.add_item(team2_button)

        # Add "Done" button
        done_button = discord.ui.Button(
            label="Finish Recording",
            style=discord.ButtonStyle.primary,
            row=2
        )
        done_button.callback = self.done_callback
        self.add_item(done_button)

    def create_team_callback(self, team_number):
        """Create callback for team selection buttons"""
        async def callback(interaction):
            # Get the currently selected match
            selected_match_id = None
            for item in self.children:
                if isinstance(item, discord.ui.Select):
                    selected_match_id = item.values[0] if item.values else None

            if not selected_match_id:
                await interaction.response.send_message(
                    "Please select a match first before recording the result.",
                    ephemeral=True
                )
                return

            # Record the result
            self.processed_results[selected_match_id] = team_number

            # Rebuild the view
            self.clear_items()
            self._add_match_select()
            self._add_team_buttons()

            await interaction.response.edit_message(
                content=f"Recording match results...\n"
                        f"Match {selected_match_id}: Team {team_number} wins!\n"
                        f"Recorded results for {len(self.processed_results)}/{len(self.match_results)} matches.",
                view=self
            )

        return callback

    async def match_select_callback(self, interaction):
        """Callback for match selection dropdown"""
        # Just acknowledge - team buttons will be used for actual action
        await interaction.response.defer()

    async def done_callback(self, interaction):
        """Callback for the 'Finish Recording' button"""
        # If we have all results, or admin wants to finish early
        missing_matches = len(self.match_results) - len(self.processed_results)

        if missing_matches > 0:
            # Ask for confirmation if not all matches recorded
            confirm_content = f"You have {missing_matches} unrecorded match results. Are you sure you want to finish?"
            confirm_view = ConfirmFinishView(self)

            await interaction.response.send_message(
                content=confirm_content,
                view=confirm_view,
                ephemeral=True
            )
        else:
            # All matches recorded, finish up
            self.stop()
            await interaction.response.edit_message(
                content=f"All {len(self.match_results)} match results recorded successfully!",
                view=None
            )


class ConfirmFinishView(discord.ui.View):
    """Confirmation view for finishing early"""
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label="Yes, finish recording", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        self.parent_view.stop()
        await interaction.response.edit_message(
            content="Recording finished.",
            view=None
        )
        await interaction.followup.edit_message(
            message_id=self.parent_view.message.id,
            content=f"Match recording completed. {len(self.parent_view.processed_results)}/{len(self.parent_view.match_results)} matches recorded.",
            view=None
        )

    @discord.ui.button(label="No, continue recording", style=discord.ButtonStyle.success)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="Continuing with result recording...",
            view=None
        )


def create_mvp_voting_button(match_id, callback):
    """Create a button for starting MVP voting"""
    view = discord.ui.View(timeout=300)
    button = discord.ui.Button(
        label="Start MVP Voting",
        style=discord.ButtonStyle.primary,
        custom_id=f"mvp_vote_{match_id}"
    )
    button.callback = callback
    view.add_item(button)
    return view

def create_multiple_mvp_voting_buttons(match_ids, callback_factory):
    """Create buttons for each match for MVP voting"""
    view = discord.ui.View(timeout=300)
    for match_id in match_ids:
        button = discord.ui.Button(
            label=f"Start MVP Voting for Match {match_id}",
            style=discord.ButtonStyle.primary,
            custom_id=f"mvp_vote_{match_id}"
        )
        button.callback = callback_factory(match_id)
        view.add_item(button)
    return view