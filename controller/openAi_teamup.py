from openai import OpenAI
from config import settings

""" Open ai players team up foramtion for tournament
    parameter:
        api_key, prompt,
        token: depending on the number of playeres the token will be adjusted
"""
async def openAi_teamUp(players):
    client = OpenAI(
        api_key= settings.API_KEY 
    )

    prompt = """
        Task: You are tasked with creating two balanced 5v5 teams for a tournament, based on players' skill levels (tiers) and role preferences.

        Team and Role Constraints:
            1. **75% Balanced Skill Levels First**: The teams must be balanced based on skill level (tiers). Ensure that both teams have players from different tiers, with no team being significantly stronger or weaker than the other. The first priority is to make the teams skill-balanced.
            2. **25% Role Preferences Second**: After balancing the teams by skill, assign players to their top preferred role. If a player's top preferred role is already filled, assign them to their second choice, and so on. The skill of the player will decrease by 5% for each preference level beyond their first choice (i.e., second choice reduces skill by 5%, third choice by 10%, etc.).
            3. **Distinct Roles**: Each team must have one player assigned to each of the following roles:
                - Top
                - Jungle
                - Mid
                - Bottom
                - Support

        Player Tiers: Players are ranked from Challenger (highest skill) to Iron (lowest skill). The given list of players is already ordered by their skill level (tier), so the first player in the list is the highest-skilled player, and the last player is the lowest-skilled player.
            Distribute players evenly between the two teams, ensuring each team has a mix of skill levels, aiming to create balanced teams overall.

        Instructions:
            You will be given a list of players, their tiers, and their preferred roles. Please assign each player to one of the two teams while ensuring the following:
            1. **Balanced Teams**: Distribute players first by skill level to ensure balanced teams. The goal is to create teams where the overall skill difference between the two is minimal.
            2. **Role Preferences**: After balancing by skill, assign players to their preferred roles while respecting the order of their preferences. If a player's top role is unavailable, assign them to the next preferred role.
            3. **Skill Impact of Preferences**: If a player is assigned a role that is lower in preference (second, third, etc.), reduce their skill by 5% for each preference level beyond the first.
            4. **Final Role Assignment**: If all of a player's preferred roles are taken, assign them to whichever role remains unassigned.

        Return the two teams, including their respective role assignments, ensuring that the balance of skill and roles is as described.
        """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {"role": "system", "content": settings.prompt},
            {"role": "user", "content": players}
        ],
        temperature=0.7,
        max_tokens= 1000,
        top_p= 0.95,
        frequency_penalty=0,
        presence_penalty=0,  
    )

    # print(response)
    return response


async def get_generated_teams(response):
    teams = {"t1": [], "t1": []}

    #this function is based on the AI response structure
    #this can be modifed with different code structure
    completion_t1_start = response.find('### Team A:')
    completion_t2_start = response.find('### Team B')

    t1_values = response[completion_t1_start:completion_t2_start].strip().split("\n")
    for line in t1_values:
        if line.startswith("-"):
            assignedRole_player = line.split(": ")
            if len(assignedRole_player)==2:
                assignedRole, player = assignedRole_player
                teams['t1'].append(f"{assignedRole}: {player}")

    t2_values = response[completion_t2_start:].strip().split("\n")
    for line in t2_values:
        if line.startswith("-"):
            assignedRole_player = line.split(": ")
            if len(assignedRole_player)==2:
                assignedRole, player = assignedRole_player
                teams['t2'].append(f"{assignedRole}: {player}")

    return teams

players = "[{'user_id': 'player10', 'tier': 'master', 'rank': 'II', 'wr': 93, 'role': ['top', 'Bottom', 'Jungle', 'support']}, {'user_id': 'player9', 'tier': 'diamond', 'rank': 'II', 'wr': 75, 'role': ['mid', 'top', 'Jungle']}, {'user_id': 'player1', 'tier': 'platinum', 'rank': 'II', 'wr': 56, 'role': ['mid', 'top', 'Jungle']}, {'user_id': 'player3', 'tier': 'platinum', 'rank': 'IV', 'wr': 77, 'role': ['bottom', 'top', 'Jungle', 'mid', 'support']}, {'user_id': 'player8', 'tier': 'platinum', 'rank': 'V', 'wr': 47, 'role': ['mid']}, {'user_id': 'player5', 'tier': 'gold', 'rank': 'I', 'wr': 69, 'role': ['top', 'Jungle', 'mid']}, {'user_id': 'player2', 'tier': 'gold', 'rank': 'II', 'role': ['support', 'mid'], 'wr': 73}, {'user_id': 'player7', 'tier': 'gold', 'rank': 'IV', 'wr': 47, 'role': ['bottom', 'mid', 'top', 'Jungle', 'support']}, {'user_id': 'player6', 'tier': 'bronze', 'rank': 'I', 'wr': 86, 'role': ['top', 'Jungle']}, {'user_id': 'player4', 'tier': 'bronze', 'rank': 'III', 'wr': 78, 'role': ['Jungle']}]"
# player_data = {"players": [{'name': 'player10', 'tier': 'master', 'role': ['top', 'Bottom', 'Jungle', 'support']}, {'name': 'player9', 'tier': 'diamond', 'role': ['mid', 'top', 'Jungle']}, {'name': 'player1', 'tier': 'platinum', 'role': ['mid', 'top', 'Jungle']}, {'name': 'player3', 'tier': 'platinum', 'role': ['bottom', 'top', 'Jungle', 'mid', 'support']}, {'name': 'player8', 'tier': 'platinum', 'role': ['mid']}, {'name': 'player5', 'tier': 'gold', 'role': ['top', 'Jungle', 'mid']}, {'name': 'player2', 'tier': 'gold', 'role': ['support', 'mid']}, {'name': 'player7', 'tier': 'gold', 'role': ['bottom', 'mid', 'top', 'Jungle', 'support']}, {'name': 'player6', 'tier': 'bronze', 'role': ['top', 'Jungle']}, {'name': 'player4', 'tier': 'bronze', 'role': ['Jungle']}]}
async def main():
    resp = await openAi_teamUp(players)
    teams = await get_generated_teams(resp)

    print(teams)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

async def setup(bot):
    pass



