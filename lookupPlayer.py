import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_guild_info(guild_name):
    url = f'{os.getenv("COMLINK_API")}/getGuilds'
    payload = {
        "payload": {
            "filterType": 4,
            "name": guild_name,
            "startIndex": 0,
            "count": 10
        },
        "enums": False
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        guild_data = response.json().get('guild', [])
        for guild in guild_data:
            if guild.get('name') == guild_name:
                member_count = guild.get('memberCount', 0)
                shceduled_raid_offset = guild.get('autoLaunchConfig', {}).get('scheduledUtcOffsetSeconds', None)
                return guild['id'], member_count, shceduled_raid_offset
        print("Guild not found.")
        return None, None, None
    else:
        print("Failed to fetch guild. Status code:", response.status_code)
        return None, None, None

def get_player_id_from_guild(guild_id, player_name):
    url = f'{os.getenv("COMLINK_API")}/guild'
    payload = {
        "payload": {
            "guildId": guild_id,
            "includeRecentGuildActivityInfo": True
        },
        "enums": False
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        guild_members = response.json().get('guild', {}).get('member', [])
        for member in guild_members:
            if member['playerName'] == player_name:
                return member['playerId']
        print("Player not found in the guild.")
        return None
    else:
        print("Failed to fetch guild members. Status code:", response.status_code)
        return None

def get_player_ally_code_by_id(player_id):
    url = f'{os.getenv("COMLINK_API")}/player'
    payload = {
        "payload": {
            "playerId": player_id
        },
        "enums": False
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        player_data = response.json()
        return player_data.get('allyCode')
    else:
        print("Failed to fetch player details. Status code:", response.status_code)
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py [guild_name] [player_name]")
        return

    guild_name = sys.argv[1]
    player_name = sys.argv[2]

    guild_id, _, _ = get_guild_info(guild_name) #  member_count, shceduled_raid_offset
    if guild_id:
        player_id = get_player_id_from_guild(guild_id, player_name)
        if player_id:
            ally_code = get_player_ally_code_by_id(player_id)
            if ally_code:
                print(f"Ally code for player {player_name}: {ally_code}")
        else:
            print("Failed to retrieve player's ally code.")

if __name__ == "__main__":
    main()