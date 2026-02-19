import discord
from discord.ext import commands, tasks
from config import settings
from model.dbc_model import Tournament_DB ,Player, Game
import requests
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

logger = settings.logging.getLogger("discord")

'''Depend on the API we use, we can use below two ptions
    Depend on the API we can use API key for request autnetication
    or
    We use API key in headeres for authorization
'''

class Api_Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_all_players_details.start()

    def cog_unload(self):
        self.fetch_all_players_details.cancel()

    @tasks.loop(seconds=600)
    async def fetch_all_players_details(self):
        db = Tournament_DB()
        #we pass here the game a hard coded
        all_players = Player.get_all_player(db)
        if all_players is not None:
            for player in all_players:
                logger.info(f"start to fetch a player discord is: {Fore.CYAN}{player[0]}{Style.RESET_ALL} details from riot api")
                player_info = await self.get_player_details(player[1], player[2])

                if player_info and player_info[0]['rank']:
                    # player_rank = player_info.get('rank', 'unranked')
                    player_tier = player_info[0]['tier']
                    player_rank = player_info[0]['rank']
                    player_wins = player_info[0]['wins']
                    player_losses = player_info[0]['losses']
                    
                    # Create a Game instance to ensure the method is called properly
                    game_db = Game(db_name=settings.DATABASE_NAME)
                    game_db.connection = db.connection
                    game_db.cursor = db.cursor
                    game_db.update_player_API_info(player[0], player_tier, player_rank, player_wins, player_losses)
            db.close_db()
    @fetch_all_players_details.before_loop
    async def before_fetch_all_players_details(self):
        await self.bot.wait_until_ready()


    async def get_player_details(interaction: discord.Interaction, game_name, tag_id):
        # headers = {
        #     'Authorization': f'Bearer {settings.API_KEY}',
        #     'Content-Type': 'application/json'
        #     }
        headers = {'X-Riot-Token': settings.API_KEY}

        url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_id}?api_key={settings.API_KEY}'
        url_puuid = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid"
        url_summonId = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner"
        try: 
            # response = requests.get(url, headers=headers)
            response = requests.get(url=url, headers=headers)

            if response.status_code == 200:
                account_info = response.json()
                puuid = account_info['puuid']

                if puuid is not None:
                    response = requests.get(f"{url_puuid}/{puuid}?api_key={settings.API_KEY}", headers=headers)
                    if response.status_code==200:
                        result_format = response.json()
                        summoner_id = result_format['id']

                        if summoner_id is not None:
                            response = requests.get(f"{url_summonId}/{summoner_id}?api_key={settings.API_KEY}", headers=headers)
                            return response.json()
                    else:
                        logger.info(f"not result for user puuid {Fore.RED}{puuid}{Style.RESET_ALL} and url: {url_puuid}")
                        return
            else:
                print(f"not result for user tag_id: {Fore.RED}{tag_id}{Style.RESET_ALL} and url: {url}")
                return
        except Exception as ex:
            logger.info(f"the request to get user puuid is failed")

    
    @commands.Cog.listener()
    async def on_message(self, message):
        """this event listner is for admin to stop and run the api schedule
        """
        if message.content.strip().lower() == settings.STOP_API_TASK.strip().lower():
            #check the permission if the user is admin
            if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
                if self.fetch_all_players_details.is_running():
                    self.fetch_all_players_details.cancel()
                    await message.channel.send("api task is stoped", ephemeral=True)

                else:
                    await message.channel.send("api task wasnt running", ephemeral=True)

        if message.content.strip().lower() == settings.START_API_TASK.strip().lower():
            #check the permission if the user is admin
            if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
                if not self.fetch_all_players_details.is_running():
                    self.fetch_all_players_details.start()
                    await message.channel.send("api task start", ephemeral=True)

                else:
                    await message.channel.send("api task was running", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Api_Collection(bot))