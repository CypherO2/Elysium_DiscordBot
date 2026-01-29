import datetime
import asyncio
import re
import discord
from discord.ext import commands
from discord import app_commands
from twitchcog import load_config

allowed_mentions = discord.AllowedMentions(roles=True)


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg) -> None:
        config = load_config()
        channel = self.bot.get_channel(config["moderation"]["mod_channel"])
        block_list = config["moderation"]["block_words"]
        if msg.author != self.bot.user:
            msg_lower = msg.content.lower()
            for text in block_list:
                # Use word boundaries to prevent false positives (e.g., "class" matching "ass")
                # Check if the word appears as a whole word or at word boundaries
                pattern = r"\b" + re.escape(text.lower()) + r"\b"
                if re.search(pattern, msg_lower):
                    embed = discord.Embed(
                        title="**ALERT!**",
                        description=f"In: {msg.channel.mention}\nReason: {msg.author} said -> ||{text}||\n<@&{config['moderation']['mod_role']}>",
                        color=0x5A0C8A,
                        timestamp=datetime.datetime.now(),
                    )
                    await msg.delete()
                    await channel.send(embed=embed)
                    break  # Only flag once per message
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
        channel2 = (
            interaction.channel.mention  # type: ignore
            if not isinstance(interaction.channel, discord.DMChannel)
            else interaction.channel.recipient.mention  # type: ignore
        )
        embed = discord.Embed(
            title="**ALERT!**",
            description=f"In: {channel2}\nReason: {issue}\n<@&{config['moderation']['mod_role']}>",
            color=0x5A0C8A,
            timestamp=datetime.datetime.now(),
        )
        await asyncio.gather(
            channel.send(embed=embed),
            interaction.response.send_message(
                "Your report has been sent", ephemeral=True
            ),
        )


async def setup(bot):
    await bot.add_cog(moderation(bot))
