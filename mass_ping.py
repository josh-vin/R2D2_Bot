import os
import csv
from dotenv import load_dotenv
import discord

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# You cannot monitor "onMessage" without ALL intents and setting ALL intents on your discord bot in the dev settings
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    # Read the CSV file
    with open('discord_messages.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            member_name = row['Members']
            discord_id = int(row['DiscordId'])
            faction = row['What faction has more useable toons?']
            toons_to_farm = row['Toons to Focus']
            
            if (toons_to_farm == "No Message"):
                continue
            # Format the message
            
            message = (
                ":loudspeaker: **Beep boop!**\n\nHello **" + member_name + "**!\n\n"
                "Please farm the following toons to create a " + faction + " team:\n"
                "> " + toons_to_farm + "\n\n"
                "*The team designated to you was determined by the officers, and the specific toons were determined by the most successful raid toons thus far.*" + "\n\n"
                + "**We would like to see these toons farmed to 7* and G12 minimum <t:1721930400:R>, IF POSSIBLE**" + " "
                "(We understand some of these are longer farms), to ensure that we can begin naboo raids and resume our supply of Mk3 currencies." + "\n\n"
                "Thanks for your continued efforts for the guild!\n\n"
                ":loudspeaker: **Beep boop!** *Message terminated*\n\n"
            )
            
            # Fetch the user and send the message
            try:
                user = await bot.fetch_user(discord_id)
                await user.send(message)
                print(f"Message sent to {member_name} (ID: {discord_id})")
            except Exception as e:
                print(f"Could not send message to {member_name} (ID: {discord_id}): {e}")

    await bot.close()

bot.run(BOT_TOKEN)
