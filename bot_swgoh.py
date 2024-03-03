import os
from dotenv import load_dotenv
import discord
from discord import option
from discord.ext import tasks
from datetime import datetime, timedelta
import json
import pytz
from zoneinfo import ZoneInfo

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# GLOBALS
RESET_MINUTE = "30" # ex. 10:{30} <-
FORMAT24 = "Military"
# Initialize the bot
bot = discord.Bot()

# Load guild reset times from JSON file on bot startup
try:
    with open("guild_reset_times.json", "r") as file:
        guild_reset_times = json.load(file)
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
        "Before Guild Reset": ":zap: Spend Cantina Energy\n:bulb: Check Guild Tier and make sure you've spent enough\n:bulb: Save for ANY energy Activity in 2 days\n:arrows_counterclockwise: Buy 3 Refreshes of Normal Energy for next Activity",
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


# Function to retrieve the activity message for the given day
def get_activity_message(day, personalreset, next_reset_time_str=None):
    if personalreset:
        activity_message = discord.Embed(title=f'{day} Personal Reset Guild Activity', color=activity_messages[day]['HexColor'], description=f"{activity_messages[day]['Challenge Title']}", url="https://swgoh.wiki/wiki/Guild_Activities")

        activity_message.add_field(name="Before Guild Reset Instructions", value=f"{activity_messages[day]['Before Guild Reset']}", inline=False)

        activity_message.add_field(name="After Guild Reset Instructions", value=f"{activity_messages[day]['After Guild Reset']}", inline=False)
    else:
        activity_message = discord.Embed(title=f'{day} Guild Activity', color=activity_messages[day]['HexColor'], description=f"{activity_messages[day]['Challenge Title']}", url="https://swgoh.wiki/wiki/Guild_Activities")

        activity_message.add_field(name="Today's Instructions", value=f"{activity_messages[day]['After Guild Reset']}", inline=False)

        next_day = list(activity_messages.keys())[(list(activity_messages.keys()).index(day) + 1) % len(activity_messages)]
        activity_message.add_field(name="Preparation for Tomorrow", value=f"{activity_messages[next_day]['Before Guild Reset']}", inline=False)    
    
    # Add thumbnail
    activity_message.set_thumbnail(url=activity_messages[day]['Image URL'])

    if next_reset_time_str != None:
        activity_message.add_field(name="Next reset time:", value=f":clock1: {next_reset_time_str} :clock2:")
    if activity_messages[day]['Footer'] != None:
        activity_message.set_footer(text=activity_messages[day]['Footer'])

    return activity_message

# Define the activity command
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
    
    # Retrieve the activity message for the requested day
    next_reset_time_str = None
    if ctx.guild_id != None:
        if str(ctx.guild_id) in guild_reset_times:
            guildinfo = guild_reset_times[str(ctx.guild_id)]
            if guildinfo != None and guildinfo != {}:
                next_reset_epoch = calculate_next_reset_epoch(guildinfo["resethour"], guildinfo["timeformat"], guildinfo["timezone"], False)
                next_reset_time_str = f"<t:{next_reset_epoch}>"
    
    activity_embed = get_activity_message(requested_day, personalreset, next_reset_time_str)
    
    # Send the activity message
    await ctx.respond(embed=activity_embed)

# Function to save guild reset times into JSON file
def save_guild_reset_times():
    with open("guild_reset_times.json", "w") as file:
        json.dump(guild_reset_times, file)


        
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
    filtered_timezones = [timezone for timezone in valid_timezones if timezone.startswith(text)]
    if len(filtered_timezones) > 25:
        return filtered_timezones[:25]
    else:
        return filtered_timezones

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
        admin_message = discord.Embed(title="Only an admin may run this command")
        await ctx.respond(embed=admin_message)
    # Update the reset time for the guild in the JSON file
    # I could allow one server to have multiple guild notifications but for now its based off the discord server id (ctx.guild_id)
    guild_reset_times[str(ctx.guild_id)] = { 
        "timezone": timezone,
        "timeformat": timeformat,
        "resethour": resethour,
        "channelid": ctx.channel_id,
        "guildname": guildname
    }

    # Calculate the next reset epoch time
    next_reset_epoch = calculate_next_reset_epoch(resethour, timeformat, timezone, False)
    next_reset_time_str = f"<t:{next_reset_epoch}>"
    
    # Save the guild reset times into the JSON file
    save_guild_reset_times()
    await ctx.respond(f"Guild reset time has been registered successfully! Next reset time: {next_reset_time_str}")

@bot.slash_command(
    name="unregister",
    description="Register the guild's reset time to send the daily message",
)
async def unregister(ctx: discord.ApplicationContext):
    # Clear the entry for the guild
    guild_reset_times[str(ctx.guild_id)] = {}
    
    save_guild_reset_times()
    await ctx.respond(f"Guild has been unregistered successfully.")

# Function to calculate the next epoch time for the specified reset hour
def calculate_next_reset_epoch(resethour, timeformat, timezone, today):
    reset_time_str = f"{resethour}:" + RESET_MINUTE + ("" if timeformat == FORMAT24 else " " + timeformat)
    reset_time_format = "%H:%M" if timeformat == FORMAT24 else "%I:%M %p"
    reset_time = datetime.strptime(reset_time_str, reset_time_format)
    
    # Adds Timezone information to the object
    reset_time = reset_time.replace(tzinfo=ZoneInfo(timezone))
    
    now = datetime.now(pytz.utc)
    next_reset_time = reset_time.replace(year=now.year, month=now.month, day=now.day)
    if today != True and next_reset_time <= now:
        next_reset_time += timedelta(days=1)
    return int(next_reset_time.timestamp())

@tasks.loop(minutes=1)
async def send_daily_message():
    for guild_id, reset_info in guild_reset_times.items():
        if reset_info != None and reset_info != {}:
            reset_hour = reset_info["resethour"]
            timezone = reset_info["timezone"]
            timeformat = reset_info["timeformat"]
            reset_epoch = calculate_next_reset_epoch(reset_hour, timeformat, timezone, True)
            next_reset_time_str = f"<t:{reset_epoch}>"
            
            # this grabs the channel information to send the message
            guild = bot.get_guild(int(guild_id))
            if guild:
                channel_id = guild_reset_times[guild_id]["channelid"]
                channel = guild.get_channel(int(channel_id))
                # if channel:
                #     await channel.send(f"Testing: {next_reset_time_str}")
            current_epoch = datetime.now().timestamp()
            if current_epoch >= reset_epoch and current_epoch < reset_epoch + 60: # this is the normal reset logic for each day
            # if current_epoch >= reset_epoch and (current_epoch - reset_epoch) % 3600 < 60: # this is an hourly tester
                print("Matched!")
                if channel:
                    next_reset_time_str = f"<t:{int(current_epoch)}>" # remove this for normal reset timestamp
                    day = datetime.now().strftime("%A")
                    await channel.send(embed=get_activity_message(day, False, next_reset_time_str))

@send_daily_message.before_loop
async def before_send_daily_message():
    print("Configuring automated messages...")
    await bot.wait_until_ready()
    print("Polling every minute to send daily messages!")

# Run the bot
send_daily_message.start()
bot.run(BOT_TOKEN)

