import requests
import sys

def get_guild_id(guild_name):
    url = 'http://localhost:5678/getGuilds'
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
            if guild['name'] == guild_name:
                return guild['id'], guild['memberCount']
        else:
            print("Guild not found.")
            return None
    else:
        print("Failed to fetch guild. Status code:", response.status_code)
        return None

def get_player_id_from_guild(guild_id, player_name):
    url = 'http://localhost:5678/guild'
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
    url = 'http://localhost:5678/player'
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

    guild_id = get_guild_id(guild_name)
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