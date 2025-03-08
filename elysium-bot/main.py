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
bot_notifications = 1234227629352288275
public_log = 1234227629557547029  # Change to you public bot log channel ID
private_log = 1234227628924207283  # Change to you private bot log channel ID
dev_id = 876876129368150018  # If you are hosting this bot, change this to your Discord UserID
twcord_userid = (
    972663150455451689  # The ID of the person handling the bot's Twitch notifications.
)

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
        **/help** - Displays the help menu - contains a list of commands.
        **/runtime** - Shows how long the bot has been online.
        **/watchlist {'{action} {streamer_name}'}** - Allows for the editing and viewing of the streamer list.
        **/setlivemessage {'{message} {role}'}** - Allows for the creation of custom messages for stream notifications.
        **/setlivechannel {'{channel}'}** - Allows for the changing of the channel the bot sends notifications in.
        **/shutdown {'{reason}'}** - This command stops the bot (Authorised users only).
        **/suggestion {'{suggestion}'}** - This command allows for the user to send a suggestion for update to the bot.
        """,
        inline=False,
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)


@Client.tree.command(
    name="watchlist",
    description="Edit/ Show the list of Streamer",
)
@app_commands.describe(
    action="What do you want to do?",
    streamername="Who you are? (Not needed if your only viewing the list)",
)
async def watchlist(
    interaction: discord.Interaction, action: str, streamername: Optional[str]
):

    if interaction.user.id != twcord_userid:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return
    if action.lower() == "add":
        response = F.followstreamer(streamer=streamername)
        response = response.replace(", ", "\n")
        await interaction.response.send_message(response, ephemeral=True)
    elif action.lower() == "remove":
        response = F.unfollowstreamer(streamer=streamername)
        await interaction.response.send_message(response, ephemeral=True)
    elif action.lower() == "show":
        response = F.viewstreamers()
        # response = response.
        embed = discord.Embed(
            title="Streamer List [Twitch]",
            description="Here is the list of streamers your listening for.",
        )
        for streamer in response:
            embed.add_field(name=f"{streamer}", value="")
        await interaction.response.send_message(embed=embed, ephemeral=True)


@Client.tree.command(
    name="setlivechannel",
    description="Choose the channel you want to send the live notifications in.",
)
@app_commands.describe(channel="channel?")
async def setlivechannel(interaction: discord.Interaction, channel: str):
    if interaction.user.id != twcord_userid:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return
    response = F.changelivechannel(channel=channel)
    await interaction.response.send_message(response, ephemeral=True)


@Client.tree.command(
    name="setlivemessage",
    description="Set the message that shows when someone goes live.",
)
@app_commands.describe(message="Input your message here", mentioned="Who are you @ing?")
async def setlivemessage(
    interaction: discord.Interaction, message: str, mentioned: str
) -> None:
    if interaction.user.id != twcord_userid:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return
    response = F.changemessage(newmessage=message, mentions=mentioned)
    await interaction.response.send_message(response, ephemeral=True)


@Client.tree.command(
    name="shutdown", description="Stops the Client [Privileged Command]."
)
@app_commands.describe(reason="Why is the bot being shutdown?")
async def shutdown(interaction: discord.Interaction, reason: Optional[str]) -> None:
    if interaction.user.id != dev_id:
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    now = datetime.now()
    time_elapsed = now - start_time
    exit_msg = discord.Embed(
        title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
        description=f"**Status**: 🔴 Offline\n**Reason**: {reason}\n**Runtime**: {time_elapsed}",
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


@Client.tree.command(name="suggestion", description="send a suggestion for the bot")
@app_commands.describe(suggestion="What is your suggestion?")
async def suggest_command(interaction: discord.Interaction, suggestion: str):
    channel = Client.get_channel(bot_notifications)
    embed = discord.Embed(
        title="**Suggestion!**", description=f"{suggestion}", color=0x5A0C8A
    )
    await asyncio.gather(
        channel.send(embed=embed),
        interaction.response.send_message(
            f"Your suggestion has been registered!\n`Your Suggestion: {suggestion}`",
            ephemeral=True,
        ),
    )


# Run the Client
if __name__ == "__main__":
    Client.run(TOKEN)
