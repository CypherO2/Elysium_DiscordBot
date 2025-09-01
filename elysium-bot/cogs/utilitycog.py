import discord
from datetime import datetime
import asyncio
from typing import Optional
from discord.ext import commands
from discord import app_commands

# Datetime for Client startup tracking
start_time = datetime.now()
dev_id = 876876129368150018  # If you are hosting this bot, change this to your Discord UserID

bot_notifications = 1234227629352288275
public_log = 1234227629557547029  # Change to you public bot log channel ID
private_log = 1234227628924207283  # Change to you private bot log channel ID


class utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="runtime", description="Shows how long the Client has been online."
    )
    async def runtime(self, interaction: discord.Interaction):
        now = datetime.now()
        time_elapsed = now - start_time
        await interaction.response.send_message(
            f"As of {now.strftime('%d/%m/%Y %H:%M:%S')},\nTime Elapsed: {time_elapsed}",
            ephemeral=True,
        )

    @app_commands.command(
        name="shutdown", description="Stops the Client [Privileged Command]."
    )
    @app_commands.describe(reason="Why is the bot being shutdown?")
    async def shutdown(
        self, interaction: discord.Interaction, reason: Optional[str]
    ) -> None:
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

        channel1 = self.bot.get_channel(public_log)
        channel2 = self.bot.get_channel(private_log)

        if channel1:
            await channel1.send(embed=exit_msg)
        if channel2:
            await channel2.send(embed=exit_msg)

        await interaction.response.send_message(
            "Bot is shutting down...", ephemeral=True
        )
        await self.bot.close()

    @app_commands.command(
        name="help", description="Shows the list of available commands."
    )
    async def help_command(self, interaction: discord.Interaction):
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

    @app_commands.command(
        name="suggestion", description="send a suggestion for the bot"
    )
    @app_commands.describe(suggestion="What is your suggestion?")
    async def suggest_command(self, interaction: discord.Interaction, suggestion: str):
        channel = self.bot.get_channel(bot_notifications)
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


async def setup(bot):
    await bot.add_cog(utility(bot))
