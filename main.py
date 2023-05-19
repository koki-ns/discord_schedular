import discord
from discord.ext import tasks, commands

import asyncio
import re
import datetime
import editcalendar
import logging
import json

from cogs.schedular import Schedular

INITIAL_EXTENSIONS = [
    'cogs.schedular'
]

token_file = "discord_token.json"

with open(token_file) as f:
    d = json.load(f)
TOKEN = d["token"]

fmt = "%(asctime)s %(levelname)s %(name)s :%(message)s"
logging.basicConfig(filename='discord.log', level=logging.DEBUG, format=fmt)
#handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

async def load_extension():
    for cog in INITIAL_EXTENSIONS:
        await bot.load_extension(cog)

async def main():
    async with bot:
        await load_extension()
        await bot.start(TOKEN)
        
asyncio.run(main())
