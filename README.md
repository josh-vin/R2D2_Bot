# R2D2_Bot

`python -m venv venv` to create your Virtual Enrivonment
`venv\Scripts\activate` to activate the Virtual Environment

`pip install -r requirements.txt` to install all the packages needed


## To add the bot to a server
Two websites you will need:
1. https://guide.pycord.dev/getting-started/creating-your-first-bot
2. https://discord.com/developers/applications
 - Go to OAuth2 for your application
 - In the URL Generator click on `bot`
 - In Bot Permissions select `Send Messages`
 - Copy the link and give it to an admin of the server

## I Know
Having the DB be a json file is not very smart. But it was quick and easy for making this bot

## Commands can take a while to register
You can add this code to the decorator:

guild_ids=[GUILD_ID]

@bot.slash_command(
    name="notification",
    description="Set up an automated DM with activity instructions",
    guild_ids=[GUILD_ID]
)

This will make it register fast when you are wanting to test. 

It may take time for it to propagate to the other servers

## Reference to py-cord library
This is the website I find most useful when trying to do different things with Py-Cord

https://guide.pycord.dev/introduction