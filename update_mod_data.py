# update_mod_data.py
import requests
from bs4 import BeautifulSoup
import json
import discord

# Load the JSON data from the file
def load_mod_data():
    with open("swgoh_mod_recommendations.json", "r") as json_file:
        return json.load(json_file)

def check_and_update_mod_data():
    url = "https://swgoh.gg/stats/mod-meta-report/guilds_100_gp/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    mod_data = []
    rows = soup.find_all('tr')
    base_url = "https://swgoh.gg"

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 5:
            continue
        
        character_name = cols[0].find('a').text.strip()
        best_mods_href = cols[0].find('a', href=True)['href']
        best_mods_url = base_url + best_mods_href
        portrait_url = row.find('img', class_='character-portrait__img')['src']
        
        mod_sets = [mod['title'].strip().split('\n')[2].strip() for mod in cols[1].find_all('div', class_='stat-mod-set-def-icon')]
        recommended_stats = [col.text.strip() for col in cols[2:]]
        
        mod_data.append({
            'character_name': character_name,
            'portrait_url': portrait_url,
            'best_mods_url': best_mods_url,
            'mod_sets': mod_sets,
            'recommended_stats': {
                'arrow': recommended_stats[0] if len(recommended_stats) > 0 else "",
                'triangle': recommended_stats[1] if len(recommended_stats) > 1 else "",
                'circle': recommended_stats[2] if len(recommended_stats) > 2 else "",
                'cross': recommended_stats[3] if len(recommended_stats) > 3 else ""
            }
        })
    
    with open("swgoh_mod_recommendations.json", "w") as json_file:
        json.dump(mod_data, json_file, indent=4)

# Load the JSON data from the file
def load_character_names():
    mod_data = load_mod_data()

    return [character['character_name'] for character in mod_data]

# Function to autocomplete character names
async def get_valid_mod_characters(ctx: discord.AutocompleteContext):
    text = ctx.value
    character_names = load_character_names()
    
    # Filter character names based on user input
    filtered_characters = [name for name in character_names if text.lower() in name.lower()]
    
    # Return the first 25 matches or all matches if fewer than 25
    if len(filtered_characters) > 25:
        return filtered_characters[:25]
    else:
        return filtered_characters



# Function to get the mod information for a specific character
def get_character_mod_info(character_name: str):
    mod_data = load_mod_data()

    # Find the character's mod information in the JSON data
    for character in mod_data:
        if character['character_name'].lower() == character_name.lower():
            return character
    
    return None  # Return None if the character is not found

# Function to find characters matching the search criteria
def find_characters_with_mod(mod_type=None, primary_stat=None, mod_set=None):
    mod_data = load_mod_data()
    
    characters = []
    for character in mod_data:
        # Check if mod_set matches or if mod_set is None (no filtering by mod_set)
        if mod_set is None or mod_set in character["mod_sets"]:
            for mod, stat in character["recommended_stats"].items():
                # Check if mod_type matches or if mod_type is None (no filtering by mod_type)
                if (mod_type is None or mod == mod_type.lower()) and \
                   (primary_stat is None or primary_stat in stat):
                    characters.append(character["character_name"])
                    break
    return characters
