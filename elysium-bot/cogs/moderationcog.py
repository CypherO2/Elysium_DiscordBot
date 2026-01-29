import datetime
import asyncio
import logging
import re
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import get_moderation_config
from utils import get_channel_safely

logger = logging.getLogger(__name__)

allowed_mentions = discord.AllowedMentions(roles=True)


class Moderation(commands.Cog):
    """Moderation cog for handling message filtering and alerts."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        """Handle incoming messages for moderation."""
        if msg.author == self.bot.user:
            return

        if not isinstance(msg.channel, discord.TextChannel):
            return

        try:
            config = get_moderation_config()
            mod_channel_id = config.get("mod_channel")
            block_list = config.get("block_words", [])
            mod_role = config.get("mod_role")

            if not mod_channel_id:
                logger.warning("Moderation channel not configured")
                return

            channel = get_channel_safely(self.bot, int(mod_channel_id))
            if not channel:
                logger.warning(f"Moderation channel {mod_channel_id} not found")
                return

            # Check for blocked words
            if block_list:
                msg_lower = msg.content.lower()
                for text in block_list:
                    # Use word boundaries to prevent false positives
                    pattern = r"\b" + re.escape(text.lower()) + r"\b"
                    if re.search(pattern, msg_lower):
                        embed = discord.Embed(
                            title="**ALERT!**",
                            description=(
                                f"In: {msg.channel.mention}\n"
                                f"Reason: {msg.author} said -> ||{text}||\n"
                                f"<@&{mod_role}>"
                                if mod_role
                                else ""
                            ),
                            color=0x5A0C8A,
                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                        )
                        try:
                            await msg.delete()
                        except discord.Forbidden:
                            logger.warning(
                                f"No permission to delete message in {msg.channel}"
                            )
                        except discord.NotFound:
                            logger.debug("Message already deleted")
                        except Exception as e:
                            logger.error(f"Error deleting message: {e}")

                        try:
                            await channel.send(embed=embed)
                        except Exception as e:
                            logger.error(f"Error sending alert to mod channel: {e}")
                        break  # Only flag once per message

            # Handle bot mentions
            if self.bot.user in msg.mentions:
                content_lower = msg.content.lower()
                if "kys" in content_lower or "kill yourself" in content_lower:
                    try:
                        await msg.channel.send(
                            "https://tenor.com/view/water-cat-cat-cat-bath-gif-8375496536506751533"
                        )
                    except Exception as e:
                        logger.error(f"Error sending response to mention: {e}")

            # React to "e"
            if msg.content.lower() == "e":
                try:
                    await msg.add_reaction("💀")
                except Exception as e:
                    logger.debug(f"Could not add reaction: {e}")

        except Exception as e:
            logger.error(f"Error in on_message handler: {e}", exc_info=True)

    @app_commands.command(name="alert", description="Report an Issue")
    @app_commands.describe(issue="What is the issue?")
    async def alert(self, interaction: discord.Interaction, issue: str) -> None:
        """Report an issue to moderators."""
        try:
            config = get_moderation_config()
            mod_channel_id = config.get("mod_channel")
            mod_role = config.get("mod_role")

            if not mod_channel_id:
                await interaction.response.send_message(
                    "Moderation channel is not configured.", ephemeral=True
                )
                return

            channel = get_channel_safely(self.bot, int(mod_channel_id))
            if not channel:
                await interaction.response.send_message(
                    "Moderation channel not found.", ephemeral=True
                )
                return

            # Get channel mention
            if isinstance(interaction.channel, discord.DMChannel):
                channel_mention = interaction.channel.recipient.mention
            else:
                channel_mention = interaction.channel.mention

            embed = discord.Embed(
                title="**ALERT!**",
                description=(
                    f"In: {channel_mention}\nReason: {issue}\n<@&{mod_role}>"
                    if mod_role
                    else ""
                ),
                color=0x5A0C8A,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )

            await asyncio.gather(
                channel.send(embed=embed),
                interaction.response.send_message(
                    "Your report has been sent", ephemeral=True
                ),
            )
        except Exception as e:
            logger.error(f"Error in alert command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while sending your report.", ephemeral=True
                )


async def setup(bot: commands.Bot):
    """Setup function for the moderation cog."""
    await bot.add_cog(Moderation(bot))
