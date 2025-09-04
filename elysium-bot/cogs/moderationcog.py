import discord
import json
import datetime
import typing
import asyncio
from typing import Optional
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, date, time, timezone, timedelta
from twitchcog import load_config
from main import Client

class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @Client.event
    async def on_message(self, msg) -> None:
        config = load_config()
        channel = self.bot.get_channel(config["moderation"]["mod_channel"])
        block_list = config["moderation"]["block_words"]
        if msg.author != self.bot.user:
            for text in block_list:
                if text in str(msg.content.lower()):
                    embed = discord.Embed(
                        title="**ALERT!**",
                        description=f"In: {msg.channel.mention}\nReason: {msg.author} said -> ||{text}||\n<@&{config['moderation']['mod_role']}>",
                        color=0x5A0C8A,
                        timestamp=datetime.datetime.now(),
                    )
                    await msg.delete()
                    await channel.send(embed=embed)
            if self.bot.user in msg.mentions:
                if "kys" in msg.content:
                    await msg.channel.send(
                        "https://tenor.com/view/water-cat-cat-cat-bath-gif-8375496536506751533"
                    )
                if "kill yourself" in msg.content:
                    await msg.channel.send(
                        "https://tenor.com/view/water-cat-cat-cat-bath-gif-8375496536506751533"
                    )

            if msg.content.lower() == "e":
                reaction = "💀"
                await msg.add_reaction(reaction)

    @app_commands.command(name="alert", description="Report an Issue")
    @app_commands.describe(issue="What is the issue?")
    async def Alert(self, interaction: discord.Interaction, issue: str) -> None:
        config = load_config()
        channel = self.bot.get_channel(config["moderation"]["mod_channel"])
        channel2 = interaction.channel.mention if not isinstance(interaction.channel, discord.DMChannel) else interaction.channel.recipient.mention
        embed = discord.Embed(
            title="**ALERT!**",
            description=f"In: {channel2}\nReason: {issue}\n<@&{config['moderation']['mod_role']}>",
            color=0x5A0C8A,
            timestamp=datetime.datetime.now(),
        )
        await asyncio.gather(
            channel.send(embed=embed),
            interaction.response.send_message("Your report has been sent", ephemeral=True),
    )

async def setup(bot):
    await bot.add_cog(moderation(bot))
