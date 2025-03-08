import asyncio
import discord
import os
import requests
import functions as F
from typing import Final, Optional
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Constants #
public_log = 1234227629557547029  # Change to you public bot log channel ID
private_log = 1234227628924207283  # Change to you private bot log channel ID


# Load Client token from environment variables
TOKEN: Final[str] = os.getenv("ELYSIUM_TOKEN")


# Declare intents
intents = discord.Intents.all()
intents.message_content = True

# Initialize the Client
Client = commands.Bot(command_prefix="!", intents=intents)


async def load():
    for filename in os.listdir("elysium-bot/cogs"):
        try:
            if filename.endswith("py"):
                await Client.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ {filename} Cog Loaded!")
        except Exception as e:
            print(f"❌ Failed to load Twitch Cog: {e}")


@Client.event
async def on_ready():

    channel1 = Client.get_channel(public_log)
    channel2 = Client.get_channel(private_log)

    try:
        synced = await Client.tree.sync()
        boot_msg = discord.Embed(
            title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
            description=f"**Status**: 🟢 Online\n**Synced Commands**: {len(synced)}",
        )
        if channel1:
            await channel1.send(embed=boot_msg)
        if channel2:
            await channel2.send(embed=boot_msg)
    except Exception as e:
        print(f"⚠️ An Error Occurred While Syncing Commands: {e}")


async def main():
    async with Client:
        await load()
        await Client.start(TOKEN)


# Run the Client
asyncio.run(main())
