import os
import csv
from dotenv import load_dotenv
import discord
from update_mod_data import find_characters_with_mod

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = 618924061677846528
CHANNEL = 1262861775649509550

# You cannot monitor "onMessage" without ALL intents and setting ALL intents on your discord bot in the dev settings
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    
    guild = bot.get_guild(int(GUILD_ID))
    raid_channel = guild.get_channel(int(CHANNEL)) if guild else None

    mod_type = "Cross"
    primary_stat = "Potency"
    mod_set = "Speed"

    matching_characters = find_characters_with_mod(mod_type, primary_stat, mod_set)
    
    if matching_characters:
        match_length = len(matching_characters)
        embeds = []
        max_chars_per_field = 200
        characters_per_field = 10
        print(f"Matching {match_length} characters for {mod_set} {mod_type} {mod_set}")

        for i in range(0, match_length, characters_per_field):
            # Group the characters
            character_group = matching_characters[i:i + characters_per_field]

            # Create a field value
            field_value = "\n".join(character_group)

            # Ensure field value doesn't exceed the max character count per field
            if len(field_value) > max_chars_per_field:
                print("Error: Field value exceeds the character limit.")
                return

            print(embeds)
            # Create an embed if it's the first group or if adding this field exceeds the limit
            if i == 0 or (embeds and embeds[-1].description and len(embeds[-1].description) + len(field_value) > 2000):
                embed = discord.Embed(
                    title=f"{match_length} Characters with {primary_stat} on {mod_type} with {mod_set if mod_set is not None else 'Any'} Set",
                    description="",  # Initialize description to an empty string
                    color=0x1E90FF
                )
                embeds.append(embed)

            # Add the field to the last embed
            if embeds:
                embeds[-1].add_field(name=f"{i + 1} to {i + len(character_group)}", value=field_value, inline=True)


        # Send all embeds
        for embed in embeds:
            await raid_channel.send(embed=embed)

    bot.loop.stop()

bot.run(BOT_TOKEN)
