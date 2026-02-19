from discord.ext import commands, tasks
from config import settings
from model.dbc_model import Tournament_DB , Player_game_info

logger = settings.logging.getLogger("discord")

class Tasks_Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tier_list = settings.TIER_LIST
        self.promote_player_tier.start()
        self.win_rate = settings.MIN_GAME_WINRATE
        self.min_game_played = settings.MIN_GAME_PLAYED
        self.max_game_lost = settings.MAX_GAME_LOST

    def cog_unload(self):
        self.promote_player_tier.cancel()

    @tasks.loop(seconds=7200)
    async def promote_player_tier(self):
        db = Tournament_DB()

        results = Player_game_info.fetch_for_tier_promotion(db)
        if results is not None:
            for row in results:
                player_id = row[0]
                player_tier = row[1].strip().lower()
                player_game_played = row[2]
                player_wr = row[3]
                #if the player wins is greater than 10 and wr is greater than 62%
                #then we promote the player to the next tier
                if player_game_played >= self.min_game_played and player_wr >= self.win_rate:
                    if player_tier in self.tier_list:
                        tier_index = self.tier_list.index(player_tier)
                        next_tier = self.tier_list[tier_index+1]

                        #update the player tier
                        if next_tier is not None:
                            Player_game_info.update_tier(db, player_id, next_tier)
                    else:
                        logger.info(f"the tier: {player_tier} is not in the {self.tier_list}")

                #if the player losses is greater than self.game_loss(default is 15) then we demote the player to the previous tier
                elif player_game_played >= self.max_game_lost:
                    if player_tier in self.tier_list:
                        tier_index = self.tier_list.index(player_tier)
                        prev_tier = self.tier_list[tier_index-1]

                        #update the player tier
                        if prev_tier is not None:
                            Player_game_info.update_tier(db, player_id, prev_tier)
                    else:
                        logger.info(f"the tier: {player_tier} is not in the {self.tier_list}")
                
            db.close_db()
    
    @promote_player_tier.before_loop
    async def before_promote_player_tier(self):
        await self.bot.wait_until_ready()



async def setup(bot):
    await bot.add_cog(Tasks_Collection(bot))