import discord
from config import settings

logger = settings.logging.getLogger("discord")

class MVPVoteView(discord.ui.View):
    """Discord UI view for MVP voting"""
    def __init__(self, match_id, winning_players, mvp_votes_db, player_db, timeout=300):
        super().__init__(timeout=timeout)
        self.match_id = match_id
        self.winning_players = winning_players
        self.mvp_votes_db = mvp_votes_db
        self.player_db = player_db
        self.message = None
        self.is_closed = False
        self.add_select_menu()
        
    def add_select_menu(self):
        """Add dropdown menu for player selection"""
        # Create select menu for MVP voting
        options = []
        
        for player_id, player_name in self.winning_players:
            option = discord.SelectOption(
                label=player_name,
                value=str(player_id),
                description=f"Vote for {player_name} as MVP"
            )
            options.append(option)
            
        select = discord.ui.Select(
            placeholder="Select the MVP for this match...",
            options=options,
            max_values=1
        )
        
        select.callback = self.select_callback
        self.add_item(select)
        
    async def select_callback(self, interaction):
        """Handle vote selection"""
        # Check if voting is still open
        if self.is_closed:
            await interaction.response.send_message(
                "Voting has ended for this match.",
                ephemeral=True
            )
            return
            
        # Record the vote
        voter_id = interaction.user.id
        player_id = int(interaction.data["values"][0])
        
        # Get player name
        player_name = next((name for id, name in self.winning_players if id == player_id), "Unknown Player")
        
        # Record the vote in the database
        success = self.mvp_votes_db.record_vote(self.match_id, voter_id, player_id)
        
        if success:
            await interaction.response.send_message(
                f"You voted for {player_name} as MVP! Thank you for voting.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Error recording your vote. Please try again.",
                ephemeral=True
            )
            
    async def close_voting(self):
        """Close the voting and disable the UI"""
        self.is_closed = True
        # Disable all items in the view
        for item in self.children:
            item.disabled = True
            
        # Update the message if we have a reference to it
        if self.message:
            try:
                await self.message.edit(
                    content="MVP voting has ended. Results will be announced shortly.",
                    view=self
                )
            except:
                pass
                
        # Stop the view
        self.stop()

def create_mvp_results_embed(match_id, vote_results, db, title="MVP Voting Results", description=None):
    """Create an embed to display MVP voting results
    
    Args:
        match_id: ID of the match
        vote_results: List of (player_id, vote_count) tuples
        db: Database connection
        title: Title for the embed
        description: Optional description for the embed
        
    Returns:
        discord.Embed with formatted results
    """
    if not description:
        description = "Here are the current MVP voting results:"
        
    results_embed = discord.Embed(
        title=f"{title} for Match {match_id}",
        description=description,
        color=discord.Color.blue()
    )
    
    if vote_results:
        winner_id, winner_votes = vote_results[0]
        
        # Get the winner's name
        db.cursor.execute(
            "SELECT game_name FROM player WHERE user_id = ?",
            (winner_id,)
        )
        winner_name_result = db.cursor.fetchone()
        winner_name = winner_name_result[0] if winner_name_result else "Unknown Player"
        
        results_embed.add_field(
            name="🏆 Current MVP Leader 🏆",
            value=f"{winner_name} with {winner_votes} votes!",
            inline=False
        )
        
        # Add all results
        results_text = ""
        for player_id, votes in vote_results:
            db.cursor.execute(
                "SELECT game_name FROM player WHERE user_id = ?",
                (player_id,)
            )
            player_name_result = db.cursor.fetchone()
            player_name = player_name_result[0] if player_name_result else "Unknown Player"
            results_text += f"{player_name}: {votes} votes\n"
        
        results_embed.add_field(
            name="All Votes",
            value=results_text,
            inline=False
        )
    else:
        results_embed.add_field(
            name="No Votes",
            value="No votes have been cast yet.",
            inline=False
        )
        
    return results_embed