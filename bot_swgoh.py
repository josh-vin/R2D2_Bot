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

# region Setup
# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# GLOBALS
RESET_MINUTE = "30" # ex. 10:{30} <-
FORMAT24 = "Military"
PREVIOUS_RANKS = None

# Initialize the bot
bot = discord.Bot()

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
# endregion

# region Helper Functions
# Function to retrieve the activity message for the given day
def get_activity_message(day, personalreset, next_reset_time_str = None, next_personal_reset_time_str = None):
    next_day = list(activity_messages.keys())[(list(activity_messages.keys()).index(day) + 1) % len(activity_messages)]
    if personalreset:
        activity_message = discord.Embed(title=f"{day} Personal Prep for {activity_messages[next_day]['Challenge Title']}", color=activity_messages[day]['HexColor'], url="https://swgoh.wiki/wiki/Guild_Activities")

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
    
def display_rank_change(title, name, previous_rank, new_rank):
    if previous_rank is not None and new_rank is not None:
        change = previous_rank - new_rank
        if change != 0:  # Check if there's a change
            emoji = ":chart_with_upwards_trend:" if change > 0 else ":chart_with_downwards_trend:"
            color = 0x008000 if change > 0 else 0xFF0000
            return discord.Embed(title=title, description=f"{name}: Rank {previous_rank} to {new_rank} (Diff: {abs(change)} {emoji})", color=color)
        
async def get_ally_code(guild_name: str, player_name: str):
    guild_id = get_guild_id(guild_name)
    if guild_id:
        player_id = get_player_id_from_guild(guild_id, player_name)
        if player_id:
            ally_code = get_player_ally_code_by_id(player_id)
            if ally_code:
                return ally_code
    return None
            
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
# endregion

# region PvP Tracking
# region Fleet Arena
# create Slash Command group with bot.create_group
fleetarena = bot.create_group("fleetarena", "Fleet Arena tracking", guild_ids=["618924061677846528"])
@fleetarena.command(
    name="enable",
    description="Enable fleet arena rank monitoring",
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

    fleetarena_settings = {
        "guild_id": ctx.guild_id,
        "channel_id": ctx.channel_id,
        "enabled": True,
        "rank": ranks_result[2],
        "opponent_rank_tracking": []  # Initialize empty list for tracking
    }

    # Update the fleet arena monitoring settings for the user in the JSON file
    user_id = str(ctx.user.id)
    ally_code_tracking[user_id]["fleetarena"] = fleetarena_settings
    
    # Save the updated settings into the JSON file
    save_ally_code_tracking()

    await ctx.respond(f'Fleet arena monitoring has been enabled successfully for `{name}` at Rank `{ranks_result[2]}`!')

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
        fleet_rank = ranks_result.get(2)
        if fleet_rank:
            user_id = str(ctx.user.id)
            opponent = {
                "ally_code": ally_code,
                "rank": fleet_rank
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
            ally_code = user_info.get("ally_code")
            if user_info.get("fleetarena", {}) and user_info.get("fleetarena", {}).get("enabled") == True:
                current_ranks, name = fetch_pvp_ranks(ally_code)
                messages_to_send = []
                if current_ranks is not None:
                    # Compare current ranks with stored ranks
                    if user_info.get("fleetarena", {}).get("rank") != current_ranks[2]:
                        previous_rank = ally_code_tracking[user_id]["fleetarena"]["rank"]
                        # Update stored ranks
                        ally_code_tracking[user_id]["fleetarena"]["rank"] = current_ranks[2]
                        
                        # Save the updated settings into the JSON file
                        save_ally_code_tracking()
                        # Send message about rank change
                        message = display_rank_change(f"{name}'s Fleet Arena", name, previous_rank, current_ranks[2])
                        if message is not None:
                            messages_to_send.append(message)
                            # this grabs the channel information to send the message
                        # Compare current ranks with stored ranks for each opponent
                for opponent in user_info.get("fleetarena", {}).get("opponent_rank_tracking", []):
                    opponent_current_ranks, opponent_name = fetch_pvp_ranks(opponent["ally_code"])
                    if opponent_current_ranks is not None:
                        if opponent["rank"] != opponent_current_ranks[2]:
                            opponent_previous_rank = opponent["rank"]
                            # Update opponent's stored rank
                            opponent["rank"] = opponent_current_ranks[2]
                            
                            # Save the updated settings into the JSON file
                            save_ally_code_tracking()

                            # Send message about rank change and append it to the list
                            message = display_rank_change(f"{name}'s Fleet Arena", opponent_name, opponent_previous_rank, opponent_current_ranks[2])
                            if message is not None:
                                messages_to_send.append(message)

                if user_info.get("fleetarena", {}).get("guild_id") and user_info.get("fleetarena", {}).get("channel_id"):
                    guild_id = user_info["fleetarena"]["guild_id"]
                    channel_id = user_info["fleetarena"]["channel_id"]
                    guild = bot.get_guild(int(guild_id))
                    if guild:
                        channel = guild.get_channel(int(channel_id))
                        for message in messages_to_send:
                            await channel.send(embed=message)
            
            if user_info.get("squadarena", {}) and user_info.get("squadarena", {}).get("enabled") == True:
                current_ranks, name = fetch_pvp_ranks(ally_code)
                if current_ranks is not None:
                    # Compare current ranks with stored ranks
                    if user_info.get("squadarena", {}).get("rank") != current_ranks[1]:
                        previous_rank = ally_code_tracking[user_id]["squadarena"]["rank"]
                        # Update stored ranks
                        ally_code_tracking[user_id]["squadarena"]["rank"] = current_ranks[1]
                        
                        # Send message about rank change
                        message = display_rank_change(f'{name}\'s Squad Arena', name, previous_rank, current_ranks[1])
                        # Save the updated settings into the JSON file
                        save_ally_code_tracking()

                        if message is not None:
                            # this grabs the channel information to send the message
                            if user_info.get("squadarena", {}).get("guild_id") and user_info.get("squadarena", {}).get("channel_id"):
                                guild_id = user_info["squadarena"]["guild_id"]
                                channel_id = user_info["squadarena"]["channel_id"]
                                guild = bot.get_guild(int(guild_id))
                                if guild:
                                    channel = guild.get_channel(int(channel_id))
                                    await channel.send(embed=message)

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

# Run the bot
send_daily_message.start()
send_daily_personal_message.start()
check_pvp_ranks.start()
bot.run(BOT_TOKEN)