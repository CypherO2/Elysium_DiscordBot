import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

FFMPEG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "ffmpeg.exe")
# For Linux/Mac use: 
# FFMPEG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "ffmpeg")

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
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.current_ctx = None
        self.disconnect_timer = None
        self.empty_channel_timer = None

    @commands.command()
    async def play(self, ctx, *, search):
        # Check if user is in a voice channel
        if not ctx.author.voice:
            return await ctx.send("You are not in a voice channel!")

        voice_channel = ctx.author.voice.channel

        # Connect to voice channel if not already connected
        if not ctx.voice_client:
            try:
                await voice_channel.connect()
            except discord.ClientException:
                return await ctx.send("Failed to connect to voice channel!")

        # Check if bot is in the same voice channel as user
        elif ctx.voice_client.channel != voice_channel:
            return await ctx.send("You must be in the same voice channel as the bot!")

        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    # Search for the song
                    info = ydl.extract_info(f"ytsearch:{search}", download=False)
                    if "entries" in info and len(info["entries"]) > 0:
                        info = info["entries"][0]
                    else:
                        return await ctx.send("No results found!")

                    url = info["url"]
                    title = info["title"]

                    # Add to queue
                    self.queue.append((url, title))
                    await ctx.send(f"Added to queue: **{title}**")

            except Exception as e:
                return await ctx.send(f"An error occurred while searching: {str(e)}")

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
        if not self.current_ctx:
            return

        ctx = self.current_ctx

        if self.queue:
            url, title = self.queue.pop(0)
            try:
                # Create audio source
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

                # Play the audio with after callback
                ctx.voice_client.play(
                    source,
                    after=lambda error: self.client.loop.create_task(
                        self.after_playing(error)
                    ),
                )
                await ctx.send(f"Now Playing: **{title}**")

            except Exception as e:
                await ctx.send(f"Error playing audio: {str(e)}")
                # Try to play next song if there was an error
                await self.play_next()
        else:
            await ctx.send("Queue is empty!")
            # Start disconnect timer when queue is empty and nothing is playing
            self.start_disconnect_timer(ctx)

    async def after_playing(self, error):
        if error:
            print(f"Player error: {error}")
        # Cancel disconnect timer since we're about to play next song
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
            self.disconnect_timer = None
        # Play next song after current one finishes
        await self.play_next()

    @commands.command()
    async def skip(self, ctx):
        if not ctx.voice_client:
            return await ctx.send("I'm not connected to a voice channel!")

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            await ctx.send("Song skipped!")
        else:
            await ctx.send("Nothing is currently playing!")

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            return await ctx.send("Queue is empty!")

        queue_list = "\n".join(
            [f"{i+1}. {title}" for i, (url, title) in enumerate(self.queue)]
        )
        await ctx.send(f"**Current Queue:**\n{queue_list}")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queue.clear()
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("Stopped playing and disconnected!")
            # Cancel timers
            self.cancel_timers()
        else:
            await ctx.send("I'm not connected to a voice channel!")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused!")
        else:
            await ctx.send("Nothing is currently playing!")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed!")
        else:
            await ctx.send("Audio is not paused!")

    def cancel_timers(self):
        """Cancel all active timers"""
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
            self.disconnect_timer = None
        if self.empty_channel_timer:
            self.empty_channel_timer.cancel()
            self.empty_channel_timer = None

    def start_disconnect_timer(self, ctx):
        """Start timer to disconnect after 30 seconds of inactivity"""
        if self.disconnect_timer:
            self.disconnect_timer.cancel()

        async def disconnect_callback():
            try:
                if (
                    ctx.voice_client
                    and not ctx.voice_client.is_playing()
                    and not self.queue
                ):
                    await ctx.send("Disconnecting due to inactivity...")
                    await ctx.voice_client.disconnect()
                    self.cancel_timers()
            except Exception as e:
                print(f"Error in disconnect callback: {e}")

        self.disconnect_timer = asyncio.create_task(asyncio.sleep(30))
        self.disconnect_timer.add_done_callback(
            lambda _: self.client.loop.create_task(disconnect_callback())
        )

    def start_empty_channel_timer(self, ctx):
        """Start timer to disconnect if voice channel is empty"""
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
                            "Disconnecting because no one is in the voice channel..."
                        )
                        await ctx.voice_client.disconnect()
                        self.cancel_timers()
                    else:
                        # Restart timer if there are still people
                        self.start_empty_channel_timer(ctx)
            except Exception as e:
                print(f"Error in empty channel callback: {e}")

        self.empty_channel_timer = asyncio.create_task(asyncio.sleep(30))
        self.empty_channel_timer.add_done_callback(
            lambda _: self.client.loop.create_task(empty_channel_callback())
        )


async def setup(bot):
    await bot.add_cog(MusicBot(bot))
