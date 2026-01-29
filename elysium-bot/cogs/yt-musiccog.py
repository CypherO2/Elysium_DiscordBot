import logging
import os
import asyncio
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands
import yt_dlp

logger = logging.getLogger(__name__)

# Determine FFmpeg path based on OS
if os.name == "nt":  # Windows
    FFMPEG_PATH = Path(__file__).parent.parent.parent / "bin" / "ffmpeg.exe"
else:  # Linux/Mac
    FFMPEG_PATH = Path(__file__).parent.parent.parent / "bin" / "ffmpeg"

# Fallback to system ffmpeg if not found in bin directory
if not FFMPEG_PATH.exists():
    FFMPEG_PATH = "ffmpeg"  # Use system ffmpeg

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
    "executable": FFMPEG_PATH,
}
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "logtostderr": False,
    "ignoreerrors": False,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues sometimes
}


class MusicBot(commands.Cog):
    """Music bot cog for playing YouTube audio in voice channels."""

    def __init__(self, bot: commands.Bot):
        """Initialize the music bot."""
        self.bot = bot
        self.queue: list[tuple[str, str]] = []  # List of (url, title) tuples
        self.current_ctx: Optional[commands.Context] = None
        self.disconnect_timer: Optional[asyncio.Task] = None
        self.empty_channel_timer: Optional[asyncio.Task] = None

    @commands.command()
    async def play(self, ctx: commands.Context, *, search: str):
        """Play a song from YouTube."""
        logger.info(
            f"Command !play used by {ctx.author} (ID: {ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'} - Search: {search[:50]}"
        )
        # Check if user is in a voice channel
        if not ctx.author.voice:
            logger.warning(
                f"Play command used by {ctx.author.id} but user not in voice channel"
            )
            await ctx.send("❌ You are not in a voice channel!")
            return

        voice_channel = ctx.author.voice.channel

        # Connect to voice channel if not already connected
        if not ctx.voice_client:
            try:
                await voice_channel.connect()
                logger.info(f"Connected to voice channel: {voice_channel.name}")
            except discord.ClientException as e:
                logger.error(f"Failed to connect to voice channel: {e}")
                await ctx.send("❌ Failed to connect to voice channel!")
                return
            except Exception as e:
                logger.error(f"Unexpected error connecting to voice channel: {e}")
                await ctx.send(
                    "❌ An error occurred while connecting to the voice channel!"
                )
                return

        # Check if bot is in the same voice channel as user
        elif ctx.voice_client.channel != voice_channel:
            await ctx.send("❌ You must be in the same voice channel as the bot!")
            return

        async with ctx.typing():
            try:
                # Run yt-dlp in a thread to avoid blocking
                def extract_info():
                    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                        return ydl.extract_info(f"ytsearch:{search}", download=False)

                info = await asyncio.to_thread(extract_info)

                if "entries" in info and len(info["entries"]) > 0:
                    info = info["entries"][0]
                else:
                    await ctx.send("❌ No results found!")
                    return

                url = info.get("url")
                title = info.get("title", "Unknown Title")

                if not url:
                    await ctx.send("❌ Could not get audio URL!")
                    return

                # Add to queue
                self.queue.append((url, title))
                await ctx.send(f"✅ Added to queue: **{title}**")
                logger.info(
                    f"Song '{title}' added to queue by {ctx.author.id} (Queue size: {len(self.queue)})"
                )

            except yt_dlp.DownloadError as e:
                logger.error(f"yt-dlp error: {e}")
                await ctx.send(f"❌ Error searching for video: {str(e)}")
            except Exception as e:
                logger.error(f"Error in play command: {e}", exc_info=True)
                await ctx.send(f"❌ An error occurred while searching: {str(e)}")

        # Set current context for callbacks
        self.current_ctx = ctx

        # Cancel any existing disconnect timer
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
            self.disconnect_timer = None

        # Play next song if nothing is currently playing
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.play_next()

        # Start monitoring for empty voice channel
        self.start_empty_channel_timer(ctx)

    async def play_next(self):
        """Play the next song in the queue."""
        if not self.current_ctx:
            return

        ctx = self.current_ctx

        if not ctx.voice_client:
            logger.warning("Voice client not available for play_next")
            return

        if self.queue:
            url, title = self.queue.pop(0)
            try:
                # Create audio source
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

                # Play the audio with after callback
                ctx.voice_client.play(
                    source,
                    after=lambda error: asyncio.create_task(self.after_playing(error)),
                )
                await ctx.send(f"🎵 Now Playing: **{title}**")
                logger.info(f"Now playing: {title}")

            except discord.ClientException as e:
                logger.error(f"Discord client error playing audio: {e}")
                await ctx.send(f"❌ Error playing audio: {str(e)}")
                # Try to play next song if there was an error
                await self.play_next()
            except Exception as e:
                logger.error(f"Error playing audio: {e}", exc_info=True)
                await ctx.send(f"❌ Error playing audio: {str(e)}")
                # Try to play next song if there was an error
                await self.play_next()
        else:
            await ctx.send("📭 Queue is empty!")
            # Start disconnect timer when queue is empty and nothing is playing
            self.start_disconnect_timer(ctx)

    async def after_playing(self, error: Optional[Exception]):
        """Callback after a song finishes playing."""
        if error:
            logger.error(f"Player error: {error}")
        # Cancel disconnect timer since we're about to play next song
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
            self.disconnect_timer = None
        # Play next song after current one finishes
        await self.play_next()

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skip the current song."""
        logger.info(
            f"Command !skip used by {ctx.author} (ID: {ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )
        if not ctx.voice_client:
            logger.warning(
                f"Skip command used by {ctx.author.id} but bot not in voice channel"
            )
            await ctx.send("❌ I'm not connected to a voice channel!")
            return

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Song skipped!")
            logger.info(f"Song skipped by {ctx.author.id}")
        else:
            logger.warning(
                f"Skip command used by {ctx.author.id} but nothing is playing"
            )
            await ctx.send("❌ Nothing is currently playing!")

    @commands.command()
    async def queue(self, ctx: commands.Context):
        """Show the current queue."""
        logger.info(
            f"Command !queue used by {ctx.author} (ID: {ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )
        if not self.queue:
            await ctx.send("📭 Queue is empty!")
            return

        queue_list = "\n".join(
            [f"{i + 1}. {title}" for i, (url, title) in enumerate(self.queue)]
        )
        embed = discord.Embed(
            title="Current Queue", description=queue_list, color=0x5A0C8A
        )
        await ctx.send(embed=embed)
        logger.debug(f"Queue displayed to {ctx.author.id} - {len(self.queue)} item(s)")

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stop playing and disconnect from voice channel."""
        logger.info(
            f"Command !stop used by {ctx.author} (ID: {ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )
        if ctx.voice_client:
            self.queue.clear()
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Stopped playing and disconnected!")
            logger.info(f"Music stopped and disconnected by {ctx.author.id}")
            # Cancel timers
            self.cancel_timers()
        else:
            logger.warning(
                f"Stop command used by {ctx.author.id} but bot not in voice channel"
            )
            await ctx.send("❌ I'm not connected to a voice channel!")

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pause the current song."""
        logger.info(
            f"Command !pause used by {ctx.author} (ID: {ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused!")
            logger.info(f"Music paused by {ctx.author.id}")
        else:
            logger.warning(
                f"Pause command used by {ctx.author.id} but nothing is playing"
            )
            await ctx.send("❌ Nothing is currently playing!")

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Resume the paused song."""
        logger.info(
            f"Command !resume used by {ctx.author} (ID: {ctx.author.id}) "
            f"in {ctx.guild.name if ctx.guild else 'DM'}"
        )
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed!")
            logger.info(f"Music resumed by {ctx.author.id}")
        else:
            logger.warning(
                f"Resume command used by {ctx.author.id} but audio is not paused"
            )
            await ctx.send("❌ Audio is not paused!")

    def cancel_timers(self):
        """Cancel all active timers"""
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
            self.disconnect_timer = None
        if self.empty_channel_timer:
            self.empty_channel_timer.cancel()
            self.empty_channel_timer = None

    def start_disconnect_timer(self, ctx: commands.Context):
        """Start timer to disconnect after 30 seconds of inactivity."""
        if self.disconnect_timer:
            self.disconnect_timer.cancel()

        async def disconnect_callback():
            try:
                if (
                    ctx.voice_client
                    and not ctx.voice_client.is_playing()
                    and not ctx.voice_client.is_paused()
                    and not self.queue
                ):
                    await ctx.send("🔌 Disconnecting due to inactivity...")
                    await ctx.voice_client.disconnect()
                    self.cancel_timers()
                    logger.info("Disconnected from voice channel due to inactivity")
            except Exception as e:
                logger.error(f"Error in disconnect callback: {e}", exc_info=True)

        self.disconnect_timer = asyncio.create_task(asyncio.sleep(30))
        self.disconnect_timer.add_done_callback(
            lambda _: asyncio.create_task(disconnect_callback())
        )

    def start_empty_channel_timer(self, ctx: commands.Context):
        """Start timer to disconnect if voice channel is empty."""
        if self.empty_channel_timer:
            self.empty_channel_timer.cancel()

        async def empty_channel_callback():
            try:
                if ctx.voice_client and ctx.voice_client.channel:
                    # Count members excluding bots
                    human_members = [
                        m for m in ctx.voice_client.channel.members if not m.bot
                    ]
                    if len(human_members) == 0:
                        await ctx.send(
                            "🔌 Disconnecting because no one is in the voice channel..."
                        )
                        await ctx.voice_client.disconnect()
                        self.cancel_timers()
                        logger.info("Disconnected from voice channel - no members")
                    else:
                        # Restart timer if there are still people
                        self.start_empty_channel_timer(ctx)
            except Exception as e:
                logger.error(f"Error in empty channel callback: {e}", exc_info=True)

        self.empty_channel_timer = asyncio.create_task(asyncio.sleep(30))
        self.empty_channel_timer.add_done_callback(
            lambda _: asyncio.create_task(empty_channel_callback())
        )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """Handle errors for text commands."""
        logger.error(
            f"Command error in {ctx.command.name if ctx.command else 'unknown'} "
            f"by {ctx.author} (ID: {ctx.author.id}) in {ctx.guild.name if ctx.guild else 'DM'}: {error}",
            exc_info=error,
        )


async def setup(bot: commands.Bot):
    """Setup function for the music bot cog."""
    await bot.add_cog(MusicBot(bot))
