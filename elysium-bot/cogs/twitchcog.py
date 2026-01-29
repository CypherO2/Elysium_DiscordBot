import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands
from requests import post, get
from requests.exceptions import RequestException, Timeout

from config import get_twitch_config, get_bot_config, load_config, save_config

logger = logging.getLogger(__name__)

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 10

allowed_mentions = discord.AllowedMentions(roles=True)


def get_twcord_userid() -> int:
    """Get the Twitch command user ID from config."""
    config = get_twitch_config()
    return config.get("twcord_userid", 0)


def get_dev_id() -> int:
    """Get the dev user ID from config."""
    bot_config = get_bot_config()
    return bot_config.get("dev_id", 0)


def is_authorized_user(user_id: int) -> bool:
    """Check if a user is authorized to use Twitch commands (dev or twitch user)."""
    dev_id = get_dev_id()
    twitch_user_id = get_twcord_userid()
    return user_id == dev_id or user_id == twitch_user_id


def get_app_access_token() -> str:
    """Get Twitch app access token."""
    config = get_twitch_config()
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")

    if not client_id or not client_secret:
        raise ValueError("Twitch client_id and client_secret must be configured")

    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    try:
        response = post(
            "https://id.twitch.tv/oauth2/token", params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("No access_token in Twitch API response")
        logger.info("Successfully obtained Twitch access token")
        return access_token
    except Timeout:
        logger.error("Timeout while getting Twitch access token")
        raise
    except RequestException as e:
        logger.error(f"Error getting Twitch access token: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response from Twitch API: {e}")
        raise


def calculate_unix_time_future(weeks: int = 3) -> int:
    """Calculate UNIX timestamp for a future date.

    Args:
        weeks: Number of weeks in the future (default: 3)

    Returns:
        int: UNIX timestamp
    """
    now = datetime.now(timezone.utc)
    future = now + timedelta(weeks=weeks)
    return int(future.timestamp())


def get_users(login_names: list[str]) -> Dict[str, str]:
    """Get Twitch user IDs from login names.

    Args:
        login_names: List of Twitch login names

    Returns:
        dict: Mapping of login names to user IDs
    """
    if not login_names:
        return {}

    config = get_twitch_config()
    access_token = config.get("access_token")
    client_id = config.get("client_id")

    if not access_token or not client_id:
        logger.error("Twitch access_token or client_id not configured")
        return {}

    params = [("login", login) for login in login_names]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": client_id,
    }

    try:
        response = get(
            "https://api.twitch.tv/helix/users",
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        return {entry["login"]: entry["id"] for entry in data}
    except Timeout:
        logger.error("Timeout while getting Twitch users")
        return {}
    except RequestException as e:
        logger.error(f"Error getting Twitch users: {e}")
        return {}
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response from Twitch API: {e}")
        return {}


def get_streams(users: Dict[str, str]) -> Dict[str, dict]:
    """Get stream information for given users.

    Args:
        users: Dictionary mapping login names to user IDs

    Returns:
        dict: Mapping of login names to stream data
    """
    if not users:
        return {}

    config = get_twitch_config()
    access_token = config.get("access_token")
    client_id = config.get("client_id")

    if not access_token or not client_id:
        logger.error("Twitch access_token or client_id not configured")
        return {}

    params = []
    for user_id in set(users.values()):  # Use set() to ensure unique user IDs
        params.append(("user_id", user_id))

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": client_id,
    }

    try:
        response = get(
            "https://api.twitch.tv/helix/streams",
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        streams_data = response.json().get("data", [])
        logger.debug(f"Retrieved {len(streams_data)} stream(s)")
        return {entry["user_login"]: entry for entry in streams_data}
    except Timeout:
        logger.error("Timeout while getting Twitch streams")
        return {}
    except RequestException as e:
        logger.error(f"Error getting Twitch streams: {e}")
        return {}
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response from Twitch API: {e}")
        return {}


class Twitch(commands.Cog):
    """Cog for managing Twitch stream notifications."""

    def __init__(self, bot: commands.Bot):
        """Initialize the Twitch cog."""
        self.bot = bot
        self.online_users: Dict[
            str, Optional[datetime]
        ] = {}  # Track online users and stream start times

    async def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("Twitch cog loaded – starting tasks")

        if not self.check_twitch_access_token.is_running():
            self.check_twitch_access_token.start()
            logger.info("Started access token check loop")
        else:
            logger.warning("Access token loop already running")

        if not self.check_twitch_online_streamers.is_running():
            self.check_twitch_online_streamers.start()
            logger.info("Started streamer check loop")
        else:
            logger.warning("Streamer check loop already running")

    async def cog_unload(self):
        """Clean up tasks when cog is unloaded."""
        logger.info("Unloading Twitch cog")
        if self.check_twitch_access_token.is_running():
            self.check_twitch_access_token.cancel()
        if self.check_twitch_online_streamers.is_running():
            self.check_twitch_online_streamers.cancel()
        # Clean up old entries from online_users (keep last 100)
        if len(self.online_users) > 100:
            # Keep only the most recent entries
            sorted_items = sorted(
                self.online_users.items(),
                key=lambda x: x[1]
                if x[1]
                else datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )[:100]
            self.online_users = dict(sorted_items)

    def get_notifications(self) -> list[dict]:
        """Get notifications for newly started streams.

        Returns:
            list: List of stream data dictionaries for new streams
        """
        config = get_twitch_config()
        watchlist = config.get("watchlist", [])

        if not watchlist:
            return []

        users = get_users(watchlist)
        if not users:
            logger.warning("No users found in Twitch API response")
            return []

        streams = get_streams(users)
        notifications = []

        for user_name in watchlist:
            logger.debug(f"Checking user: {user_name}")

            if user_name not in self.online_users:
                self.online_users[user_name] = None  # Start as None to signify offline
                logger.debug(f"Initializing {user_name} as offline")

            if user_name not in streams:
                self.online_users[user_name] = None  # User is not online
                logger.debug(f"{user_name} is offline")
            else:
                stream_data = streams[user_name]
                logger.debug(f"{user_name} is online")

                try:
                    # Convert the started_at string to a datetime object
                    started_at_str = stream_data.get("started_at")
                    if not started_at_str:
                        logger.warning(f"No started_at for {user_name}")
                        continue

                    started_at = datetime.strptime(
                        started_at_str, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)

                    # Check if this is a new stream
                    if (
                        self.online_users[user_name] is None
                        or started_at > self.online_users[user_name]
                    ):
                        logger.info(f"Adding notification for {user_name}")
                        notifications.append(stream_data)
                        self.online_users[user_name] = started_at
                except (ValueError, KeyError) as e:
                    logger.error(f"Error parsing stream data for {user_name}: {e}")
                    continue

        logger.debug(f"Found {len(notifications)} new stream(s)")
        return notifications

    @tasks.loop(minutes=60)
    async def check_twitch_access_token(self):
        """Periodically check and refresh Twitch access token."""
        try:
            logger.debug("Running Twitch access token check")
            current_time = datetime.now(timezone.utc).timestamp()
            config = load_config()
            twitch_config = config.get("twitch", {})
            expire_date = twitch_config.get("expire_date", 0)

            if int(current_time) >= expire_date:
                logger.info("Twitch access token expired, refreshing...")
                access_token = get_app_access_token()
                twitch_config["access_token"] = access_token
                twitch_config["expire_date"] = calculate_unix_time_future(weeks=3)
                config["twitch"] = twitch_config
                save_config(config)
                logger.info("Access token regenerated successfully")
            else:
                logger.debug("Access token still valid")
        except ValueError as e:
            logger.error(f"Configuration error in check_twitch_access_token: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error in check_twitch_access_token: {e}", exc_info=True
            )

    @tasks.loop(seconds=90)
    async def check_twitch_online_streamers(self):
        """Periodically check for online streamers and send notifications."""
        try:
            config = get_twitch_config()
            logger.debug("Running streamer check loop")

            channel_id_str = config.get("channel_id")
            if not channel_id_str:
                logger.warning("Twitch channel_id not configured")
                return

            try:
                channel_id = int(channel_id_str)
            except (ValueError, TypeError):
                logger.error(f"Invalid channel_id format: {channel_id_str}")
                return

            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                logger.warning(f"Channel {channel_id} not found or not a text channel")
                return

            live_message = config.get("live_msg", "@everyone")
            notifications = self.get_notifications()

            for notification in notifications:
                try:
                    user_login = notification.get("user_login", "unknown")
                    user_name = notification.get("user_name", user_login)
                    title = notification.get("title", "Untitled Stream")
                    game_name = notification.get("game_name", "")
                    viewer_count = notification.get("viewer_count", 0)

                    embed = discord.Embed(
                        title=title,
                        url=f"https://twitch.tv/{user_login}",
                        description=f"[Watch Here](https://twitch.tv/{user_login})",
                        color=0x6034B2,
                    )
                    embed.set_author(
                        name=f"{user_name} is now live on Twitch!",
                        url=f"https://twitch.tv/{user_login}",
                    )
                    embed.add_field(
                        name="Game",
                        value=game_name if game_name else "Unknown",
                        inline=True,
                    )
                    embed.add_field(
                        name="Viewers",
                        value=str(viewer_count),
                        inline=True,
                    )
                    embed.set_image(
                        url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{user_login}-1920x1080.jpg"
                    )

                    await channel.send(
                        live_message, allowed_mentions=allowed_mentions, embed=embed
                    )
                    logger.info(f"Sent notification for {user_name}")
                except discord.Forbidden:
                    logger.error(
                        f"No permission to send message to channel {channel_id}"
                    )
                except discord.HTTPException as e:
                    logger.error(f"Discord API error sending notification: {e}")
                except Exception as e:
                    logger.error(f"Error sending notification: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in check_twitch_online_streamers: {e}", exc_info=True)

    @app_commands.command(
        name="watchlist",
        description="Edit/ Show the list of Streamer",
    )
    @app_commands.describe(
        action="What do you want to do? (add/remove/show)",
        streamername="Streamer name (not needed if only viewing the list)",
    )
    async def watchlist(
        self,
        interaction: discord.Interaction,
        action: str,
        streamername: Optional[str] = None,
    ):
        """Manage the Twitch streamer watchlist."""
        if not is_authorized_user(interaction.user.id):
            logger.warning(
                f"Unauthorized /watchlist attempt by {interaction.user} (ID: {interaction.user.id}) "
                f"in {interaction.guild.name if interaction.guild else 'DM'} - Action: {action}"
            )
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_type = "dev" if interaction.user.id == get_dev_id() else "twitch user"
        logger.info(
            f"Command /watchlist used by authorized {user_type} {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'} - Action: {action}, Streamer: {streamername or 'N/A'}"
        )
        action_lower = action.lower()

        try:
            if action_lower == "add":
                if not streamername:
                    logger.warning(
                        f"Watchlist add command used without streamer name by {interaction.user.id}"
                    )
                    await interaction.response.send_message(
                        "❌ Streamer name is required for adding.", ephemeral=True
                    )
                    return
                response = followstreamer(streamer=streamername)
                await interaction.response.send_message(response, ephemeral=True)
                logger.info(
                    f"Watchlist add completed by {interaction.user.id}: {streamername}"
                )
            elif action_lower == "remove":
                if not streamername:
                    logger.warning(
                        f"Watchlist remove command used without streamer name by {interaction.user.id}"
                    )
                    await interaction.response.send_message(
                        "❌ Streamer name is required for removing.", ephemeral=True
                    )
                    return
                response = unfollowstreamer(streamer=streamername)
                await interaction.response.send_message(response, ephemeral=True)
                logger.info(
                    f"Watchlist remove completed by {interaction.user.id}: {streamername}"
                )
            elif action_lower == "show":
                response = viewstreamers()
                embed = discord.Embed(
                    title="Streamer List [Twitch]",
                    description="Here is the list of streamers you're listening for.",
                )
                if response:
                    for streamer in response:
                        embed.add_field(name=streamer, value="", inline=False)
                else:
                    embed.description = "No streamers in watchlist."
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(
                    f"Watchlist show completed by {interaction.user.id} - {len(response)} streamer(s)"
                )
            else:
                logger.warning(
                    f"Invalid watchlist action '{action}' by {interaction.user.id}"
                )
                await interaction.response.send_message(
                    "❌ Invalid action. Use 'add', 'remove', or 'show'.", ephemeral=True
                )
        except Exception as e:
            logger.error(
                f"Error in watchlist command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while processing your request.",
                    ephemeral=True,
                )

    @app_commands.command(
        name="setlivechannel",
        description="Choose the channel you want to send the live notifications in.",
    )
    @app_commands.describe(channel="Channel mention or ID")
    async def setlivechannel(self, interaction: discord.Interaction, channel: str):
        """Set the channel for Twitch live notifications."""
        if not is_authorized_user(interaction.user.id):
            logger.warning(
                f"Unauthorized /setlivechannel attempt by {interaction.user} (ID: {interaction.user.id}) "
                f"in {interaction.guild.name if interaction.guild else 'DM'}"
            )
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_type = "dev" if interaction.user.id == get_dev_id() else "twitch user"
        logger.info(
            f"Command /setlivechannel used by authorized {user_type} {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'} - Channel: {channel}"
        )

        from utils import validate_channel_id  # type: ignore

        channel_id = validate_channel_id(channel)
        if not channel_id:
            await interaction.response.send_message(
                "❌ Invalid channel format. Please use a channel mention or ID.",
                ephemeral=True,
            )
            return

        # Verify channel exists
        if not self.bot.get_channel(channel_id):
            await interaction.response.send_message(
                "❌ Channel not found.", ephemeral=True
            )
            return

        try:
            response = changelivechannel(channel_id=channel_id)
            await interaction.response.send_message(response, ephemeral=True)
            logger.info(
                f"Live channel updated by {interaction.user.id} to channel {channel_id}"
            )
        except Exception as e:
            logger.error(
                f"Error in setlivechannel command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while setting the channel.", ephemeral=True
                )

    @app_commands.command(
        name="setlivemessage",
        description="Set the message that shows when someone goes live.",
    )
    @app_commands.describe(
        message="Input your message here",
        mentioned="Who are you @ing? (role mention or @everyone/@here)",
    )
    async def setlivemessage(
        self, interaction: discord.Interaction, message: str, mentioned: str
    ) -> None:
        """Set the live notification message."""
        if not is_authorized_user(interaction.user.id):
            logger.warning(
                f"Unauthorized /setlivemessage attempt by {interaction.user} (ID: {interaction.user.id}) "
                f"in {interaction.guild.name if interaction.guild else 'DM'}"
            )
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return

        user_type = "dev" if interaction.user.id == get_dev_id() else "twitch user"
        logger.info(
            f"Command /setlivemessage used by authorized {user_type} {interaction.user} (ID: {interaction.user.id}) "
            f"in {interaction.guild.name if interaction.guild else 'DM'}"
        )

        if not message or not message.strip():
            logger.warning(
                f"Empty message attempt in setlivemessage by {interaction.user.id}"
            )
            await interaction.response.send_message(
                "❌ Message cannot be empty.", ephemeral=True
            )
            return

        try:
            response = changemessage(newmessage=message, mentions=mentioned)
            await interaction.response.send_message(response, ephemeral=True)
            logger.info(f"Live message updated by {interaction.user.id}")
        except Exception as e:
            logger.error(
                f"Error in setlivemessage command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while setting the message.", ephemeral=True
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


def followstreamer(streamer: str) -> str:
    """Add a streamer to the watchlist."""
    if not streamer or not streamer.strip():
        return "❌ Streamer name cannot be empty."

    streamer = streamer.lower().strip()
    config = load_config()
    twitch_config = config.get("twitch", {})
    watchlist = twitch_config.get("watchlist", [])

    if streamer in watchlist:
        return f"❌ {streamer} is already on the list."

    watchlist.append(streamer)
    twitch_config["watchlist"] = watchlist
    config["twitch"] = twitch_config

    try:
        save_config(config)
        logger.info(f"Added {streamer} to watchlist")
        return f"✅ {streamer} has been successfully added to the list."
    except Exception as e:
        logger.error(f"Error in followstreamer: {e}", exc_info=True)
        return f"❌ An error occurred: {e}"


def unfollowstreamer(streamer: str) -> str:
    """Remove a streamer from the watchlist."""
    if not streamer or not streamer.strip():
        return "❌ Streamer name cannot be empty."

    streamer = streamer.lower().strip()
    config = load_config()
    twitch_config = config.get("twitch", {})
    watchlist = twitch_config.get("watchlist", [])

    if streamer not in watchlist:
        return f"❌ {streamer} is not in the list - cannot be removed."

    watchlist.remove(streamer)
    twitch_config["watchlist"] = watchlist
    config["twitch"] = twitch_config

    try:
        save_config(config)
        logger.info(f"Removed {streamer} from watchlist")
        return f"✅ {streamer} has been successfully removed from the list."
    except Exception as e:
        logger.error(f"Error in unfollowstreamer: {e}", exc_info=True)
        return f"❌ An error occurred: {e}"


def viewstreamers() -> list[str]:
    """Get the list of streamers in the watchlist."""
    config = get_twitch_config()
    return config.get("watchlist", [])


def changemessage(newmessage: str, mentions: str) -> str:
    """Change the live notification message."""
    config = load_config()
    twitch_config = config.get("twitch", {})

    try:
        live_msg = f"{mentions}! {newmessage}"
        twitch_config["live_msg"] = live_msg
        config["twitch"] = twitch_config
        save_config(config)
        logger.info("Updated live notification message")
        return f"✅ Your new message has been set.\nNew Message: {live_msg}"
    except Exception as e:
        logger.error(f"Error changing message: {e}", exc_info=True)
        return f"❌ An error occurred when changing the message: {e}"


def changelivechannel(channel_id: int) -> str:
    """Change the channel for live notifications."""
    config = load_config()
    twitch_config = config.get("twitch", {})

    try:
        twitch_config["channel_id"] = str(channel_id)
        config["twitch"] = twitch_config
        save_config(config)
        logger.info(f"Updated live notification channel to {channel_id}")
        return f"✅ The channel has been set to: <#{channel_id}>"
    except Exception as e:
        logger.error(f"Error changing channel: {e}", exc_info=True)
        return f"❌ An error occurred when changing the channel: {e}"


def streamerinlist(streamer: str) -> bool:
    """Check if a streamer is in the watchlist."""
    watchlist = viewstreamers()
    return streamer.lower() in [s.lower() for s in watchlist]


async def setup(bot: commands.Bot):
    """Setup function for the Twitch cog."""
    await bot.add_cog(Twitch(bot))
