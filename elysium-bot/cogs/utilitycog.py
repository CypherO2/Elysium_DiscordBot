import logging
from datetime import datetime
from datetime import timezone
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import get_bot_config
from utils import get_channel_safely

logger = logging.getLogger(__name__)

# Datetime for Client startup tracking
start_time = datetime.now(timezone.utc)

# Load bot config
try:
    bot_config = get_bot_config()
    dev_id = bot_config.get("dev_id", 0)
    bot_notifications = bot_config.get("bot_notifications", 0)
    public_log = bot_config.get("public_log", 0)
    private_log = bot_config.get("private_log", 0)

    if not dev_id:
        logger.warning("dev_id not configured in bot config")
except Exception as e:
    logger.error(f"Error loading bot config: {e}")
    dev_id = 0
    bot_notifications = 0
    public_log = 0
    private_log = 0


class Utility(commands.Cog):
    """Utility cog for bot management and help commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="runtime", description="Shows how long the Client has been online."
    )
    async def runtime(self, interaction: discord.Interaction):
        """Show bot runtime information."""
        logger.info(
            f"Command /runtime used by {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'}"
        )
        try:
            now = datetime.now(timezone.utc)
            time_elapsed = now - start_time
            await interaction.response.send_message(
                f"As of {now.strftime('%d/%m/%Y %H:%M:%S')} UTC,\nTime Elapsed: {time_elapsed}",
                ephemeral=True,
            )
            logger.debug(
                f"Runtime command completed successfully for {interaction.user.id}"
            )
        except Exception as e:
            logger.error(
                f"Error in runtime command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while getting runtime information.",
                    ephemeral=True,
                )

    @app_commands.command(
        name="shutdown", description="Stops the Client [Privileged Command]."
    )
    @app_commands.describe(reason="Why is the bot being shutdown?")
    async def shutdown(
        self, interaction: discord.Interaction, reason: Optional[str] = None
    ) -> None:
        """Shutdown the bot (dev only)."""
        if interaction.user.id != dev_id:
            logger.warning(
                f"Unauthorized shutdown attempt by {interaction.user} (ID: {interaction.user.id}) "
                f"in {interaction.guild.name if interaction.guild else 'DM'}"
            )
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        logger.info(
            f"Command /shutdown used by authorized user {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'} - Reason: {reason or 'No reason provided'}"
        )

        try:
            now = datetime.now(timezone.utc)
            time_elapsed = now - start_time
            exit_msg = discord.Embed(
                title="𝓔𝓵𝔂𝓼𝓲𝓾𝓶",
                description=(
                    f"**Status**: 🔴 Offline\n"
                    f"**Reason**: {reason or 'No reason provided'}\n"
                    f"**Runtime**: {time_elapsed}"
                ),
                timestamp=now,
            )

            channel1 = get_channel_safely(self.bot, public_log) if public_log else None
            channel2 = (
                get_channel_safely(self.bot, private_log) if private_log else None
            )

            if channel1:
                try:
                    await channel1.send(embed=exit_msg)
                except Exception as e:
                    logger.error(f"Error sending to public log: {e}")
            if channel2:
                try:
                    await channel2.send(embed=exit_msg)
                except Exception as e:
                    logger.error(f"Error sending to private log: {e}")

            await interaction.response.send_message(
                "Bot is shutting down...", ephemeral=True
            )
            logger.info(
                f"Bot shutdown initiated by {interaction.user} (ID: {interaction.user.id})"
            )
            await self.bot.close()
        except Exception as e:
            logger.error(f"Error in shutdown command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while shutting down.", ephemeral=True
                )

    @app_commands.command(
        name="help", description="Shows the list of available commands."
    )
    async def help_command(self, interaction: discord.Interaction):
        """Display help information."""
        logger.info(
            f"Command /help used by {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'}"
        )
        try:
            embed = discord.Embed(
                title="**𝓔𝓵𝔂𝓼𝓲𝓾𝓶 - Help Centre**",
                description="Need help? Here is a list of commands available with this Client.",
                color=0x5A0C8A,
            )
            embed.add_field(
                name="Commands",
                value=(
                    "**/help** - Displays the help menu - contains a list of commands.\n"
                    "**/runtime** - Shows how long the bot has been online.\n"
                    "**/watchlist {action} {streamer_name}** - Allows for the editing and viewing of the streamer list.\n"
                    "**/setlivemessage {message} {role}** - Allows for the creation of custom messages for stream notifications.\n"
                    "**/setlivechannel {channel}** - Allows for the changing of the channel the bot sends notifications in.\n"
                    "**/shutdown {reason}** - This command stops the bot (Authorised users only).\n"
                    "**/suggestion {suggestion}** - This command allows for the user to send a suggestion for update to the bot.\n"
                    "**/alert {issue}** - Report an issue to moderators.\n"
                    "**!play {song}** - Play music in a voice channel.\n"
                    "**!skip** - Skip the current song.\n"
                    "**!queue** - Show the current queue.\n"
                    "**!stop** - Stop playing and disconnect.\n"
                    "**!pause** - Pause the current song.\n"
                    "**!resume** - Resume the paused song."
                ),
                inline=False,
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while displaying help.", ephemeral=True
                )

    @app_commands.command(
        name="suggestion", description="send a suggestion for the bot"
    )
    @app_commands.describe(suggestion="What is your suggestion?")
    async def suggest_command(self, interaction: discord.Interaction, suggestion: str):
        """Submit a suggestion for the bot."""
        logger.info(
            f"Command /suggestion used by {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'}"
        )
        if not suggestion or not suggestion.strip():
            logger.warning(f"Empty suggestion attempt by {interaction.user.id}")
            await interaction.response.send_message(
                "❌ Suggestion cannot be empty.", ephemeral=True
            )
            return

        try:
            channel = (
                get_channel_safely(self.bot, bot_notifications)
                if bot_notifications
                else None
            )
            if not channel:
                await interaction.response.send_message(
                    "❌ Suggestion channel is not configured.", ephemeral=True
                )
                return

            embed = discord.Embed(
                title="**Suggestion!**",
                description=suggestion,
                color=0x5A0C8A,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_author(
                name=str(interaction.user),
                icon_url=interaction.user.display_avatar.url
                if interaction.user.display_avatar
                else None,
            )

            await channel.send(embed=embed)
            await interaction.response.send_message(
                f"✅ Your suggestion has been registered!\n`Your Suggestion: {suggestion}`",
                ephemeral=True,
            )
            logger.info(
                f"Suggestion successfully submitted by {interaction.user.id}: {suggestion[:50]}..."
            )
        except Exception as e:
            logger.error(
                f"Error in suggestion command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while submitting your suggestion.",
                    ephemeral=True,
                )

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors for app commands."""
        logger.error(
            f"App command error in {interaction.command.name if interaction.command else 'unknown'} "
            f"by {interaction.user} (ID: {interaction.user.id}): {error}",
            exc_info=error,
        )


async def setup(bot: commands.Bot):
    """Setup function for the utility cog."""
    await bot.add_cog(Utility(bot))
