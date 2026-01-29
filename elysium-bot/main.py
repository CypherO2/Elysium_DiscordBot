import asyncio
import logging
import os
from typing import Final

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import get_bot_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

# Load config for channel IDs
try:
    bot_config = get_bot_config()
    public_log = bot_config.get("public_log")
    private_log = bot_config.get("private_log")

    if not public_log or not private_log:
        logger.warning("Public or private log channel IDs not found in config")
except Exception as e:
    logger.error(f"Error loading bot config: {e}")
    public_log = None
    private_log = None

# Load Client token from environment variables
TOKEN: Final[str] = os.getenv("ELYSIUM_TOKEN") or ""

if not TOKEN:
    logger.error("ELYSIUM_TOKEN not found in environment variables!")
    raise ValueError("Bot token is required. Please set ELYSIUM_TOKEN in .env file")


# Declare intents
intents = discord.Intents.all()
intents.message_content = True

# Initialize the Client
Client = commands.Bot(command_prefix="!", intents=intents)


async def load():
    """Load all cogs from the cogs directory."""
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")

    if not os.path.exists(cogs_dir):
        logger.error(f"Cogs directory not found: {cogs_dir}")
        return

    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog_name = filename[:-3]  # Remove .py extension
            try:
                await Client.load_extension(f"cogs.{cog_name}")
                logger.info(f"✅ {filename} Cog Loaded!")
            except commands.ExtensionError as e:
                logger.error(f"❌ Failed to load {filename} Cog: {e}")
            except Exception as e:
                logger.error(
                    f"❌ Unexpected error loading {filename} Cog: {e}", exc_info=True
                )


@Client.event
async def on_ready():
    """Event handler for when the bot is ready."""
    logger.info(f"Bot logged in as {Client.user} (ID: {Client.user.id})")

    channel1 = Client.get_channel(public_log) if public_log else None
    channel2 = Client.get_channel(private_log) if private_log else None

    try:
        synced = await Client.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")

        boot_msg = discord.Embed(
            title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
            description=f"**Status**: 🟢 Online\n**Synced Commands**: {len(synced)}",
        )

        if channel1:
            try:
                await channel1.send(embed=boot_msg)
            except discord.Forbidden:
                logger.warning(
                    f"No permission to send to public log channel {public_log}"
                )
            except Exception as e:
                logger.error(f"Error sending to public log channel: {e}")

        if channel2:
            try:
                await channel2.send(embed=boot_msg)
            except discord.Forbidden:
                logger.warning(
                    f"No permission to send to private log channel {private_log}"
                )
            except Exception as e:
                logger.error(f"Error sending to private log channel: {e}")
    except discord.HTTPException as e:
        logger.error(f"Discord API error while syncing commands: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in on_ready: {e}", exc_info=True)


async def main():
    async with Client:
        await load()
        await Client.start(TOKEN)


# Run the Client
asyncio.run(main())
