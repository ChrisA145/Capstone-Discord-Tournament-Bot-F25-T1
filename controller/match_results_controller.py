import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from view.bracket_image import create_bracket_image
from common.bracket_helper import resolve_bracket_team
from config import settings
from model.dbc_model import Tournament_DB, Player, Game
from view.match_results_view import (
    MatchResultView, 
    create_mvp_voting_button,
    create_multiple_mvp_voting_buttons
)


logger = settings.logging.getLogger("discord")

class BracketResultView(discord.ui.View):
    """
    Interactive bracket result recording view.
    Shows buttons for each semifinal, then winner selection,
    then auto-posts updated bracket image.
    """
 
    def __init__(self, bot, bracket_id: str, matches: list[str], bracket_id_for_image: str):
        """
        Args:
            bot: the Discord bot instance (needed to call _process_match_results etc.)
            bracket_id: e.g. "bracket_match_1_match_2"
            matches: [semi1_code, semi2_code, final_code]
            bracket_id_for_image: same as bracket_id, used for show_bracket
        """
        super().__init__(timeout=3600)  # 1 hour timeout
        self.bot = bot
        self.bracket_id = bracket_id
        self.matches = matches  # [semi1, semi2, final]
        self.bracket_id_for_image = bracket_id_for_image
        self.recorded = set()  # track which match codes have been recorded
        self.message = None  # will hold the original message reference after sending

        self._build_buttons()
 
    def _build_buttons(self):
        self.clear_items()

        # Check DB for actual recorded status — don't rely on in-memory set
        db = Tournament_DB()
        try:
            completed = set()
            for mc in self.matches:
                db.cursor.execute(
                    "SELECT status FROM BracketMatches WHERE match_code = ?",
                    (mc,)
                )
                row = db.cursor.fetchone()
                if row and row[0] == "completed":
                    completed.add(mc)
        finally:
            db.close_db()

        # Sync in-memory recorded set with DB
        self.recorded = completed

        labels = ["🥊 Semifinal 1", "🥊 Semifinal 2", "🏆 Final"]
        both_semis_done = all(self.matches[j] in completed for j in range(2))

        for i, match_code in enumerate(self.matches):
            is_final = i == 2
            already_done = match_code in completed
            disabled = (is_final and not both_semis_done) or already_done

            label = labels[i]
            if already_done:
                label += " ✅"

            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.success if already_done
                    else discord.ButtonStyle.primary,
                custom_id=f"bracket_pick_{match_code}",
                disabled=disabled,
                row=0
            )
            btn.callback = self._make_pick_callback(match_code, i)
            self.add_item(btn)
 
    def _make_pick_callback(self, match_code: str, match_idx: int):
        """Returns a callback that shows the winner selection for this match."""
        async def callback(interaction: discord.Interaction):
            # Admin check
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Only admins can record bracket results.", ephemeral=True
                )
                return
 
            if match_code in self.recorded:
                await interaction.response.send_message(
                    f"❌ Result for `{match_code}` already recorded.", ephemeral=True
                )
                return
 
            # Fetch team names for this bracket match
            db = Tournament_DB()
            try:
                db.cursor.execute(
                    "SELECT teamA_id, teamB_id FROM BracketMatches WHERE match_code = ?",
                    (match_code,)
                )
                row = db.cursor.fetchone()
                team_a = row[0] if row else "Team 1"
                team_b = row[1] if row else "Team 2"
            finally:
                db.close_db()
 
            # Show winner selection as ephemeral message
            winner_view = BracketWinnerView(
                bot=self.bot,
                parent_view=self,
                match_code=match_code,
                team_a=team_a,
                team_b=team_b,
                bracket_id=self.bracket_id,
            )
 
            round_labels = ["Semifinal 1", "Semifinal 2", "Final"]
            await interaction.response.send_message(
                f"**{round_labels[match_idx]}** (`{match_code}`)\nWho won?",
                view=winner_view,
                ephemeral=True
            )
 
        return callback
 
    async def refresh(self, interaction: discord.Interaction):
        """Rebuild buttons and edit the original message."""
        self._build_buttons()
        try:
            if self.message:
                await self.message.edit(
                    content=self._status_text(),
                    view=self
                )
            else: await interaction.message.edit(
                content=self._status_text(),
                view=self
            )

        except Exception as e:
            logger.error(f"BracketResultView.refresh failed: {e}")
 
    def _status_text(self) -> str:
        lines = [f"📋 **Bracket `{self.bracket_id}`** — Record Results:"]
        labels = ["Semifinal 1", "Semifinal 2", "Final"]
        for i, mc in enumerate(self.matches):
            status = "✅ Done" if mc in self.recorded else "⏳ Pending"
            lines.append(f"{labels[i]}: `{mc}` — {status}")
        return "\n".join(lines)
 
 
class BracketWinnerView(discord.ui.View):
    """Ephemeral view shown after clicking a semifinal/final button."""
 
    def __init__(self, bot, parent_view: BracketResultView,
                 match_code: str, team_a: str, team_b: str, bracket_id: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.parent_view = parent_view
        self.match_code = match_code
        self.team_a = team_a
        self.team_b = team_b
        self.bracket_id = bracket_id
 
        # Team A wins
        btn_a = discord.ui.Button(
            label=f"✅ {team_a} Wins",
            style=discord.ButtonStyle.primary,
            custom_id=f"winner_a_{match_code}"
        )
        btn_a.callback = self._make_winner_callback(winning_team=1)
        self.add_item(btn_a)
 
        # Team B wins
        btn_b = discord.ui.Button(
            label=f"✅ {team_b} Wins",
            style=discord.ButtonStyle.danger,
            custom_id=f"winner_b_{match_code}"
        )
        btn_b.callback = self._make_winner_callback(winning_team=2)
        self.add_item(btn_b)
 
    def _make_winner_callback(self, winning_team: int):
        async def callback(interaction: discord.Interaction):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Only admins can record results.", ephemeral=True
                )
                return
 
            await interaction.response.defer(ephemeral=True)
 
            # Get the MatchResultsController to reuse existing logic
            results_cog = self.bot.get_cog("MatchResultsController")
            if not results_cog:
                await interaction.followup.send(
                    "❌ MatchResultsController not loaded.", ephemeral=True
                )
                return
 
            db = Tournament_DB()
            try:
                # Populate bracket match with players first (if not already done)
                results_cog._populate_bracket_match(db, self.match_code)

                # Now process results normally — players exist in Matches table
                results = {self.match_code: winning_team}
                results_cog._process_match_results(db, results)

                bracket_result = results_cog._advance_bracket_after_result(
                    db, self.match_code, winning_team
                )

                await results_cog._sync_match_to_sheets(db, self.match_code)

                self.parent_view.recorded.add(self.match_code)

            finally:
                db.close_db()

            # Confirm to the admin (ephemeral)
            winner_label = f"Team A (`{self.team_a}`)" if winning_team == 1 else f"Team B (`{self.team_b}`)"
            await interaction.followup.send(
                f"✅ Result recorded for `{self.match_code}` — {winner_label} wins!",
                ephemeral=True
            )
 
            # Refresh parent button panel
            await self.parent_view.refresh(interaction)
 
            # Auto-post updated bracket image (public)
            def generate():
                thread_db = Tournament_DB()
                try:
                    from view.bracket_image import create_bracket_image
                    return create_bracket_image(self.bracket_id, thread_db)
                finally:
                    thread_db.close_db()
 
            try:
                import asyncio
                img_path = await asyncio.to_thread(generate)
 
                # Check if tournament is complete
                db2 = Tournament_DB()
                try:
                    db2.cursor.execute(
                        "SELECT status FROM Brackets WHERE bracket_id = ?",
                        (self.bracket_id,)
                    )
                    row = db2.cursor.fetchone()
                    status = row[0] if row else "active"
                finally:
                    db2.close_db()
 
                status_emoji = "🏆" if status == "complete" else "🟢"
                embed = discord.Embed(
                    title=f"📊 Bracket Update — {self.bracket_id}",
                    description=f"{status_emoji} Status: **{status.upper()}**",
                    color=discord.Color.gold() if status == "complete"
                          else discord.Color.blue(),
                )
                import discord as _discord
                file = _discord.File(img_path, filename=f"bracket_{self.bracket_id}.png")
                embed.set_image(url=f"attachment://bracket_{self.bracket_id}.png")
 
                # Post publicly in the same channel
                await interaction.channel.send(embed=embed, file=file)
 
                # Tournament complete announcement
                if bracket_result and bracket_result.get("completed_bracket"):
                    from common.bracket_helper import resolve_bracket_team
                    from view.winners_image import create_winners_image
 
                    winner_team_id = bracket_result["advanced_team_id"]
 
                    # Resolve player mentions
                    db3 = Tournament_DB()
                    try:
                        winner_players = resolve_bracket_team(db3, winner_team_id)
                        mentions = " ".join(f"<@{p['user_id']}>" for p in winner_players)
                    finally:
                        db3.close_db()
 
                    # Generate winners image in thread (Pillow is blocking)
                    def generate_winners():
                        thread_db = Tournament_DB()
                        try:
                            return create_winners_image(
                                bracket_id=self.bracket_id,
                                winner_team_id=winner_team_id,
                                db=thread_db,
                            )
                        finally:
                            thread_db.close_db()
 
                    try:
                        winners_img_path = await asyncio.to_thread(generate_winners)
 
                        winners_embed = discord.Embed(
                            title="🏆 Tournament Champions!",
                            description=f"Congratulations to: {mentions}",
                            color=discord.Color.gold(),
                        )
                        winners_file = discord.File(
                            winners_img_path,
                            filename=f"winners_{self.bracket_id}.png"
                        )
                        winners_embed.set_image(
                            url=f"attachment://winners_{self.bracket_id}.png"
                        )
 
                        await interaction.channel.send(
                            embed=winners_embed,
                            file=winners_file
                        )
 
                    except Exception as win_ex:
                        logger.error(f"Winners image failed: {win_ex}")
                        # Fall back to text-only announcement
                        await interaction.channel.send(
                            f"🏆 **Tournament complete!** Congratulations to: {mentions}"
                        )
 
            except Exception as e:
                logger.error(f"Auto bracket image failed: {e}")
                await interaction.followup.send(
                    f"⚠️ Result recorded but bracket image failed: {e}", ephemeral=True
                )
 
            self.stop()
 
        return callback

class MatchResultsController(commands.Cog):
    """Controller for managing match results"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="sheets_ping", description="Test Google Sheets connectivity")
    async def sheets_ping(self, interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must be an Admin to use this command.",
                ephemeral=True
            )
            return
        
        sheet_sync = getattr(self.bot, "sheet_sync", None)
        if not sheet_sync:
            await interaction.response.send_message("❌ SheetSync is not initialized.", ephemeral=True)
            return
        try:
            await asyncio.to_thread(sheet_sync.ping)
            await interaction.response.send_message("✅ SheetSync ping successful.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ SheetSync ping failed: {e}", ephemeral=True)

    @app_commands.command(name="record_multiple_match_results", description="Record the outcomes of multiple matches")
    async def record_multiple_match_results(self, interaction):
        """Command to record results for multiple matches at once"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        # Get recent matches that don't have results yet
        db = Tournament_DB()
        try:
            # Look for matches without win/loss recorded
            db.cursor.execute("""
                SELECT DISTINCT teamId, MAX(date_played) 
                FROM Matches 
                WHERE win IS NULL AND loss IS NULL
                GROUP BY teamId
                ORDER BY teamId ASC
                LIMIT 10
            """)

            recent_matches = db.cursor.fetchall()

            if not recent_matches:
                await interaction.response.send_message("No pending matches found to record results for.")
                db.close_db()
                return

            # Prepare match data for the view
            match_results = []

            for i, (match_id, _) in enumerate(recent_matches):
                match_results.append({
                    "match_id": match_id,
                    "pool_idx": i
                })

            # Create view for match results
            view = MatchResultView(match_results)

            # Send initial message
            response = await interaction.response.send_message(
                content=f"Found {len(match_results)} matches needing results.\n"
                        f"Select a match and then click the team that won.",
                view=view
            )

            # Store message reference for later updates
            view.message = await interaction.original_response()

            # Wait for the view to complete
            await view.wait()

            # Process the results
            players_updated, _ = self._process_match_results(db, view.processed_results)
            results_processed = len(view.processed_results)

            # Collect bracket announcements as we process each match
            bracket_announcements = []

            for mid, winning_team in view.processed_results.items():
                bracket_result = self._advance_bracket_after_result(db, mid, winning_team)

                if bracket_result:
                    if bracket_result["completed_bracket"]:
                        winner_players = resolve_bracket_team(db, bracket_result["advanced_team_id"])
                        mentions = " ".join(f"<@{p['user_id']}>" for p in winner_players)
                        bracket_announcements.append(f"🏆 Tournament complete! Winning team: {mentions}")
                    else:
                        bracket_announcements.append(
                            f"✅ `{bracket_result['advanced_team_id']}` advances to "
                            f"`{bracket_result['next_match_code']}`!"
                        )

            for mid in view.processed_results.keys():
                await self._sync_match_to_sheets(db, mid)

            # Send final confirmation
            if results_processed > 0:

                def create_callback(mid):
                    async def callback(inter):
                        await self._start_mvp_voting(inter, mid)
                    return callback

                mvp_view = create_multiple_mvp_voting_buttons(
                    view.processed_results.keys(),
                    create_callback
                )

                await interaction.followup.send(
                    f"Successfully recorded results for {results_processed} matches "
                    f"and updated player stats. Would you like to start MVP voting?",
                    view=mvp_view
                )

                # Send bracket announcements after the main confirmation
                for announcement in bracket_announcements:
                    await interaction.followup.send(announcement)

        except Exception as ex:
            logger.error(f"Error recording match results: {ex}")
            await interaction.followup.send(f"Error recording match results: {str(ex)}")
        finally:
            db.close_db()

    @app_commands.command(name="record_match_result", description="Record the outcome of a single match")
  
    @app_commands.describe(
        match_id="The ID of the match (from run_matchmaking command)",
        winning_team="The number of the winning team (1 or 2)"
    )
    async def record_match_result(self, interaction, match_id: str, winning_team: int):
        """Command to record the result of a single match"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you don't have required permission to use this command",
                ephemeral=True
            )
            return
            
        if winning_team not in [1, 2]:
            await interaction.response.send_message("Winning team must be either 1 or 2", ephemeral=True)
            return

        db = Tournament_DB()
        try:
            db.cursor.execute("SELECT COUNT(*) FROM Matches WHERE teamId = ?", (match_id,))
            count = db.cursor.fetchone()[0]

            # Also check BracketMatches in case it's a bracket round match code
            if count == 0:
                db.cursor.execute("SELECT COUNT(*) FROM BracketMatches WHERE match_code = ?", (match_id,))
                bracket_count = db.cursor.fetchone()[0]
                
                if bracket_count == 0:
                    await interaction.response.send_message(
                        f"❌ Match ID `{match_id}` not found in Matches or BracketMatches.",
                        ephemeral=True
                    )
                    return

            # Process the match result
            results = {match_id: winning_team}
            players_updated, _ = self._process_match_results(db, results)

            await self._sync_match_to_sheets(db, match_id)

            # Create callback for MVP voting button
            async def mvp_callback(inter):
                await self._start_mvp_voting(inter, match_id)
                
            # Create view with button to start MVP voting
            mvp_view = create_mvp_voting_button(match_id, mvp_callback)
            
            # Send confirmation
            await interaction.response.send_message(
                f"Match {match_id} result recorded: Team {winning_team} wins!\n"
                f"Updated stats for {players_updated} players.",
                view=mvp_view
            )
            bracket_result = self._advance_bracket_after_result(db, match_id, winning_team)

            if bracket_result:
                if bracket_result["completed_bracket"]:
                    winner_players = resolve_bracket_team(db, bracket_result["advanced_team_id"])
                    mentions = " ".join(f"<@{p['user_id']}>" for p in winner_players)
                    await interaction.followup.send(f"🏆 Tournament complete! Winning team: {mentions}")
                else:
                    await interaction.followup.send(
                        f"✅ `{bracket_result['advanced_team_id']}` advances to `{bracket_result['next_match_code']}`!")

        except Exception as ex:
            logger.error(f"Error recording match result: {ex}")
            await interaction.response.send_message(f"Error recording match result: {str(ex)}")
        finally:
            db.close_db()

    def _populate_bracket_match(self, db, bracket_match_code: str):
        """
        For a bracket round match code (e.g. match_3), copy the players
        from the original matchmaking teams into the Matches table so that
        _process_match_results can update their stats normally.

        Only inserts if rows don't already exist for this bracket match code.
        """
        # Check if already populated
        db.cursor.execute(
            "SELECT COUNT(*) FROM Matches WHERE teamId = ?",
            (bracket_match_code,)
        )
        if db.cursor.fetchone()[0] > 0:
            return  # already populated, skip

        # Get the team IDs from BracketMatches
        db.cursor.execute(
            "SELECT teamA_id, teamB_id FROM BracketMatches WHERE match_code = ?",
            (bracket_match_code,)
        )
        row = db.cursor.fetchone()
        if not row:
            logger.error(f"_populate_bracket_match: no BracketMatch found for {bracket_match_code}")
            return

        teamA_id, teamB_id = row  # e.g. "match_1_team1", "match_2_team2"

        teams = {
            "team1": teamA_id,
            "team2": teamB_id,
        }

        from model.dbc_model import Matches
        matches_db = Matches(db_name=settings.DATABASE_NAME)
        matches_db.connection = db.connection
        matches_db.cursor = db.cursor
        match_num = matches_db.get_next_match_id()

        for team_slot, source_team_id in teams.items():
            if not source_team_id:
                continue

            # Parse source match_code and teamUp from team_id string
            if source_team_id.endswith("_team1"):
                src_match_code = source_team_id[:-6]
                src_team_up    = "team1"
            elif source_team_id.endswith("_team2"):
                src_match_code = source_team_id[:-6]
                src_team_up    = "team2"
            else:
                continue

            # Copy players from the original matchmaking match
            db.cursor.execute(
                "SELECT user_id, game_name FROM Matches WHERE teamId = ? AND teamUp = ?",
                (src_match_code, src_team_up)
            )
            players = db.cursor.fetchall()

            for user_id, game_name in players:
                db.cursor.execute(
                    """
                    INSERT INTO Matches (user_id, game_name, teamUp, teamId, match_num, date_played)
                    VALUES (?, ?, ?, ?, ?, date('now'))
                    """,
                    (user_id, game_name, team_slot, bracket_match_code, match_num)
                )

        db.connection.commit()
        logger.info(f"Populated bracket match {bracket_match_code} with players from {teamA_id} vs {teamB_id}")

    def _process_match_results(self, db, match_results):
        """Process match results and update database
        
        Args:
            db: Database connection
            match_results: Dictionary mapping match_id to winning_team
            
        Returns:
            Number of results processed
        """
        results_processed = 0
        players_updated = 0

        affected_player_ids = set()
        match_rows = []  # rows to append to Google Sheet "Matches" tab
        
        for match_id, winning_team in match_results.items():
            # Update winners
            winning_team_name = f"team{winning_team}"
            losing_team_name = f"team{3 - winning_team}"  # If winning_team is 1, losing is 2 and vice versa

            # Update winners
            db.cursor.execute(
                "UPDATE Matches SET win = 'yes', loss = 'no' WHERE teamId = ? AND teamUp = ?",
                (match_id, winning_team_name)
            )
            winners_updated = db.cursor.rowcount
            logger.info(f"Updated {winners_updated} winners for match {match_id}, team {winning_team_name}")

            # Update losers
            db.cursor.execute(
                "UPDATE Matches SET win = 'no', loss = 'yes' WHERE teamId = ? AND teamUp = ?",
                (match_id, losing_team_name)
            )
            losers_updated = db.cursor.rowcount
            logger.info(f"Updated {losers_updated} losers for match {match_id}, team {losing_team_name}")
            
            # Update all other players in this match (e.g., volunteers or participation) to mark match as completed
            db.cursor.execute(
                "UPDATE Matches SET win = 'n/a', loss = 'n/a' WHERE teamId = ? AND win IS NULL AND loss IS NULL",
                (match_id,)
            )
            others_updated = db.cursor.rowcount
            logger.info(f"Updated {others_updated} other players for match {match_id} to mark as completed")

            # Get player stats to update
            db.cursor.execute(
                "SELECT user_id, teamUp FROM Matches WHERE teamId = ?",
                (match_id,)
            )
            players = db.cursor.fetchall()

            # Update player stats in the Game table
            for player_id, team in players:
                affected_player_ids.add(player_id)
                
                # Get current player stats
                db.cursor.execute(
                    "SELECT wins, losses FROM game WHERE user_id = ? ORDER BY game_date DESC LIMIT 1",
                    (player_id,)
                )
                result = db.cursor.fetchone()

                if not result:
                    continue
                
                current_wins, current_losses = result

                # Set default values if None
                current_wins = current_wins if current_wins is not None else 0
                current_losses = current_losses if current_losses is not None else 0

                 # Update based on match result
                if team == winning_team_name:
                    new_wins = current_wins + 1
                    update_query = """
                        UPDATE game SET wins = ?
                        WHERE user_id = ? AND game_date = (
                            SELECT MAX(game_date) FROM game WHERE user_id = ?
                        )
                    """
                    db.cursor.execute(update_query, (new_wins, player_id, player_id))
                elif team == losing_team_name:  # Exclude participation players
                    new_losses = current_losses + 1
                    update_query = """
                        UPDATE game SET losses = ?
                        WHERE user_id = ? AND game_date = (
                            SELECT MAX(game_date) FROM game WHERE user_id = ?
                        )
                    """
                    db.cursor.execute(update_query, (new_losses, player_id, player_id))
                
                if team in [winning_team_name, losing_team_name]:
                    players_updated += 1

            # Make sure to commit changes after each match is processed
            db.connection.commit()
            logger.info(f"Committed changes for match {match_id}")

            results_processed += 1

        # Final commit for any remaining changes
        db.connection.commit()
        logger.info(f"Final commit complete, processed {results_processed} matches")
        
        return players_updated, affected_player_ids


    def _advance_bracket_after_result(self, db, match_code: str, winning_team: int):
        """
        match_code example: 'match_1'
        winning_team:
            1 -> teamA_id wins
            2 -> teamB_id wins
        """

        try:
            db.cursor.execute("""
                SELECT bracket_id, teamA_id, teamB_id, next_match_code, next_slot, status
                FROM BracketMatches
                WHERE match_code = ?
            """, (match_code,))
            row = db.cursor.fetchone()

            if not row:
                return None  # not a bracket match

            bracket_id, teamA_id, teamB_id, next_match_code, next_slot, status = row

            if not teamA_id or not teamB_id:
                logger.error(f"Bracket match {match_code} is incomplete (missing teams)")
                return None
            if status == "completed":
                return None

            if winning_team == 1:
                winner_team_id = teamA_id
                loser_team_id = teamB_id
            elif winning_team == 2:
                winner_team_id = teamB_id
                loser_team_id = teamA_id
            else:
                raise ValueError("winning_team must be 1 or 2")

            db.cursor.execute("""
                UPDATE BracketMatches
                SET winner_team_id = ?, loser_team_id = ?, status = 'completed'
                WHERE match_code = ?
            """, (winner_team_id, loser_team_id, match_code))

            # Championship match
            if not next_match_code:
                db.cursor.execute("""
                    UPDATE Brackets
                    SET status = 'complete'
                    WHERE bracket_id = ?
                """, (bracket_id,))
                db.connection.commit()
                return {
                    "advanced_team_id": winner_team_id,
                    "next_match_code": None,
                    "completed_bracket": True
                }

            # Advance winner to next bracket match
            if next_slot == "A":
                db.cursor.execute("""
                    UPDATE BracketMatches
                    SET teamA_id = ?
                    WHERE match_code = ?
                """, (winner_team_id, next_match_code))
            elif next_slot == "B":
                db.cursor.execute("""
                    UPDATE BracketMatches
                    SET teamB_id = ?
                    WHERE match_code = ?
                """, (winner_team_id, next_match_code))

            db.cursor.execute("""
                SELECT teamA_id, teamB_id
                FROM BracketMatches
                WHERE match_code = ?
            """, (next_match_code,))
            next_row = db.cursor.fetchone()

            if next_row and next_row[0] and next_row[1]:
                db.cursor.execute("""
                    UPDATE BracketMatches
                    SET status = 'ready'
                    WHERE match_code = ?
                """, (next_match_code,))

            db.connection.commit()

            return {
                "advanced_team_id": winner_team_id,
                "next_match_code": next_match_code,
                "completed_bracket": False
            }

        except Exception as ex:
            logger.error(f"_advance_bracket_after_result failed with error {ex}")
            return None
    
    async def _sync_match_to_sheets(self, db: Tournament_DB, match_id: str):
        sheet_sync = getattr(self.bot, "sheet_sync", None)
        if not sheet_sync:
            logger.info("SheetSync not initialized; skipping Sheets mirror.")
            return

        # 1) Build match rows (append-only)
        db.cursor.execute(
            "SELECT user_id, teamUp, win, loss FROM Matches WHERE teamId = ?",
            (match_id,)
        )
        match_entries = db.cursor.fetchall()

        # Match sheet row format example:
        # [match_id, user_id, teamUp, win, loss]
        match_rows = []
        affected_ids = set()

        for user_id, teamUp, win, loss in match_entries:
            affected_ids.add(user_id)
            match_rows.append([match_id, user_id, teamUp, win, loss])

        logger.info(f"[DB] settings.DATABASE_NAME = {settings.DATABASE_NAME}")

        db.cursor.execute("PRAGMA database_list;")
        logger.info(f"[DB] database_list = {db.cursor.fetchall()}")

        db.cursor.execute("PRAGMA table_info(game);")
        cols = [r[1] for r in db.cursor.fetchall()]   # <-- fetch immediately
        logger.info(f"[DB] game columns = {cols}")

        tox_col = "toxicity_points" if "toxicity_points" in cols else None
        mvp_col = "mvp_count" if "mvp_count" in cols else None

        select_tox = f"g.{tox_col}" if tox_col else "0"
        select_mvp = f"g.{mvp_col}" if mvp_col else "0"
        # 2) Pull latest stats for affected players
        players_for_sync = []
        for pid in affected_ids:
            db.cursor.execute(f"""
                SELECT p.user_id, p.game_name, p.tag_id,
                    g.tier, g.rank, g.role, g.wins, g.losses,
                    g.manual_tier, {select_tox} as toxicity_points, {select_mvp} as mvp_count
                FROM player p
                JOIN game g ON p.user_id = g.user_id
                WHERE p.user_id = ?
                ORDER BY g.game_date DESC
                LIMIT 1
            """, (pid,))
            row = db.cursor.fetchone()
            if not row:
                continue

            (player_id, game_name, tag_id, tier, rank, role,
            wins, losses, manual_tier, toxicity_points, mvp_count) = row

            players_for_sync.append({
                "player_id": player_id,
                "game_name": game_name,
                "tag_id": tag_id,
                "tier": (tier or "default"),
                "rank": (rank or "V"),
                "role": role or "",
                "wins": wins or 0,
                "losses": losses or 0,
                "manual_tier": manual_tier,
                "toxicity_points": toxicity_points or 0,
                "mvp_count": mvp_count or 0,
            })

        # 3) Offload Sheets calls to a thread (gspread is blocking)
        try:
            await asyncio.to_thread(sheet_sync.append_match_rows, match_rows)
            await asyncio.to_thread(sheet_sync.upsert_players_batch, players_for_sync)
            logger.info(f"Synced match {match_id} to Sheets: {len(players_for_sync)} players.")
        except Exception as ex:
            logger.error(f"Sheets sync failed (non-fatal) for match {match_id}: {ex}")



    async def _start_mvp_voting(self, interaction, match_id):
        """Start MVP voting for a match
        
        Args:
            interaction: Discord interaction
            match_id: ID of the match to start voting for
        """
        try:
            mvp_cog = self.bot.get_cog("MVPVotingController")
            if mvp_cog:
                # Access the start_mvp_voting command's callback directly
                cmd = mvp_cog.start_mvp_voting
                # Call the callback with the appropriate context
                await cmd.callback(mvp_cog, interaction, match_id)
            else:
                await interaction.response.send_message(
                    "MVP voting module not available. Please contact an administrator.",
                    ephemeral=True
                )
        except Exception as ex:
            logger.error(f"Error starting MVP voting: {ex}")
            await interaction.response.send_message(
                f"Error starting MVP voting: {str(ex)}",
                ephemeral=True
            )

    @app_commands.command(name="show_bracket", description="Display the current state of a bracket")
    
    @app_commands.describe(bracket_id="The bracket ID to display (e.g. bracket_1)")
    async def show_bracket(self, interaction, bracket_id: str):
        """Generate and post a bracket image for the given bracket_id."""
        await interaction.response.defer()          # image generation can take a moment

        db = Tournament_DB()
        try:
            # Verify the bracket exists
            db.cursor.execute(
                "SELECT status, total_teams FROM Brackets WHERE bracket_id = ?",
                (bracket_id,)
            )
            row = db.cursor.fetchone()

            if not row:
                await interaction.followup.send(
                    f"❌ Bracket `{bracket_id}` not found.", ephemeral=True
                )
                return

            status, total_teams = row

        finally:
            db.close_db()

        def generate():
            thread_db = Tournament_DB()
            try:
                return create_bracket_image(bracket_id, thread_db)
            finally:
                thread_db.close_db()

        try:
            img_path = await asyncio.to_thread(generate)

            # Build embed
            status_emoji = {
                "active":   "🟢",
                "complete": "🏆",
                "pending":  "🕐",
            }.get(status, "⚪")

            embed = discord.Embed(
                title=f"📊  Bracket — {bracket_id}",
                description=f"{status_emoji} Status: **{status.upper()}**  ·  Teams: **{total_teams}**",
                color=discord.Color.gold() if status == "complete" else discord.Color.blue(),
            )
            embed.set_footer(text=f"Bracket ID: {bracket_id}")

            # Attach image
            file = discord.File(img_path, filename=f"bracket_{bracket_id}.png")
            embed.set_image(url=f"attachment://bracket_{bracket_id}.png")

            await interaction.followup.send(embed=embed, file=file)

        except ValueError as ve:
            await interaction.followup.send(f"❌ {ve}", ephemeral=True)
        except Exception as ex:
            import logging
            logging.getLogger("discord").error(f"show_bracket failed: {ex}")
            await interaction.followup.send(
                f"❌ Failed to generate bracket image: {str(ex)}", ephemeral=True
            )
        finally:
            db.close_db()

    

async def setup(bot):
    await bot.add_cog(MatchResultsController(bot))