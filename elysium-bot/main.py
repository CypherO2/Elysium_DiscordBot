import asyncio
import discord
import os
import requests
import functions as F
from typing import Final
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Constants #
public_log = 1234227629557547029  # Change to you public bot log channel ID
private_log = 1234227628924207283  # Change to you private bot log channel ID
dev_id = 876876129368150018  # If you are hosting this bot, change this to your Discord UserID

# Datetime for Client startup tracking
start_time = datetime.now()

# Load Client token from environment variables
TOKEN: Final[str] = os.getenv("ELYSIUM_TOKEN")

# Declare intents
intents = discord.Intents.all()
intents.message_content = True

# Initialize the Client
Client = commands.Bot(command_prefix="!", intents=intents)


@Client.event
async def on_ready():
    try:
        await Client.load_extension("cogs.twitchcog")
        print("✅ Twitch Cog Loaded!")
    except Exception as e:
        print(f"❌ Failed to load Twitch Cog: {e}")

    channel1 = Client.get_channel(public_log)
    channel2 = Client.get_channel(private_log)

    try:
        synced = await Client.tree.sync()
        boot_msg = discord.Embed(
            title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
            description=f"**Status**: 🟢 Online\n**Synced Commands**: {len(synced)}",
            timestamp=start_time,
        )
        if channel1:
            await channel1.send(embed=boot_msg)
        if channel2:
            await channel2.send(embed=boot_msg)
    except Exception as e:
        print(f"⚠️ An Error Occurred While Syncing Commands: {e}")


@Client.tree.command(
    name="runtime", description="Shows how long the Client has been online."
)
async def runtime(interaction: discord.Interaction):
    now = datetime.now()
    time_elapsed = now - start_time
    await interaction.response.send_message(
        f"As of {now.strftime('%d/%m/%Y %H:%M:%S')},\nTime Elapsed: {time_elapsed}",
        ephemeral=True,
    )


@Client.tree.command(name="help", description="Shows the list of available commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**𝓔𝓵𝔂𝓼𝓲𝓾𝓶 - Help Centre**",
        description="Need help? Here is a list of commands available with this Client.",
        color=0x5A0C8A,
    )
    embed.add_field(
        name="Commands",
        value=f"""
        **/help** - Displays this help menu.
        **/runtime** - Shows how long the Client has been online.
        """,
        inline=False,
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)


@Client.tree.command(
    name="watchlist_add",
    description="Add a new streamer to the config file (use their name as is show in their twitch.tv link)",
)
@app_commands.describe(streamername="Who you are adding?")
async def watchlistadd(interaction: discord.Interaction, streamername: str):
    response = F.followstreamer(streamer=streamername)
    await interaction.response.send_message(response, ephemeral=True)


@Client.tree.command(
    name="watchlist_remove",
    description="Remove a streamer from the config file (use their name as is show in their twitch.tv link)",
)
@app_commands.describe(streamername="Who you are removing")
async def watchlistremove(interaction: discord.Interaction, streamername: str):
    response = F.unfollowstreamer(streamer=streamername)
    await interaction.response.send_message(response, ephemeral=True)


@Client.tree.command(
    name="shutdown", description="Stops the Client [Privileged Command]."
)
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id != dev_id:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    now = datetime.now()
    time_elapsed = now - start_time
    exit_msg = discord.Embed(
        title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
        description=f"**Status**: 🔴 Offline\n**Runtime**: {time_elapsed}",
        timestamp=now,
    )

    channel1 = Client.get_channel(public_log)
    channel2 = Client.get_channel(private_log)

    if channel1:
        await channel1.send(embed=exit_msg)
    if channel2:
        await channel2.send(embed=exit_msg)

    await interaction.response.send_message("Bot is shutting down...", ephemeral=True)
    await Client.close()


@Client.tree.command(
    name="startmaintainance",
    description="Stops the Client for Maintainance [Privileged Command].",
)
async def startmaintainance(interaction: discord.Interaction):
    if interaction.user.id != dev_id:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    now = datetime.now()
    time_elapsed = now - start_time
    exit_msg = discord.Embed(
        title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
        description=f"**Status**: 🔴 Offline for Maintainance\n**Runtime**: {time_elapsed}",
        timestamp=now,
    )

    channel1 = Client.get_channel(public_log)
    channel2 = Client.get_channel(private_log)

    if channel1:
        await channel1.send(embed=exit_msg)
    if channel2:
        await channel2.send(embed=exit_msg)

    await interaction.response.send_message("Bot is shutting down...", ephemeral=True)
    await Client.close()


# Run the Client
if __name__ == "__main__":
    Client.run(TOKEN)
