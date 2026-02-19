import pytest
from aioresponses import aioresponses
from common.riot_api import RiotAPI

@pytest.mark.asyncio
async def test_fetch_summoner_by_name_success():
    api = RiotAPI()
    summoner_name = "TestSummoner"
    expected_data = {
        "id": "123",
        "accountId": "456",
        "puuid": "789",
        "name": summoner_name,
        "profileIconId": 1234,
        "summonerLevel": 30
    }

    encoded_name = summoner_name.replace(" ", "%20")
    url = f"{api.base_url}/summoner/v4/summoners/by-name/{encoded_name}"

    with aioresponses() as mocked:
        mocked.get(url, payload=expected_data, status=200)
        result = await api.fetch_summoner_by_name(summoner_name)
        assert result == expected_data

@pytest.mark.asyncio
async def test_fetch_ranked_stats_success():
    api = RiotAPI()
    summoner_id = "123"
    ranked_data = [
        {"queueType": "RANKED_SOLO_5x5", "tier": "GOLD", "rank": "IV", "wins": 10, "losses": 5},
        {"queueType": "RANKED_FLEX_SR", "tier": "SILVER", "rank": "II", "wins": 3, "losses": 2}
    ]
    url = f"{api.base_url}/league/v4/entries/by-summoner/{summoner_id}"

    with aioresponses() as mocked:
        mocked.get(url, payload=ranked_data, status=200)
        result = await api.fetch_ranked_stats(summoner_id)
        assert result['tier'] == 'GOLD'
        assert result['wins'] == 10

@pytest.mark.asyncio
async def test_get_player_info_combined():
    api = RiotAPI()
    summoner_name = "TestSummoner"
    summoner_data = {
        "id": "123",
        "accountId": "456",
        "puuid": "789",
        "name": summoner_name,
        "profileIconId": 1234,
        "summonerLevel": 30
    }
    ranked_data = [
        {"queueType": "RANKED_SOLO_5x5", "tier": "PLATINUM", "rank": "II", "wins": 20, "losses": 10}
    ]

    encoded_name = summoner_name.replace(" ", "%20")
    summoner_url = f"{api.base_url}/summoner/v4/summoners/by-name/{encoded_name}"
    ranked_url = f"{api.base_url}/league/v4/entries/by-summoner/{summoner_data['id']}"

    with aioresponses() as mocked:
        mocked.get(summoner_url, payload=summoner_data, status=200)
        mocked.get(ranked_url, payload=ranked_data, status=200)
        result = await api.get_player_info(summoner_name)

        assert result['name'] == summoner_name
        assert result['tier'] == 'platinum'
        assert result['wr'] == pytest.approx(66.6666, 0.01)

@pytest.mark.asyncio
async def test_get_champion_masteries_default_count():
    api = RiotAPI()
    summoner_id = "123"
    mastery_url = f"{api.base_url}/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}/top?count=5"
    mastery_data = [{"championId": 1, "championPoints": 10000}]

    with aioresponses() as mocked:
        mocked.get(mastery_url, payload=mastery_data, status=200)
        result = await api.get_champion_masteries(summoner_id)
        assert isinstance(result, list)
        assert result[0]['championId'] == 1
