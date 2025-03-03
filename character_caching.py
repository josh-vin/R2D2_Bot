import aiohttp
import asyncio
import json
import os
from datetime import datetime, timedelta
import discord
from functools import wraps

CACHE_FILE = "all_characters_cache.json"

def print_and_ignore_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except discord.HTTPException as e:
            print(f"Discord HTTP error in {func.__name__}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in {func.__name__}: {str(e)}")
    return wrapper

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

def load_character_base_id(character_base_id: str):
    character_data = load_character_data()
    if not character_data:
        return None  # Cache doesn't exist or is empty

    # Search for the character object by name
    for character in character_data:
        if character['base_id'].lower() == character_base_id.lower():
            return character
    
    return None  # Character not found


def is_cache_expired(cache_file, max_age_days=1):
    if not os.path.exists(cache_file):
        return True
    cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    return datetime.now() - cache_time > timedelta(days=max_age_days)

async def fetch_from_api(url, retries=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    for _ in range(retries):
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 403:
                    print("Rate limited. Waiting before retrying...")
                    await asyncio.sleep(1)  # wait before retrying
                    continue
                response.raise_for_status()
                return await response.json()
    raise Exception(f"Failed to fetch {url} after {retries} retries")

async def fetch_all_characters_and_ships():
    characters_url = "https://swgoh.gg/api/characters"
    ships_url = "https://swgoh.gg/api/ships"
    
    # Fetch characters and ships concurrently
    characters_data = await fetch_from_api(characters_url)
    ships_data = await fetch_from_api(ships_url)
    
    # Extract and combine the name and image for characters and ships
    combined_data = [
        {"name": item["name"], "image": item["image"], "type": "character", "base_id": item["base_id"]}
        for item in characters_data
    ] + [
        {"name": item["name"], "image": item["image"], "type": "ship", "base_id": item["base_id"]}
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

@print_and_ignore_exceptions
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