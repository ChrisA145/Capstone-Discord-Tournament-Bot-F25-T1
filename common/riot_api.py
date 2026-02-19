import aiohttp
import asyncio
import json
import logging
import os
from config import settings

logger = settings.logging.getLogger("discord")

class RiotAPI:
    """
    A class for interacting with the Riot Games API for League of Legends
    """
    def __init__(self):
        self.api_key = os.environ.get('RIOT_API_KEY', '')
        self.base_url = os.environ.get('API_URL', 'https://na1.api.riotgames.com/lol')
        self.headers = {
            "X-Riot-Token": self.api_key
        }

    async def fetch_summoner_by_name(self, summoner_name):
        """Fetch a summoner's account information by their summoner name"""
        # URL encode the name
        encoded_name = summoner_name.replace(' ', '%20')
        url = f"{self.base_url}/summoner/v4/summoners/by-name/{encoded_name}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.info(f"Summoner {summoner_name} not found")
                        return None
                    else:
                        logger.error(f"Error fetching summoner {summoner_name}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Exception fetching summoner {summoner_name}: {e}")
            return None

    async def fetch_ranked_stats(self, summoner_id):
        """Fetch a summoner's ranked stats by their summoner ID"""
        url = f"{self.base_url}/league/v4/entries/by-summoner/{summoner_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Find solo queue stats
                        for queue in data:
                            if queue.get('queueType') == 'RANKED_SOLO_5x5':
                                return queue
                        return None
                    elif response.status == 404:
                        logger.info(f"No ranked stats found for summoner {summoner_id}")
                        return None
                    else:
                        logger.error(f"Error fetching ranked stats: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Exception fetching ranked stats: {e}")
            return None

    async def get_player_info(self, summoner_name):
        """
        Get a player's information from the Riot API, including their rank
        Returns a dictionary with player's information or None if not found
        """
        # First get summoner data
        summoner_data = await self.fetch_summoner_by_name(summoner_name)
        if not summoner_data:
            return None
        
        # Then get their ranked stats
        ranked_data = await self.fetch_ranked_stats(summoner_data['id'])
        
        # Build player info dictionary
        player_info = {
            'name': summoner_data['name'],
            'level': summoner_data['summonerLevel'],
            'profile_icon_id': summoner_data['profileIconId'],
            'puuid': summoner_data['puuid'],
            'account_id': summoner_data['accountId'],
            'id': summoner_data['id'],
            'tier': 'default',
            'rank': 'V',
            'wins': 0,
            'losses': 0,
            'wr': 0.0
        }
        
        # Add ranked info if available
        if ranked_data:
            player_info['tier'] = ranked_data.get('tier', 'default').lower()
            player_info['rank'] = ranked_data.get('rank', 'V')
            player_info['wins'] = ranked_data.get('wins', 0)
            player_info['losses'] = ranked_data.get('losses', 0)
            
            # Calculate win rate
            total_games = player_info['wins'] + player_info['losses']
            if total_games > 0:
                player_info['wr'] = (player_info['wins'] / total_games) * 100
        
        return player_info

    async def get_champion_masteries(self, summoner_id, count=5):
        """Get a player's top champion masteries"""
        url = f"{self.base_url}/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}/top"
        if count:
            url += f"?count={count}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching champion masteries: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Exception fetching champion masteries: {e}")
            return []