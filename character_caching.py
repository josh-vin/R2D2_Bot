import aiohttp
import asyncio
import json
import os
from datetime import datetime, timedelta
import discord

CACHE_FILE = "all_characters_cache.json"

def load_character_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as json_file:
            return json.load(json_file)
    else:
        return None

def load_character(character_name: str):
    character_data = load_character_data()
    if not character_data:
        return None  # Cache doesn't exist or is empty

    # Search for the character object by name
    for character in character_data:
        if character['name'].lower() == character_name.lower():
            return character
    
    return None  # Character not found


def is_cache_expired(cache_file, max_age_days=1):
    if not os.path.exists(cache_file):
        return True
    cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    return datetime.now() - cache_time > timedelta(days=max_age_days)

async def fetch_from_api(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to fetch data from {url}: {response.status}")

async def fetch_all_characters_and_ships():
    characters_url = "https://swgoh.gg/api/characters"
    ships_url = "https://swgoh.gg/api/ships"
    
    # Fetch characters and ships concurrently
    characters_data, ships_data = await asyncio.gather(
        fetch_from_api(characters_url),
        fetch_from_api(ships_url)
    )
    
    # Extract and combine the name and image for characters and ships
    combined_data = [
        {"name": item["name"], "image": item["image"], "type": "character"}
        for item in characters_data
    ] + [
        {"name": item["name"], "image": item["image"], "type": "ship"}
        for item in ships_data
    ]
    return combined_data

async def update_all_characters_cache():
    if is_cache_expired(CACHE_FILE):
        # Load the existing cache if it exists
        all_data = await fetch_all_characters_and_ships()

        try:
            cached_data = load_character_data()
            
            # Compare the fetched data with the cached data
            if cached_data is None or all_data != cached_data:
                print("Cache has differences or is missing. Updating...")
                with open(CACHE_FILE, "w") as f:
                    json.dump(all_data, f, indent=4)
                print("Cache updated.")
        except Exception as e:
            print(f"Error updating cache: {e}")

async def get_valid_all_characters(ctx: discord.AutocompleteContext):
    text = ctx.value

    # Ensure the cache is updated before searching
    cached_data = load_character_data()
    
    # Compare the fetched data with the cached data
    if cached_data is None:
        await update_all_characters_cache()
    
    # Load cached data
    all_data = load_character_data()
    
    # Filter names (characters and ships) based on user input
    filtered_names = [
        item["name"] for item in all_data if text.lower() in item["name"].lower()
    ]

    filtered_names = sorted(filtered_names)
    
    # Return the first 25 matches or all matches if fewer than 25
    return filtered_names[:25]