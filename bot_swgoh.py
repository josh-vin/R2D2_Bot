import os
from lookupPlayer import get_guild_id, get_player_id_from_guild, get_player_ally_code_by_id
from dotenv import load_dotenv
import discord
from discord import option
from discord.ext import tasks
from datetime import datetime, timedelta
import json
import pytz
from zoneinfo import ZoneInfo
import requests
import re
from update_mod_data import check_and_update_mod_data, get_valid_mod_characters, get_character_mod_info, find_characters_with_mod
from png_generator import create_image_with_mods

# region Setup
# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# GLOBALS
RESET_MINUTE = "30" # ex. 10:{30} <-
FORMAT24 = "Military"
PREVIOUS_RANKS = None

# You cannot monitor "onMessage" without ALL intents and setting ALL intents on your discord bot in the dev settings
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

# Load guild reset times from JSON file on bot startup
try:
    with open("guild_reset_times.json", "r") as file:
        guild_reset_times = json.load(file)
except FileNotFoundError:
    guild_reset_times = {}

try:
    with open("personal_reset_times.json", "r") as file:
        personal_reset_times = json.load(file)
except FileNotFoundError:
    guild_reset_times = {}

try:
    with open("ally_code_tracking.json", "r") as file:
        ally_code_tracking = json.load(file)
except FileNotFoundError:
    guild_reset_times = {}

try:
    with open("channels.json", "r") as file:
        channels = json.load(file)
except FileNotFoundError:
    channels = {}

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

# Define the activity messages
activity_messages = {
    "Sunday": {
        "Challenge Title":"Spend Cantina Energy",
        "HexColor": 0xdb0b31,
        "Image URL": "https://swgoh.wiki/images/4/4c/Game-Icon-Cantina_Energy.png",
        "Before Guild Reset": ":crossed_swords: Finish Squad Arena PvP Battles\n:no_entry: Do not spend Cantina Energy\n:moneybag: Buy Refresh Cantina Energy when close to max before reset",
        "After Guild Reset": ":zap: Spend ALL Cantina Energy\n:checkered_flag: 2 refreshes is the Goal\n:arrows_counterclockwise: If you don't typically refresh Cantina, do it on this day\n:bulb: Spend rest of Normal Energy to reach 600 Raid Tickets",
        "Footer": ""
    },
    "Monday": {
        "Challenge Title":"Spend Light Side Energy",
        "HexColor": 0xfdc331,
        "Image URL": "https://swgoh.wiki/images/b/ba/Game-Icon-Energy.png",
        "Before Guild Reset": "\n:bulb: Check Guild Tier and make sure you've spent enough\n:bulb: Save Cantina energy for ANY energy Activity in 2 days\n:arrows_counterclockwise: Buy 3 Refreshes of Normal Energy for next Activity",
        "After Guild Reset": ":zap: Spend Light Side Energy\n:checkered_flag: 1400 is the Goal\n:bulb: Spend all Energy and Bonuses\n:arrows_counterclockwise: 3 refreshes all on Light Side",
        "Footer": ""
    },
    "Tuesday": {
        "Challenge Title":"Spend ANY Energy",
        "HexColor": 0x9431fd,
        "Image URL": "https://swgoh.wiki/images/4/4e/Game-Icon-Conquest_Energy.png",
        "Before Guild Reset": ":zap: Spend Light Side Energy\n:octagonal_sign: STOP spending all other energy\n:bulb: Save energy for tomorrow's activity\n:coin: Saving can net 800+ Guild Tokens",
        "After Guild Reset": ":money_with_wings: Spend ALL Energy\n:checkered_flag: 2400 is the Goal\n:arrows_counterclockwise: This is a great day for doing refreshes on all energy\n:bulb: Spend 2-3 refreshes on Ship and Mod Energy",
        "Footer": ""
    },
    "Wednesday": {
        "Challenge Title":"Hard Battles",
        "HexColor": 0xb9b9b9,
        "Image URL": "https://swgoh.wiki/images/thumb/b/bd/Unit-Ship-Imperial_TIE_Bomber.png/370px-Unit-Ship-Imperial_TIE_Bomber.png",
        "Before Guild Reset": ":money_with_wings: Finish spending ALL Energy to 2400\n:bulb: Spend Normal energy early and then save for Hard Battles Activity\n:warning: Watch your Guild's Tier so you don't spend unnecessarily",
        "After Guild Reset": ":tools: Do Hard Nodes for Light and Dark Side\n:checkered_flag: 4 refreshes is the Goal\n:no_entry_sign: Do NOT do your Daily Challenges after Personal Reset",
        "Footer": "Be aware of when your personal reset is so that you can use challenges from both days that the next activity covers"
    },
    "Thursday": {
        "Challenge Title":"Daily Challenges",
        "HexColor": 0x30e71b,
        "Image URL": "https://swgoh.wiki/images/f/f8/Game-Icon-Sim_Ticket.png",
        "Before Guild Reset": ":tools: Finish Hard Battles activity\n:warning: Save Daily Challenges for Next Activity",
        "After Guild Reset": ":gift: Do Daily Challenges\n:checkered_flag: 20 Challenges is the Goal\n:coin: 20 Challenges gets you 300+ tokens at Tier 7\n:bookmark_tabs: 8 Challenges and 2 Fleet Challenges",
        "Footer": "Be aware of when your personal reset is so that you can use challenges from both days that this activity covers"
    },
    "Friday": {
        "Challenge Title":"Spend Dark Side Energy",
        "HexColor": 0xdb0b31,
        "Image URL": "https://swgoh.wiki/images/b/ba/Game-Icon-Energy.png",
        "Before Guild Reset": ":gift: Make sure you finished your Daily Challenges\n:zap: Save Normal Energy for Dark Side Activity",
        "After Guild Reset": ":zap: Spend Energy on Dark Side nodes\n:checkered_flag: 4 refreshes is the Goal",
        "Footer": "Be aware of when your personal reset is so that you can use PvP attempts from both days that the next activity covers"
    },
    "Saturday": {
        "Challenge Title":"Squad Arena PvP Attempts",
        "HexColor": 0x6a6969,
        "Image URL": "https://swgoh.wiki/images/0/0d/Game-Icon-Squad_Arena_Token.png",
        "Before Guild Reset": ":zap: Spend Dark Side Energy\n:no_entry: Save Squad Arena PvP Battles",
        "After Guild Reset": ":crossed_swords: Squad Arena PvP Battles\n:checkered_flag: 10 is the Goal",
        "Footer": "Be aware of when your personal reset is so that you can use PvP attempts from both days that this activity covers"
    }
}

mod_primary_stats = {
    "Circle": ["Health", "Protection"],
    "Arrow": ["Speed", "Accuracy", "Critical Avoidance", "Health", "Protection", "Offense", "Defense"],
    "Triangle": ["Critical Chance", "Critical Damage", "Health", "Protection", "Offense", "Defense"],
    "Cross": ["Tenacity", "Potency", "Health", "Protection", "Offense", "Defense"]
}
# endregion

# region Helper Functions
# Function to retrieve the activity message for the given day
def get_activity_message(day, personalreset, next_reset_time_str = None, next_personal_reset_time_str = None):
    next_day = list(activity_messages.keys())[(list(activity_messages.keys()).index(day) + 1) % len(activity_messages)]
    if personalreset:
        activity_message = discord.Embed(title=f"{day} Personal Prep for {activity_messages[day]['Challenge Title']}", color=activity_messages[day]['HexColor'], url="https://swgoh.wiki/wiki/Guild_Activities")

        activity_message.add_field(name="Before Guild Reset Instructions", value=f"{activity_messages[day]['Before Guild Reset']}", inline=False)

        activity_message.add_field(name="After Guild Reset Instructions", value=f"{activity_messages[day]['After Guild Reset']}", inline=False)
    else:
        activity_message = discord.Embed(title=f"{day} {activity_messages[day]['Challenge Title']}", color=activity_messages[day]['HexColor'], url="https://swgoh.wiki/wiki/Guild_Activities")

        activity_message.add_field(name=f"{activity_messages[day]['Challenge Title']}", value=f"{activity_messages[day]['After Guild Reset']}", inline=False)

        activity_message.add_field(name=f"Preparation for {activity_messages[next_day]['Challenge Title']}", value=f"{activity_messages[next_day]['Before Guild Reset']}", inline=False)    
    
    # Add thumbnail
    activity_message.set_thumbnail(url=activity_messages[day]['Image URL'])

    # Add reset times
    if next_reset_time_str != None:
        activity_message.add_field(name="Next reset time:", value=f":clock1: {next_reset_time_str}")
    if next_personal_reset_time_str != None:
        activity_message.add_field(name="Next personal reset time:", value=f":clock6: {next_personal_reset_time_str}")
    
    # Add Footer if not empty
    if activity_messages[day]['Footer'] != None:
        activity_message.set_footer(text=activity_messages[day]['Footer'])

    return activity_message

# Function to save guild reset times into JSON file
def save_guild_reset_times():
    with open("guild_reset_times.json", "w") as file:
        json.dump(guild_reset_times, file)

# Function to save guild reset times into JSON file
def save_personal_reset_times():
    with open("personal_reset_times.json", "w") as file:
        json.dump(personal_reset_times, file)

def save_ally_code_tracking():
    with open("ally_code_tracking.json", "w") as file:
        json.dump(ally_code_tracking, file)

def save_channels():
    with open("channels.json", "w") as file:
        json.dump(channels, file)

        
# Fetch the list of valid timezones
valid_timezones = list(pytz.all_timezones)

# Function to provide hour options based on the selected time format
async def get_hour_options(ctx: discord.AutocompleteContext):
    time_format = ctx.options["timeformat"]
    text = ctx.value
    if time_format == 'Military':
        return [str(i) for i in range(0, 24) if str(i).startswith(text)]
    else:
        return [str(i) for i in range(1, 13) if str(i).startswith(text)]
    
async def get_valid_timezones(ctx: discord.AutocompleteContext):
    text = ctx.value
    filtered_timezones = [timezone for timezone in valid_timezones if text.lower() in timezone.lower()]
    if len(filtered_timezones) > 25:
        return filtered_timezones[:25]
    else:
        return filtered_timezones
    
async def unsubscribe(ctx: discord.ApplicationContext):
    # Clear the entry for the guild
    guild_reset_times[str(ctx.guild_id)] = {}
    
    save_guild_reset_times()
    await ctx.respond(f"User has been unsubscribed successfully.")

# Function to calculate the next epoch time for the specified reset hour
def calculate_next_reset_epoch(resethour, timeformat, timezone, dst, today, personal = False):
    resetmin = "00" if personal else RESET_MINUTE
    reset_time_str = f"{resethour}:" + resetmin + ("" if timeformat == FORMAT24 else " " + timeformat)
    reset_time_format = "%H:%M" if timeformat == FORMAT24 else "%I:%M %p"
    reset_time = datetime.strptime(reset_time_str, reset_time_format)
    
    # Adds Timezone information to the object
    reset_time = reset_time.replace(tzinfo=ZoneInfo(timezone))

    # If the guild's reset time was set during DST, check if DST is currently in effect
    current_time = datetime.now(ZoneInfo(timezone))
    is_currently_dst = current_time.dst() != timedelta(0)
    if dst and not is_currently_dst:
        reset_time -= timedelta(hours=1)
    elif not dst and is_currently_dst:
        reset_time += timedelta(hours=1)
    
    now = datetime.now(ZoneInfo(timezone))
    next_reset_time = reset_time.replace(year=now.year, month=now.month, day=now.day)
    if today != True and next_reset_time <= now:
        next_reset_time += timedelta(days=1)
    return next_reset_time

def fetch_pvp_ranks(ally_code: str):
    url = 'http://localhost:5678/playerArena'
    payload = {
        "payload": {
            "allyCode": ally_code
        }
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        pvp_profile = response.json().get('pvpProfile', [])
        name = response.json().get('name', "")
        ranks = {entry['tab']: entry['rank'] for entry in pvp_profile}
        return ranks, name
    else:
        print("Failed to fetch PvP ranks. Status code:", response.status_code)
        return None
    
def display_rank_changes(current_ranks):
    global PREVIOUS_RANKS  # Use the global variable
    messages = []

    if PREVIOUS_RANKS is not None and current_ranks is not None:
        if 1 in PREVIOUS_RANKS and 1 in current_ranks:
            squad_change = PREVIOUS_RANKS[1] - current_ranks[1]
            if squad_change != 0:  # Check if there's a change
                squad_emoji = ":chart_with_upwards_trend:" if squad_change > 0 else ":chart_with_downwards_trend:"
                squad_color = 0x008000 if squad_change > 0 else 0xFF0000
                squad_rank_message = discord.Embed(title=f'Squad Arena Logs', description=f"Rank {PREVIOUS_RANKS[1]} to {current_ranks[1]} (Diff: {abs(squad_change)} {squad_emoji})", color=squad_color)
                messages.append(squad_rank_message)
        if 2 in PREVIOUS_RANKS and 2 in current_ranks:
            fleet_change = PREVIOUS_RANKS[2] - current_ranks[2]
            if fleet_change != 0:  # Check if there's a change
                fleet_emoji = ":chart_with_upwards_trend:" if fleet_change > 0 else ":chart_with_downwards_trend:"
                fleet_color = 0x008000 if fleet_change > 0 else 0xFF0000
                fleet_rank_message = discord.Embed(title="Fleet Arena Logs", description=f"Rank {PREVIOUS_RANKS[2]} to {current_ranks[2]} (Diff: {abs(fleet_change)} {fleet_emoji})", color=fleet_color)
                messages.append(fleet_rank_message)
        
        return messages
    return None

def display_rank_change(title, name, previous_rank, new_rank):
    if previous_rank is not None and new_rank is not None:
        change = previous_rank - new_rank
        if change != 0:  # Check if there's a change
            emoji = ":chart_with_upwards_trend:" if change > 0 else ":chart_with_downwards_trend:"
            color = 0x008000 if change > 0 else 0xFF0000
            return discord.Embed(title=title, description=f"{name}: Rank {previous_rank} to {new_rank} (Diff: {abs(change)} {emoji})", color=color)
    return None
        
async def get_ally_code(guild_name: str, player_name: str):
    guild_id, member_count = get_guild_id(guild_name)
    if guild_id:
        player_id = get_player_id_from_guild(guild_id, player_name)
        if player_id:
            ally_code = get_player_ally_code_by_id(player_id)
            if ally_code:
                return ally_code
    return None

def get_player_info(user_id, user_info, arena_type: str, getAll: bool):
    arena_tab_num = 2 if arena_type == "fleetarena" else 1
    ally_code = user_info.get("ally_code")
    name = ""
    try:
        current_ranks, name = fetch_pvp_ranks(ally_code)
    except TypeError as e:
        print(f"Error fetching PvP ranks for ally code {ally_code}: {e}")

    player_info_list = []
    if current_ranks is not None:
        # Compare current ranks with stored ranks
        if user_info.get(arena_type, {}).get("rank") != current_ranks[arena_tab_num] or getAll:
            previous_rank = ally_code_tracking[user_id][arena_type].get("previous_rank", ally_code_tracking[user_id][arena_type]["rank"]) if getAll else ally_code_tracking[user_id][arena_type]["rank"]
            # Update stored ranks
            ally_code_tracking[user_id][arena_type]["rank"] = current_ranks[arena_tab_num]
            ally_code_tracking[user_id][arena_type]["previous_rank"] = previous_rank
            
            # Save the updated settings into the JSON file
            save_ally_code_tracking()

            player_info = {
                    "name": name,
                    "rank": current_ranks[arena_tab_num],  # Current rank
                    "previous_rank": previous_rank  # Previous rank
            }
            player_info_list.append(player_info)

    for opponent in user_info.get(arena_type, {}).get("opponent_rank_tracking", []):
            try:
                opponent_current_ranks, opponent_name = fetch_pvp_ranks(opponent["ally_code"])
            except TypeError as e:
                print(f"Error fetching PvP ranks for opponent ally code {opponent['ally_code']}: {e}")

            if opponent_current_ranks is not None:
                if opponent["rank"] != opponent_current_ranks[arena_tab_num] or getAll:
                    opponent_previous_rank = opponent.get("previous_rank", opponent["rank"]) if getAll else opponent["rank"]
                    # Update opponent's stored rank
                    opponent["rank"] = opponent_current_ranks[arena_tab_num]
                    opponent["previous_rank"] = opponent_previous_rank
                    # Save the updated settings into the JSON file
                    save_ally_code_tracking()
                    
                    # add player to list for generating messages
                    player_info = {
                        "name": opponent_name,
                        "rank": opponent_current_ranks[arena_tab_num],  # Current rank
                        "previous_rank": opponent_previous_rank  # Previous rank
                    }
                    player_info_list.append(player_info)

    return player_info_list, name

def get_rank_table(name, arena_string, sorted_player_info_list):
    # Prepare the header of the table
    # blank_line = "`{:<6} {:<16} {:<6}`".format("","","")
    # table = ["```{:<6} {:<16} {:<6}".format("","","")]
    table = ["```"]
    table.append("Rank   Name             Change")

    # Iterate over players and format each line
    for player in sorted_player_info_list:
        # Add fields for each player's rank, name, and change
        change = "+" if player["rank"] < player["previous_rank"] else ("-" if player["rank"] > player["previous_rank"] else "/")
        line = "{:<6} {:<16} {:<10}   ".format(player["rank"], player["name"], change)
        table.append(line)
    
    # table.append("{:<6} {:<16} {:<6}```".format("","",""))

    table.append("```")
    rank_table = discord.Embed(title=f"{name}'s {arena_string}", color=0xFFD700, description="\n".join(table))
    return rank_table

async def send_arena_monitoring_messages(user_id, user_info, arena_type: str):
    arena_string = "Fleet Arena" if arena_type == "fleetarena" else "Squad Arena"
    if user_info.get(arena_type, {}) and user_info.get(arena_type, {}).get("enabled") == True:
        player_info_list, name = get_player_info(user_id, user_info, arena_type, False)
        messages_to_send = []
        
        # Order the list of players by rank
        sorted_player_info_list = sorted(player_info_list, key=lambda x: x["rank"])

        # Determine how many players' ranks changed
        num_rank_changes = sum(1 for player in sorted_player_info_list if player["rank"] != player["previous_rank"])

        # Create a message based on the number of rank changes
        if num_rank_changes == 1:
            # Send message about rank change and append it to the list
            for player in sorted_player_info_list:
                if player["rank"] != player["previous_rank"]:
                    message = display_rank_change(f"{name}'s {arena_string}", player["name"], player["previous_rank"],  player["rank"])
                    if message is not None:
                        messages_to_send.append(message)
        elif num_rank_changes > 1:
            # Create an embedded card
            activity_message = get_rank_table(name, arena_string, sorted_player_info_list)
            messages_to_send.append(activity_message)

        # section for sending the actual messages
        if user_info.get(arena_type, {}).get("guild_id") and user_info.get(arena_type, {}).get("channel_id"):
            guild_id = user_info[arena_type]["guild_id"]
            channel_id = user_info[arena_type]["channel_id"]
            guild = bot.get_guild(int(guild_id))
            if guild:
                channel = guild.get_channel(int(channel_id))
                for message in messages_to_send:
                    try:
                        await channel.send(embed=message)
                    except DiscordServerError as e:
                        print(f"Error sending discord message to channel {channel.name}: {e}")
    return

# endregion

# region Slash Commands
# region Acitivty Commands
@bot.slash_command(
    name="activity",
    description="Prints today's activity message",
)
@option(
    "showall",
    description="Show entire week of activities"
)
@option(
    "day",
    description="Choose a day of the week",
    required=False,
    choices=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
)
@option(
    "personalreset",
    description="Show instructions for what to do at your personal reset"
)
async def activity(ctx: discord.ApplicationContext, showall: bool = False, day: str = None, personalreset: bool = False):
    if day:
        requested_day = day
    elif showall:
        # If showall parameter is True, retrieve and display activity messages for all days
        for day in activity_messages.keys():
            await ctx.respond(embed=get_activity_message(day, personalreset))
        return
    else:
        # If no specific day is provided, default to today
        requested_day = datetime.now().strftime("%A")
    
    next_reset_time_str = None
    next_personal_reset_time_str = None
    # Try to grab the user's next personal reset time
    if ctx.user.id != None:
        if str(ctx.user.id) in personal_reset_times:
            user = personal_reset_times[str(ctx.user.id)]
            if user != None and user != {}:
                now = datetime.now(ZoneInfo(user["timezone"]))
                next_personal_reset_datetime = calculate_next_reset_epoch(user["resethour"], user["timeformat"], user["timezone"], user["dst"], False, True)
                if now.day < next_personal_reset_datetime.day and requested_day == now.strftime("%A"): # if their reset time is tomorrow and the requested day shows today
                    tomorrow = now + timedelta(days=1)
                    requested_day = tomorrow.strftime("%A")
                next_personal_reset_time_str = f"<t:{int(next_personal_reset_datetime.timestamp())}>"
    # If the context is from a server then get the servers reset time
    if ctx.guild_id != None:
        if str(ctx.guild_id) in guild_reset_times:
            guildinfo = guild_reset_times[str(ctx.guild_id)]
            if guildinfo != None and guildinfo != {}:
                next_reset_datetime = calculate_next_reset_epoch(guildinfo["resethour"], guildinfo["timeformat"], guildinfo["timezone"], guildinfo["dst"], False)
                next_reset_time_str = f"<t:{int(next_reset_datetime.timestamp())}>"
    # If it came from a DM, then look up the guildid and see if it has a registered reset time
    elif user["guildid"] != None and user["guildid"] != {}:
        if str(user["guildid"]) in guild_reset_times:
            guildinfo = guild_reset_times[str(user["guildid"])]
            if guildinfo != None and guildinfo != {}:
                next_reset_datetime = calculate_next_reset_epoch(guildinfo["resethour"], guildinfo["timeformat"], guildinfo["timezone"], guildinfo["dst"], False)
                next_reset_time_str = f"<t:{int(next_reset_datetime.timestamp())}>"
    
    activity_embed = get_activity_message(requested_day, personalreset, next_reset_time_str, next_personal_reset_time_str)
    
    # Send the activity message
    await ctx.respond(embed=activity_embed)

@bot.slash_command(
    name="register",
    description="Register the guild's reset time to send the daily message",
)
@option(
    "guildname",
    description="Name of guild that this channel is for",
    required=True
)
@option(
    "timezone",
    description="Choose a valid timezone (start typing to filter)",
    required=True,
    autocomplete=get_valid_timezones
)
@option(
    "timeformat",
    description="This allows for 0-23 time on the next param or 1-12",
    required=True,
    choices=[FORMAT24, "AM", "PM"]
)
@option(
    "resethour",
    description="Guild resets at this hour and 30 minutes",
    required=True,
    autocomplete=get_hour_options
)
async def register(ctx: discord.ApplicationContext, guildname: str, timezone: str, timeformat: str, resethour: str):
    if not ctx.author.guild_permissions.administrator:
        admin_message = discord.Embed(title="Only an admin may run this command", color=0xff0000)
        await ctx.respond(embed=admin_message)
        return
    # Update the reset time for the guild in the JSON file
    # I could allow one server to have multiple guild notifications but for now its based off the discord server id (ctx.guild_id)
    current_time = datetime.now(pytz.timezone(timezone))
    dst = current_time.dst() != timedelta(0)
    guild_reset_times[str(ctx.guild_id)] = { 
        "timezone": timezone,
        "timeformat": timeformat,
        "resethour": resethour,
        "dst": dst,
        "channelid": ctx.channel_id,
        "guildname": guildname
    }

    # Calculate the next reset epoch time
    next_reset_epoch = calculate_next_reset_epoch(resethour, timeformat, timezone, dst, False)
    next_reset_time_str = f"<t:{int(next_reset_epoch.timestamp())}>"
    
    # Save the guild reset times into the JSON file
    save_guild_reset_times()
    await ctx.respond(f"Guild reset time has been registered successfully! Next reset time: {next_reset_time_str}")

@bot.slash_command(
    name="unregister",
    description="Unregister the guild's reset time for sending the daily message"
)
async def unregister(ctx: discord.ApplicationContext):
    # Clear the entry for the guild
    if not ctx.author.guild_permissions.administrator:
        admin_message = discord.Embed(title="Only an admin may run this command", color=0xff0000)
        await ctx.respond(embed=admin_message)
        return
    guild_reset_times[str(ctx.guild_id)] = {}
    print(f"Unregistered {ctx.guild_id}")
    
    save_guild_reset_times()
    await ctx.respond(f"Guild has been unregistered successfully.")

@bot.slash_command(
    name="subscribe",
    description="Subscribe to an automated DM with activity instructions at your reset time",
)
@option(
    "timezone",
    description="Choose a valid timezone (start typing to filter)",
    required=True,
    autocomplete=get_valid_timezones
)
@option(
    "timeformat",
    description="This allows for 0-23 time on the next param or 1-12",
    required=True,
    choices=[FORMAT24, "AM", "PM"]
)
@option(
    "resethour",
    description="This is the time your personal reset happens so that you know what to do with your energy and such",
    required=True,
    autocomplete=get_hour_options
)
async def subscribe(ctx: discord.ApplicationContext, timezone: str, timeformat: str, resethour: str):
    confirmation_message = discord.Embed(title="A DM will be sent to you shortly", color=0x00ff00)
    await ctx.respond(embed=confirmation_message)
    # Update the reset time for the user in the JSON file
    current_time = datetime.now(pytz.timezone(timezone))
    dst = current_time.dst() != timedelta(0)
    personal_reset_times[str(ctx.user.id)] = { 
        "timezone": timezone,
        "timeformat": timeformat,
        "resethour": resethour,
        "dst": dst,
        "channelid": ctx.channel_id,
        "guildid": ctx.guild_id
    }

    # Calculate the next reset epoch time
    next_reset_epoch = calculate_next_reset_epoch(resethour, timeformat, timezone, dst, False, True)
    next_reset_time_str = f"<t:{int(next_reset_epoch.timestamp())}>"
    
    # Save the guild reset times into the JSON file
    save_personal_reset_times()
    user = await bot.fetch_user(ctx.user.id)
    await user.send(f"Personal reset time has been subscribed successfully! Next reset time: {next_reset_time_str}")

@bot.slash_command(
    name="unsubscribe",
    description="Unsubscribe the user's reset time for sending the daily message",
)
# endregion

# region Utility Commands
@bot.slash_command(
        name="search",
        description="Search for an ally code of a player given their guild and name"
)
@option(
    "guild_name",
    description="The exact name of their current guild.",
    required=True
)
@option(
    "player_name",
    description="Their exact player name.",
    required=True
)
async def search(ctx: discord.ApplicationContext, guild_name: str, player_name: str):
    await ctx.defer()

    ally_code = await get_ally_code(guild_name, player_name)
    if ally_code:
        await ctx.respond(f"Ally code for player {player_name}: {ally_code}")
    else:
        await ctx.respond("Failed to retrieve player's ally code.")

@bot.slash_command(
        name="monitor",
        description="Monitor channel's messages",
        guild_ids = ["618924061677846528", "1186439503183892580"]
)
async def monitor(ctx: discord.ApplicationContext):
    await ctx.defer()
    if ctx.channel_id not in channels:
        channels.append(ctx.channel_id)
        save_channels()

        await ctx.respond(f"Now monitoring messages for channel <#{ctx.channel_id}>")
    else:
        await ctx.respond(f"Messages are already being monitored for channel <#{ctx.channel_id}>")

@bot.slash_command(
        name="unmonitor",
        description="Unmonitor channel's messages",
        guild_ids = ["618924061677846528", "1186439503183892580"]
)
async def unmonitor(ctx: discord.ApplicationContext):
    await ctx.defer()

    if ctx.channel_id in channels:
        channels.remove(ctx.channel_id)
        save_channels()

        await ctx.respond(f"No longer monitoring messages for channel <#{ctx.channel_id}>")
    else:
        await ctx.respond(f"Messages were not being monitored for channel <#{ctx.channel_id}>")

def calculate_left_to_farm(shard_string):
    # calculate shards left to farm
    try:
        current_shards, out_of_shards = map(int, shard_string.split('/'))
    except ValueError:
        raise ValueError("Invalid format. The string should be in '##/##' format.")
    
    shards_needed = 330
    match int(out_of_shards):
        case 10 | 15:
            shards_needed = 320
        case 25:
            shards_needed = 305
        case 30 | 50: 
            shards_needed = 280
        case 65 | 80:
            shards_needed = 250
        case 85 | 145:
            shards_needed = 185
        case 100: 
            shards_needed = 100
        
    left_to_farm = int(shards_needed) - int(current_shards)
    return left_to_farm

def calculate_cantina_crystal_cost(refreshes):
    total_costs = [0, 100, 200, 300, 500, 700, 1100, 1500, 2300, 3100, 3900, 5500, 7100, 10300, 13500]
    
    if refreshes < 0 or refreshes >= len(total_costs):
        raise ValueError("Invalid number of refreshes")
    
    return total_costs[refreshes]

def calculate_normal_crystal_cost(refreshes):
    total_costs = [0, 50, 100, 150, 250, 350, 450, 650, 850, 1050, 1450, 1850, 2250, 3050, 3850, 4650]
    
    if refreshes < 0 or refreshes >= len(total_costs):
        raise ValueError("Invalid number of refreshes")
    
    return total_costs[refreshes]

def calculate_hard_node_refresh_crystal_cost(refreshes):
    costs = [25, 50, 100, 100, 200, 200, 400, 400, 900, 900, 1800, 1800, 1800, 3600]
    total_cost = 0

    for i in range(min(refreshes, len(costs))):
        total_cost += costs[i]

    return total_cost

def create_shard_embed(shard_string, farm_type, shard_drop, node_energy_cost):
    remaining_shards = calculate_left_to_farm(shard_string)
    
    # Basic daily shard gain based on farm type
    daily_shard_gain = 1 / 3 * shard_drop

    daily_energy_gain = {
        "Normal Energy": 375,
        "Cantina Energy": 165,
        "Fleet Energy": 285,
    }[farm_type]

    farm_url = {
        "Normal Energy": "https://swgoh.wiki/images/b/ba/Game-Icon-Energy.png",
        "Cantina Energy": "https://swgoh.wiki/images/4/4c/Game-Icon-Cantina_Energy.png",
        "Fleet Energy": "https://swgoh.wiki/images/3/3f/Game-Icon-Ship_Energy.png",
    }[farm_type]
    
    def calculate_daily_total_attempts(farm_type, daily_energy_gain, node_energy_cost, refreshes):
        energy_per_refresh = 120  # Assuming each refresh gives 120 energy

        if farm_type == "Cantina Energy":
            # attempts
            cantina_energy = refreshes * energy_per_refresh + daily_energy_gain
            attempts_per_day = cantina_energy / node_energy_cost
            
            #crystals
            crystal_cost = calculate_cantina_crystal_cost(refreshes)

        
        else: 
            attempts_per_day = 5 + (5 * refreshes) # hard node refreshes give 5 more attempts
            crystal_cost = calculate_hard_node_refresh_crystal_cost(refreshes)

            # calculate if more energy is needed than normal amount
            total_energy_needed = attempts_per_day * node_energy_cost
            if total_energy_needed > daily_energy_gain:
                extra_energy_needed = total_energy_needed - daily_energy_gain
                extra_energy_refreshes = (extra_energy_needed + energy_per_refresh - 1) // energy_per_refresh  # Ceiling division

                # I might want to seperate this out into another column in the future to be more precise about where the cost is coming from
                crystal_cost += calculate_normal_crystal_cost(extra_energy_refreshes)
        
        return attempts_per_day, crystal_cost

    def calculate_completion(farm_type, remaining_shards, daily_energy_gain, daily_shard_gain, refreshes):
        
        total_daily_attempts, crystal_cost = calculate_daily_total_attempts(farm_type, daily_energy_gain, node_energy_cost, refreshes)
        
        adjusted_daily_shard_gain = total_daily_attempts * daily_shard_gain
        
        days_to_complete = remaining_shards / adjusted_daily_shard_gain
        completion_date = datetime.now() + timedelta(days=days_to_complete)
        epoch_timestamp = int(completion_date.timestamp())
        
        return round(days_to_complete, 1), completion_date.strftime("%Y-%m-%d"), crystal_cost, epoch_timestamp
    
    embed = discord.Embed(title=f"Shard Farming Estimates", color=0x00ff00)
    embed.set_thumbnail(url=f"{farm_url}")  # Replace with actual URLs
    
    embed.add_field(name="Current Shards", value=f"{shard_string}", inline=True)
    embed.add_field(name="Shards Required", value=f"{remaining_shards}", inline=True)
    embed.add_field(name="-", value="", inline=False)
    embed.add_field(name="Shard Drop Rate", value=f"{shard_drop}", inline=True)
    embed.add_field(name="Energy Cost", value=f"{node_energy_cost}", inline=True)

    # No refresh
    days, date, _, epoch_timestamp = calculate_completion(farm_type, remaining_shards, daily_energy_gain, daily_shard_gain, 0)
    embed.add_field(name="No Refreshes", value=f"Days: {days} or <t:{epoch_timestamp}:R>\nCompletion: {date}", inline=False)
    # With refreshes
    for refreshes in [1, 2, 3]:
        days, date, crystals, epoch_timestamp = calculate_completion(farm_type, remaining_shards, daily_energy_gain, daily_shard_gain, refreshes)
        refresh_str = "Refresh" if refreshes == 1 else "Refreshes"
        embed.add_field(name=f"{refreshes} {refresh_str} per Day", value=f"Days: {days} or <t:{epoch_timestamp}:R>\nCompletion: {date}\nCrystal Cost: {crystals}", inline=False)
    
    return embed

@bot.slash_command(name="estimate_farm", description="Estimate farm for a toon", guild_ids=["618924061677846528"])
@option(
    "shard_count",
    description="Current shards \"##/##\" as seen ingame",
    required=True
)
@option(
    "farm_type",
    description="Where the farm is located",
    required=True,
    choices=[ 
        "Normal Energy",
        "Cantina Energy",
        "Fleet Energy"
    ]
)
@option(
    "drop_count",
    description="Non-accelerated / Accelerated",
    required=True,
    choices=[ 
        1, 2
    ]
)
@option(
    "energy_cost",
    description="Energy cost per attempt",
    required=True,
    choices=[ 
        8, 10, 12, 16, 20
    ]
)
async def estimate_farm(ctx: discord.ApplicationContext, shard_count: str, farm_type, drop_count: int, energy_cost: int):
    embed = create_shard_embed(shard_count, farm_type, int(drop_count), int(energy_cost))
    await ctx.respond(embed=embed)

# endregion

#region Mods Commands
@bot.slash_command(
    name="mods",
    description="Show mod information based on SWGOH.gg's aggregated mod data",
    guild_ids=["618924061677846528", "1186439503183892580"]
)
@option(
    "character",
    description="Name of Character to show recommended mods for",
    required=True,
    autocomplete=get_valid_mod_characters
)
async def mods(ctx: discord.ApplicationContext, character: str):
    mod_info = get_character_mod_info(character)

    if mod_info is None:
        ctx.respond("Please select a valid character within the character option.")
    
    output_image_path = "output_image.png"
    create_image_with_mods(output_image_path, mod_info["character_name"], mod_info["portrait_url"], mod_info["recommended_stats"], mod_info["mod_sets"])
    
    # Send the image as a response
    with open(output_image_path, 'rb') as image_file:
        await ctx.respond(file=discord.File(image_file, 'mod_info_image.png'))

async def primary_stat_autocomplete(ctx: discord.AutocompleteContext):
    mod_type = ctx.options.get("mod_type")
    if mod_type:
        return mod_primary_stats.get(mod_type, [])
    return []

@bot.slash_command(
    name="modsearch",
    description="Search for characters with specific mod recommendations",
    guild_ids=["618924061677846528", "1186439503183892580"]
)
@option(
    "mod_type",
    description="Select the mod type (Circle, Arrow, Triangle, or Cross)",
    required=True,
    choices=list(mod_primary_stats.keys())
)
@option(
    "primary_stat",
    description="Select the primary stat",
    required=True,
    autocomplete=primary_stat_autocomplete
)
@option(
    "mod_set",
    description="Select the Mod Set",
    required=True,
    choices=["Health","Defense","Critical Damage","Critical Chance","Tenacity","Offense","Potency","Speed"]
)
async def modsearch(ctx: discord.ApplicationContext, mod_type: str, primary_stat: str, mod_set):
    valid_stats = mod_primary_stats.get(mod_type, [])
    
    if primary_stat not in valid_stats:
        await ctx.respond(f"Invalid primary stat for {mod_type}. Please choose one of: {', '.join(valid_stats)}.")
        return
    
    matching_characters = find_characters_with_mod(mod_type, primary_stat, mod_set)
    
    if matching_characters:
        response_message = f"**Characters with {primary_stat} on {mod_type} with {mod_set}:**\n"
        await ctx.respond(response_message)
        response_message = ""
        character_limit = 2000  # Discord message character limit

        # Loop through the matching characters
        for character in matching_characters:
            # Add the character to the response message, each on a new line
            new_line = f"{character}\n"
            
            # Check if adding this line would exceed the character limit
            if len(response_message) + len(new_line) > character_limit:
                # If it would, send the current message and start a new one
                await ctx.respond(response_message)
                response_message = new_line
            else:
                # Otherwise, just add the new line to the response
                response_message += new_line

        # Send any remaining characters that didn't hit the limit
        if response_message:
            await ctx.respond(response_message)
    else:
        await ctx.respond(f"No characters found with {primary_stat} on {mod_type}.")



# endregion

# region PvP Tracking
# region Fleet Arena
# create Slash Command group with bot.create_group
fleetarena = bot.create_group("fleetarena", "Fleet Arena tracking", guild_ids=["618924061677846528", "1273871496145801317"])
@fleetarena.command(
    name="enable",
    description="Enable fleet arena rank monitoring",
)
@option(
    "ally_code",
    description="Add your ally code XXXXXXXXX",
    required=False
)
@option(
    "user",
    description="User that this will be enabled for",
    required=False
)
async def enable(ctx: discord.ApplicationContext, ally_code: str, user: discord.User):
    await ctx.defer()

    # Check if an ally code is provided as an option
    
    if user is not None:
        user_id = str(user.id)
    else:
        user_id = str(ctx.user.id)
    # Check if the user's ID already exists in the dictionary
    if user_id not in ally_code_tracking:
        # If not, create a new entry for the user
        ally_code_tracking[user_id] = {}

    if ally_code is not None:
        ally_code_tracking[user_id]["ally_code"] = ally_code
    else:
        # Check if the user already has an ally code registered
        if ally_code_tracking.get(user_id) and ally_code_tracking[user_id].get("ally_code"):
            ally_code = ally_code_tracking[user_id]["ally_code"]
        else:
            await ctx.respond("Please /register your ally code...")
            return

    ranks_result, name = fetch_pvp_ranks(ally_code)

    fleetarena_settings = {
        "guild_id": ctx.guild_id,
        "channel_id": ctx.channel_id,
        "enabled": True,
        "rank": ranks_result[2],
        "opponent_rank_tracking": []  # Initialize empty list for tracking
    }

    # Update the fleet arena monitoring settings for the user in the JSON file
    ally_code_tracking[user_id]["fleetarena"] = fleetarena_settings
    
    # Save the updated settings into the JSON file
    save_ally_code_tracking()

    await ctx.respond(f'Fleet arena monitoring has been enabled successfully for `{name}` at Rank `{ranks_result[2]}` in channel <#{ctx.channel_id}>!')

@fleetarena.command(
    name="disable",
    description="Disable fleet arena rank monitoring",
)
async def disable_fleet_arena(ctx: discord.ApplicationContext):
    await ctx.defer()

    user_id = str(ctx.user.id)
    if user_id not in ally_code_tracking or "fleetarena" not in ally_code_tracking[user_id]:
        await ctx.respond("Fleet arena monitoring is not enabled for you.")
        return

    ally_code_tracking[user_id]["fleetarena"]["enabled"] = False
    save_ally_code_tracking()

    await ctx.respond("Fleet arena monitoring has been disabled successfully!")

@fleetarena.command(
    name="add",
    description="Add a player to fleet arena rank monitoring",
    guild_ids=["618924061677846528"]
)
@option(
    "guild_name",
    description="Guild name",
    required=True
)
@option(
    "player_name",
    description="Player name",
    required=True
)
async def add_player(ctx: discord.ApplicationContext, guild_name: str, player_name: str):
    await ctx.defer()

    # Get the ally code for the player
    ally_code = await get_ally_code(guild_name, player_name)
    if ally_code:
        # Retrieve the fleet rank from the player's PvP profile
        ranks_result, _ = fetch_pvp_ranks(ally_code)
        if ranks_result is not None:
            fleet_rank = ranks_result.get(2)
            if fleet_rank:
                user_id = str(ctx.user.id)
                opponent = {
                    "ally_code": ally_code,
                    "rank": fleet_rank,
                    "previous_rank": fleet_rank
                }

                # Update the opponent_rank_tracking for the user in the JSON file
                if user_id not in ally_code_tracking:
                    ally_code_tracking[user_id] = {}
                if "fleetarena" not in ally_code_tracking[user_id]:
                    ally_code_tracking[user_id]["fleetarena"] = {
                        "guild_id": ctx.guild_id,
                        "channel_id": ctx.channel_id,
                        "enabled": True,
                        "opponent_rank_tracking": []  # Initialize empty list for tracking
                    }
                ally_code_tracking[user_id]["fleetarena"]["opponent_rank_tracking"].append(opponent)

                # Save the updated settings into the JSON file
                save_ally_code_tracking()

                await ctx.respond(f'Player {player_name} from guild {guild_name} added successfully to fleet arena tracking at Rank {fleet_rank}!')
        else:
            await ctx.respond(f"Failed to retrieve fleet rank for player {player_name}.")
    else:
        await ctx.respond(f"Ally code not found for player {player_name} in guild {guild_name}.")
    return

@fleetarena.command(
    name="display",
    description="Display fleet arena ranks",
)
async def display_fleet_arena(ctx: discord.ApplicationContext):
    await ctx.defer()
    arena_type = "fleetarena"
    arena_string = "Fleet Arena"
    user_id = str(ctx.user.id)
    user_info = ally_code_tracking.get(user_id)
    if user_info is not None and user_info != {} and user_info.get("ally_code") is not None:
        if user_info.get(arena_type, {}) and user_info.get(arena_type, {}).get("enabled") == True:
            player_info_list, name = get_player_info(user_id, user_info, arena_type, True)
            
            # Order the list of players by rank
            sorted_player_info_list = sorted(player_info_list, key=lambda x: x["rank"])

            activity_message = get_rank_table(name, arena_string, sorted_player_info_list)
            if activity_message is not None:
                await ctx.respond(embed=activity_message)
            else:
                await ctx.respond(f"Could not find rank table for <@{user_id}>")
    else: 
        await ctx.respond(f"No user_info was found for <@{user_id}>")
    return  

# endregion

# region Squad Arena
# create Slash Command group with bot.create_group
squadarena = bot.create_group("squadarena", "Squad Arena tracking", guild_ids=["618924061677846528"])
@squadarena.command(
    name="enable",
    description="Enable squad arena rank monitoring",
    guild_ids=["618924061677846528"]
)
@option(
    "ally_code",
    description="Add your ally code XXXXXXXXX",
    required=False
)
async def enable(ctx: discord.ApplicationContext, ally_code: str):
    await ctx.defer()

    # Check if an ally code is provided as an option
    
    user_id = str(ctx.user.id)
    # Check if the user's ID already exists in the dictionary
    if user_id not in ally_code_tracking:
        # If not, create a new entry for the user
        ally_code_tracking[user_id] = {}

    if ally_code is not None:
        ally_code_tracking[user_id]["ally_code"] = ally_code
    else:
        # Check if the user already has an ally code registered
        if ally_code_tracking.get(user_id) and ally_code_tracking[user_id].get("ally_code"):
            ally_code = ally_code_tracking[user_id]["ally_code"]
        else:
            await ctx.respond("Please /register your ally code...")
            return

    ranks_result, name = fetch_pvp_ranks(ally_code)

    squadarena_settings = {
        "guild_id": ctx.guild_id,
        "channel_id": ctx.channel_id,
        "enabled": True,
        "rank": ranks_result[1],
        "opponent_rank_tracking": []  # Initialize empty list for tracking
    }

    # Update the fleet arena monitoring settings for the user in the JSON file
    user_id = str(ctx.user.id)
    ally_code_tracking[user_id]["squadarena"] = squadarena_settings
    
    # Save the updated settings into the JSON file
    save_ally_code_tracking()

    await ctx.respond(f'Squad arena monitoring has been enabled successfully for `{name}` at Rank `{ranks_result[1]}`!')
    return

@squadarena.command(
    name="disable",
    description="Disable squad arena rank monitoring",
)
async def disable_squad_arena(ctx: discord.ApplicationContext):
    await ctx.defer()

    user_id = str(ctx.user.id)
    if user_id not in ally_code_tracking or "squadarena" not in ally_code_tracking[user_id]:
        await ctx.respond("Squad arena monitoring is not enabled for you.")
        return

    ally_code_tracking[user_id]["squadarena"]["enabled"] = False
    save_ally_code_tracking()

    await ctx.respond("Squad arena monitoring has been disabled successfully!")
# endregion
# endregion
# endregion

# region Looping Functions
# Task that runs every 30 minutes
@tasks.loop(minutes=30)
async def update_mod_data():
    check_and_update_mod_data()

@tasks.loop(minutes=1)
async def send_daily_message():
    for guild_id, reset_info in guild_reset_times.items():
        if reset_info != None and reset_info != {}:
            reset_hour = reset_info["resethour"]
            timezone = reset_info["timezone"]
            timeformat = reset_info["timeformat"]
            dst = reset_info["dst"]
            reset_datetime = calculate_next_reset_epoch(reset_hour, timeformat, timezone, dst, True)
            next_reset_time_str = f"<t:{int(reset_datetime.timestamp())}>"
            
            # this grabs the channel information to send the message
            guild = bot.get_guild(int(guild_id))
            if guild:
                channel_id = guild_reset_times[guild_id]["channelid"]
                channel = guild.get_channel(int(channel_id))
                # if channel:
                #     await channel.send(f"Testing: {next_reset_time_str}")
            current_epoch = datetime.now().timestamp()
            reset_epoch = reset_datetime.timestamp()
            if current_epoch >= reset_epoch and current_epoch < reset_epoch + 60: # this is the normal reset logic for each day
            # if current_epoch >= reset_epoch and (current_epoch - reset_epoch) % 3600 < 60: # this is an hourly tester
                if channel:
                    reset_datetime += timedelta(days=1) # this will show what the next reset time is 
                    next_reset_time_str = f"<t:{int(reset_datetime.timestamp())}>" 
                    day = datetime.now().strftime("%A")
                    await channel.send(embed=get_activity_message(day, False, next_reset_time_str))

@tasks.loop(minutes=1)
async def send_daily_personal_message():
    for user_id, user_info in personal_reset_times.items():
        if user_info != None and user_info != {}:
            user_reset_hour = user_info["resethour"]
            user_timezone = user_info["timezone"]
            user_timeformat = user_info["timeformat"]
            guildid = user_info["guildid"]
            dst = user_info["dst"]
            reset_datetime = calculate_next_reset_epoch(user_reset_hour, user_timeformat, user_timezone, dst, True, True)
            next_reset_time_str = f"<t:{int(reset_datetime.timestamp())}>"

            # Check the guildid to see if we have its reset time to add to the card
            next_guild_reset_time_str = None
            if str(guildid) in guild_reset_times:
                guildinfo = guild_reset_times[str(guildid)]
                if guildinfo != None and guildinfo != {}:
                    guild_reset_hour = guildinfo["resethour"]
                    guild_timezone = guildinfo["timezone"]
                    guild_timeformat = guildinfo["timeformat"]
                    guild_dst = guildinfo["dst"]
                    guild_reset_datetime = calculate_next_reset_epoch(guild_reset_hour, guild_timeformat, guild_timezone, guild_dst, False) # Grab tomorrows reset time
                    next_guild_reset_time_str = f"<t:{int(guild_reset_datetime.timestamp())}>"
            
            # this grabs the user information to send the message
            user = await bot.fetch_user(int(user_id))
            now = datetime.now(ZoneInfo(user_timezone))
            current_epoch = now.timestamp()
            reset_epoch = reset_datetime.timestamp()
            if current_epoch >= reset_epoch and current_epoch < reset_epoch + 60: # this is the normal reset logic for each day
            # if current_epoch >= reset_epoch and (current_epoch - reset_epoch) % 3600 < 60: # this is an hourly tester
                if user:
                    reset_datetime += timedelta(days=1) # this will show what the next reset time is 
                    next_reset_time_str = f"<t:{int(reset_datetime.timestamp())}>"
                    # need to grab the next day if the reset time is before midnight
                    day = now
                    if now.hour >= 1:
                        day += timedelta(days=1)
                    
                    await user.send(embed=get_activity_message(day.strftime("%A"), True, next_guild_reset_time_str, next_reset_time_str))

@tasks.loop(minutes=1)
async def check_pvp_ranks():   
    for user_id, user_info in ally_code_tracking.items():
        if user_info is not None and user_info != {} and user_info.get("ally_code") is not None:
            await send_arena_monitoring_messages(user_id, user_info, "fleetarena")
            await send_arena_monitoring_messages(user_id, user_info, "squadarena")

@update_mod_data.before_loop
async def before_update_mod_data():
    print("Checking and updating mod data...")
    await bot.wait_until_ready()
    print("Polling every 30 minutes to check and update mod data!")

@send_daily_message.before_loop
async def before_send_daily_message():
    print("Configuring automated Guild messages...")
    await bot.wait_until_ready()
    print("Polling every minute to send daily Guild messages!")

@send_daily_personal_message.before_loop
async def before_send_daily_personal_message():
    print("Configuring automated Personal messages...")
    await bot.wait_until_ready()
    print("Polling every minute to send daily Personal messages!")

@check_pvp_ranks.before_loop
async def before_check_pvp_ranks():
    print("Configuring automated PvP Rank Checking...")
    await bot.wait_until_ready()
    print("Polling every minute to check PvP ranks!")

# endregion

def parse_ticket_message(message, monitorAll: bool):
    # Regular expression pattern to match the expected format
    total_members_missed = 0
    total_tickets_missed = 0
    
    if monitorAll:
        pattern = r'\b\w+\s+\(.*(\d+).*/600\)'
        matches = re.findall(pattern, message)

        total_members_missed = len(matches)

        # Iterate over matches and calculate total and missing tickets
        for tickets in matches:
            if int(tickets) < 600:
                total_tickets_missed += 600 - int(tickets)
    else:
        pattern = r".*Below are the members that missed the 600 ticket mark. Discipline as you must!\n(.*)" # This hotbot message is customizable per guild settings
        
        # Search for the pattern in the message
        match = re.search(pattern, message, re.DOTALL)
        
        if match:
            # Get the list of members and their ticket counts
            member_lines = match.group(1).split('\n')
            # Initialize counters
            
            # Iterate over each member line
            for line in member_lines:
                # Extract member name and ticket count using regular expression
                member_match = re.match(r".*\s+\([\s,*]*(\d+)[\s,*]*/600\)", line)
                if member_match:
                    # Increment counters
                    total_members_missed += 1
                    total_tickets_missed += 600 - int(member_match.group(1))
        else:
            return None, None

    return total_members_missed, total_tickets_missed


@bot.event
async def on_message(message):
    if message.author == bot.user: # skip own messages
            return
    
    if message.channel.id in channels:
        total_members_missed, total_tickets_missed = parse_ticket_message(message.content, False)
        member_message = ""
        if total_members_missed is not None and total_members_missed > 0:
            # I also want to check if the guild that has monitoring enabled has a guild name in our json so I can check their members
            guildname = guild_reset_times[str(message.guild.id)]["guildname"]
            if guildname is not None:
                id, member_count = get_guild_id(guildname)
                if member_count is not None and member_count > 0:
                    total_missing = total_tickets_missed + (50 - member_count) * 600
                    member_message = f"\nTotal members in Guild: `{member_count}/50`\nTotal Tickets missing: `{total_missing}`\nGuild Tickets for day: **{30000-total_missing:,}**/30k"
            description = f"Total Members missing tickets: `{total_members_missed}`\nMember Tickets missing: `{total_tickets_missed}`{member_message}"
            response = discord.Embed(title="Ticket Summary", color=0xFF0000, description=description)
            await message.channel.send(embed=response)
    

# Run the bot
update_mod_data.start()
send_daily_message.start()
send_daily_personal_message.start()
check_pvp_ranks.start()
bot.run(BOT_TOKEN)