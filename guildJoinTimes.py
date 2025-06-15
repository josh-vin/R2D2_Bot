import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_guild_members():
    url = f'{os.getenv("COMLINK_API")}/guild'
    payload = {
        "payload": {
            "guildId": "jb7VVuWETreqtBkJmVx1Tw",
            "includeRecentGuildActivityInfo": True
        },
        "enums": True
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get('guild', {}).get('member', [])
    else:
        print("Failed to fetch guild members. Status code:", response.status_code)
        return []

def format_join_time(epoch_time):
    try:
        epoch_time = int(epoch_time)
        return datetime.utcfromtimestamp(epoch_time).strftime('%m/%d/%Y %I:%M %p')
    except ValueError:
        return "Invalid timestamp"


def main():
    guild_members = fetch_guild_members()

    if guild_members:
        for member in guild_members:
            player_name = member.get('playerName', 'Unknown')
            join_time = member.get('guildJoinTime', 0)
            formatted_join_time = format_join_time(join_time)
            print(f"{player_name}, {formatted_join_time} UTC")
    else:
        print("No guild members found.")

if __name__ == "__main__":
    main()