import discord
from discord import option
from discord.ext import tasks
from datetime import datetime, timedelta
import json
import pytz

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
        "Before Guild Reset": "Do your 5 Squad Arena PvP activity after your daily reset and before the Guild reset if possible Let your Cantina Energy accumulate, grab Bonus Cantina Energy as close to max collection time as possible to allow more time to accumulate before adding it on\n\n:white_check_mark: Spend all Normal Energy and 45 of the first Bonus Normal Energy\n:white_check_mark: Let the rest accumulate for tomorrow.",
        "After Guild Reset": "Immediately do Cantina Battles activity by spending all Cantina Energy and if able do 2 refreshes Spend only as much additional Normal Energy as you need to reach 600 Raid Tickets Doing 3 refreshes of Normal Energy at the end of the day some time before your daily reset can save you about 50 Crystals for the next Guild Activity This requires you to spend your Energy for this day early in the morning so it can be at 144 before the last Bonus Energy Then you would do the 3 refreshes after that."
    },
    "Monday": {
        "Challenge Title":"Spend Light Side Energy",
        "HexColor": 0xfdc331,
        "Image URL": "https://swgoh.wiki/images/b/ba/Game-Icon-Energy.png",
        "Before Guild Reset": "Finish off Cantina Battles activity by spending Cantina Energy Spend only as much Cantina Energy as you need to get to or over 480 on the guild activity Start letting it accumulate for Tuesday And like the previous message states, get your Normal Energy refreshes saved up for after Guild Reset.",
        "After Guild Reset": "Do Light Side activity by spending all Energy and if able do up to 3 refreshes Try to do this 2 and a half hours before Daily Activities Reset If you did not get Energy on Sunday for this you will need to do 2 additional refreshes to reach the goal Do not spend crystals on refreshing Hard Battles, do multiple Hard Battles or farm for Gear/Relic scrap mats."
    },
    "Tuesday": {
        "Challenge Title":"Spend ANY Energy",
        "HexColor": 0x9431fd,
        "Image URL": "https://swgoh.wiki/images/4/4e/Game-Icon-Conquest_Energy.png",
        "Before Guild Reset": "Finish off Light Side activity by spending Normal Energy This will require 3 refreshes if no Energy refreshes were done on Sunday and 2 refreshes if there were Only use Energy up to the 1400 mark and let the rest of it along with all other types of energy accumulate for the next activity.",
        "After Guild Reset": "Do Energy Battles activity by spending all Cantina Energy, + 1 refresh of Cantina Energy, and your Bonus Cantina Energy Spend all Ship Energy + 3 refreshes and Bonus Ship Energy Spend all Mod Energy + 2 refresh and Bonus Mod Energy."
    },
    "Wednesday": {
        "Challenge Title":"Hard Battles",
        "HexColor": 0xb9b9b9,
        "Image URL": "https://swgoh.wiki/images/thumb/b/bd/Unit-Ship-Imperial_TIE_Bomber.png/370px-Unit-Ship-Imperial_TIE_Bomber.png",
        "Before Guild Reset": "Spend your Normal Energy as early as possible and save all Bonus Normal Energy for the next activity If slightly off from 2400 use a little bit of Normal Energy Save some Hard Nodes if possible for the next activity.",
        "After Guild Reset": "Do Hard Battles activity by spending all Normal Energy on any Dark Side or Light Side Hard Battle You will need to do 4 refreshes if aiming for the goal."
    },
    "Thursday": {
        "Challenge Title":"Daily Challenges",
        "HexColor": 0x30e71b,
        "Image URL": "https://swgoh.wiki/images/f/f8/Game-Icon-Sim_Ticket.png",
        "Before Guild Reset": "Finish Hard Battles activity by spending all Energy on any Dark Side or Light Side Hard Battle You will need to do 4 refreshes if aiming for the goal **Save your Daily Challenges till after the Guild Reset tomorrow**",
        "After Guild Reset": "Do Daily Challenges by completing all 8 Challenges and 2 Fleet Challenges.",
        "Footer": "Be aware of when your personal reset is so that you can use attempts from both days that this activity covers"
    },
    "Friday": {
        "Challenge Title":"Spend Dark Side Energy",
        "HexColor": 0xdb0b31,
        "Image URL": "https://swgoh.wiki/images/b/ba/Game-Icon-Energy.png",
        "Before Guild Reset": "Do Daily Challenges after your daily reset by completing all 8 Challenges and 2 Fleet Challenges Save your Dark Side farming nodes till after the guild reset if possible.",
        "After Guild Reset": "Do Dark Side activity by spending all Energy on any Dark Side Battles You will need to do 4 refreshes if aiming for the goal."
    },
    "Saturday": {
        "Challenge Title":"Squad Arena PvP Attempts",
        "HexColor": 0x6a6969,
        "Image URL": "https://swgoh.wiki/images/0/0d/Game-Icon-Squad_Arena_Token.png",
        "Before Guild Reset": ":zap: Spend Dark Side Energy\n:bulb: 4 refreshes maximizes guild potential for highest tier\n:x: Save Squad Arena PvP Battles if possible",
        "After Guild Reset": ":crossed_swords: Squad Arena PvP Battles\n:bulb: 10 is the Max to shoot for",
        "Footer": "Be aware of when your personal reset is so that you can use attempts from both days that this activity covers"
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
        activity_message.add_field(name="Next reset time:", value=f"{next_reset_time_str}")
    if activity_messages[day]['Footer'] != None:
        activity_message.set_footer(text=activity_messages[day]['Footer'])

    return activity_message

# Define the activity command
@bot.slash_command(
    name="activity",
    description="Prints today's activity message",
    guild_ids=[618924061677846528]
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
    if ctx.guild_id != None:
        guildinfo = guild_reset_times[str(ctx.guild_id)]
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
    guild_ids=[618924061677846528]
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
    guild_ids=[618924061677846528]
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
    reset_time = pytz.timezone(timezone).localize(reset_time)
    now = datetime.now(pytz.utc)
    next_reset_time = reset_time.replace(year=now.year, month=now.month, day=now.day)
    if today != True and next_reset_time <= now:
        next_reset_time += timedelta(days=1)
    return int(next_reset_time.timestamp())

@tasks.loop(minutes=1)
async def send_daily_message():
    for guild_id, reset_info in guild_reset_times.items():
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
        # if current_epoch >= reset_epoch and current_epoch < reset_epoch + 60: # this is the normal reset logic for each day
        if current_epoch >= reset_epoch and (current_epoch - reset_epoch) % 3600 < 60: # this is an hourly tester
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
bot.run("MTIwNzkwMDI4MjA4ODg0OTU0OA.GLSXd9.sHWCgITQWgxizgxSX5IeNRiJFVutOP_gkBc5bg")

