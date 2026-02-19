import discord
import asyncio
from config import settings
from controller.genetic_match_making import GeneticMatchMaking

logger = settings.logging.getLogger("discord")

class TeamSwapView(discord.ui.View):
    def __init__(self, team1_players, team2_players, match_id, timeout=300):
        super().__init__(timeout=timeout)
        self.team1_players = team1_players
        self.team2_players = team2_players
        self.match_id = match_id
        self.selected_player1 = None
        self.selected_player2 = None
        self.message = None
        self.interaction = None
        self.genetic_matchmaker = GeneticMatchMaking()
        
        # Role color mapping (using League of Legends colors)
        self.role_colors = {
            "top": "🟥",      # Red
            "jungle": "🟩",   # Green
            "mid": "🟨",      # Yellow
            "bottom": "🟦",   # Blue
            "support": "🟪",  # Purple
            "tbd": "⬜",      # White/empty
            "forced": "⬛"     # Black/forced
        }
        
        # Add player selection dropdowns
        self._add_player_selects()
        
        # Add action buttons
        self._add_action_buttons()
    
    async def initialize_display(self, interaction):
        """Initialize the view display with team information"""
        self.interaction = interaction
        
        # Calculate team metrics
        team1_perf = self.genetic_matchmaker.team_performance(self.team1_players)
        team2_perf = self.genetic_matchmaker.team_performance(self.team2_players)
        balance_diff = abs(team1_perf - team2_perf)
        
        # Create embeds for teams
        team1_embed, team2_embed = self._create_team_embeds(team1_perf, team2_perf)
        
        # Instructions
        instructions = (
            f"**Team Swap Interface - Match ID: `{self.match_id}`**\n"
            f"Current Team Balance Difference: {balance_diff:.2f}\n\n"
            f"Select one player from each team to swap positions. After swapping, "
            f"team balance will be recalculated."
        )
        
        self.message = await interaction.followup.send(
            content=instructions,
            embeds=[team1_embed, team2_embed],
            view=self
        )
    
    def _create_team_embeds(self, team1_perf=None, team2_perf=None):
        """Create embeds displaying the teams"""
        if team1_perf is None:
            team1_perf = self.genetic_matchmaker.team_performance(self.team1_players)
        if team2_perf is None:
            team2_perf = self.genetic_matchmaker.team_performance(self.team2_players)
        
        # Create team embeds
        team1_embed = discord.Embed(
            title=f"Team 1 - Performance: {team1_perf:.2f}",
            color=discord.Color.blue()
        )
        
        team2_embed = discord.Embed(
            title=f"Team 2 - Performance: {team2_perf:.2f}",
            color=discord.Color.red()
        )
        
        # Add players to embeds
        for i, player in enumerate(self.team1_players):
            name = player.get('game_name', player.get('user_id', 'Unknown'))
            tier = player.get('tier', 'unknown').capitalize()
            rank = player.get('rank', '')
            roles = player.get('role', [])
            
            # Format roles with colors
            colored_roles = []
            for role in roles:
                role_lower = role.lower()
                role_emoji = self.role_colors.get(role_lower, "⬜")
                colored_roles.append(f"{role_emoji} {role.capitalize()}")
            
            role_str = '  '.join(colored_roles) if colored_roles else 'None'
            
            # Special formatting for selected player
            if self.selected_player1 and player.get('user_id') == self.selected_player1.get('user_id'):
                name = f"➡️ {name} ⬅️"  # Add indicator for selection
            
            team1_embed.add_field(
                name=f"Player {i + 1}: {name}",
                value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}",
                inline=True
            )
        
        for i, player in enumerate(self.team2_players):
            name = player.get('game_name', player.get('user_id', 'Unknown'))
            tier = player.get('tier', 'unknown').capitalize()
            rank = player.get('rank', '')
            roles = player.get('role', [])
            
            # Format roles with colors
            colored_roles = []
            for role in roles:
                role_lower = role.lower()
                role_emoji = self.role_colors.get(role_lower, "⬜")
                colored_roles.append(f"{role_emoji} {role.capitalize()}")
            
            role_str = '  '.join(colored_roles) if colored_roles else 'None'
            
            # Special formatting for selected player
            if self.selected_player2 and player.get('user_id') == self.selected_player2.get('user_id'):
                name = f"➡️ {name} ⬅️"  # Add indicator for selection
            
            team2_embed.add_field(
                name=f"Player {i + 1}: {name}",
                value=f"**Rank:** {tier} {rank}\n**Roles:** {role_str}",
                inline=True
            )
        
        return team1_embed, team2_embed
    
    def _add_player_selects(self):
        """Add player selection dropdowns"""
        # Create team 1 select menu
        team1_options = []
        for player in self.team1_players:
            player_name = player.get('game_name', str(player.get('user_id')))
            tier = player.get('tier', 'unknown').capitalize()
            rank = player.get('rank', '')
            
            option = discord.SelectOption(
                label=f"{player_name}",
                description=f"{tier} {rank}",
                value=str(player.get('user_id')),
                default=self.selected_player1 is not None and player.get('user_id') == self.selected_player1.get('user_id')
            )
            team1_options.append(option)
        
        team1_select = discord.ui.Select(
            placeholder="Select a player from Team 1...",
            min_values=1,
            max_values=1,
            options=team1_options,
            row=0,
            custom_id="team1_select"
        )
        team1_select.callback = self.team1_select_callback
        self.add_item(team1_select)
        
        # Create team 2 select menu
        team2_options = []
        for player in self.team2_players:
            player_name = player.get('game_name', str(player.get('user_id')))
            tier = player.get('tier', 'unknown').capitalize()
            rank = player.get('rank', '')
            
            option = discord.SelectOption(
                label=f"{player_name}",
                description=f"{tier} {rank}",
                value=str(player.get('user_id')),
                default=self.selected_player2 is not None and player.get('user_id') == self.selected_player2.get('user_id')
            )
            team2_options.append(option)
        
        team2_select = discord.ui.Select(
            placeholder="Select a player from Team 2...",
            min_values=1,
            max_values=1,
            options=team2_options,
            row=1,
            custom_id="team2_select"
        )
        team2_select.callback = self.team2_select_callback
        self.add_item(team2_select)
    
    def _add_action_buttons(self):
        """Add action buttons"""
        # Swap button
        swap_button = discord.ui.Button(
            label="Swap Players",
            style=discord.ButtonStyle.primary,
            disabled=not (self.selected_player1 and self.selected_player2),
            row=2
        )
        swap_button.callback = self.swap_callback
        self.add_item(swap_button)
        
        # Cancel button
        cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        cancel_button.callback = self.cancel_callback
        self.add_item(cancel_button)
    
    async def team1_select_callback(self, interaction):
        # Get selected player ID from select menu
        selected_id = int(interaction.data['values'][0])
        
        # Update selected player
        self.selected_player1 = next((p for p in self.team1_players if p.get('user_id') == selected_id), None)
        
        # Rebuild the view
        self.clear_items()
        self._add_player_selects()
        self._add_action_buttons()
        
        # Update embeds
        team1_embed, team2_embed = self._create_team_embeds()
        
        # Update the message
        await interaction.response.edit_message(
            embeds=[team1_embed, team2_embed],
            view=self
        )
    
    async def team2_select_callback(self, interaction):
        # Get selected player ID from select menu
        selected_id = int(interaction.data['values'][0])
        
        # Update selected player
        self.selected_player2 = next((p for p in self.team2_players if p.get('user_id') == selected_id), None)
        
        # Rebuild the view
        self.clear_items()
        self._add_player_selects()
        self._add_action_buttons()
        
        # Update embeds
        team1_embed, team2_embed = self._create_team_embeds()
        
        # Update the message
        await interaction.response.edit_message(
            embeds=[team1_embed, team2_embed],
            view=self
        )
    
    async def swap_callback(self, interaction):
        """Swap the selected players"""
        if not self.selected_player1 or not self.selected_player2:
            await interaction.response.send_message(
                "Please select one player from each team first.",
                ephemeral=True
            )
            return
        
        # Import here to avoid circular imports
        from controller.team_swap_controller import TeamSwapController
        
        # Create controller instance
        controller = TeamSwapController(interaction.client)
        
        # Perform the swap in the database
        success = await controller.swap_players(
            self.match_id, 
            self.selected_player1.get('user_id'),
            self.selected_player2.get('user_id')
        )
        
        if success:
            # Swap players in local lists
            self._swap_players_locally()
            
            # Calculate new team performance
            team1_perf = self.genetic_matchmaker.team_performance(self.team1_players)
            team2_perf = self.genetic_matchmaker.team_performance(self.team2_players)
            balance_diff = abs(team1_perf - team2_perf)
            
            # Reset selections
            self.selected_player1 = None
            self.selected_player2 = None
            
            # Create updated embeds
            team1_embed, team2_embed = self._create_team_embeds(team1_perf, team2_perf)
            
            # Update instructions
            instructions = (
                f"**Team Swap Interface - Match ID: `{self.match_id}`**\n"
                f"✅ Players swapped successfully!\n"
                f"New Team Balance Difference: {balance_diff:.2f}\n\n"
                f"Select more players to swap, or click Cancel when done."
            )
            
            # Rebuild the view
            self.clear_items()
            self._add_player_selects()
            self._add_action_buttons()
            
            await interaction.response.edit_message(
                content=instructions,
                embeds=[team1_embed, team2_embed],
                view=self
            )
        else:
            await interaction.response.send_message(
                "Failed to swap players. Please try again or check server logs.",
                ephemeral=True
            )
    
    def _swap_players_locally(self):
        """Swap the selected players in the local team lists"""
        if not self.selected_player1 or not self.selected_player2:
            return
        
        # Find and remove players from their current teams
        self.team1_players = [p for p in self.team1_players if p.get('user_id') != self.selected_player1.get('user_id')]
        self.team2_players = [p for p in self.team2_players if p.get('user_id') != self.selected_player2.get('user_id')]
        
        # Add players to the opposite teams
        self.team1_players.append(self.selected_player2)
        self.team2_players.append(self.selected_player1)
    
    async def cancel_callback(self, interaction):
        """Close the team swap interface"""
        # Disable all controls
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(
            content=f"Team swap interface for Match ID `{self.match_id}` closed.",
            embeds=[],
            view=self
        )
        self.stop()