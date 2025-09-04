import discord
import json
import requests
import os
from typing import Optional
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta


allowed_mentions = discord.AllowedMentions(roles=True)
twcord_userid = (
    972663150455451689  # The ID of the person handling the bot's Twitch notifications.
)


# Get the absolute path to the config file
def get_config_path():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one directory and look for config.json
    config_path = os.path.join(script_dir, "..", "config.json")
    return os.path.abspath(config_path)


def load_config():
    config_path = get_config_path()
    print(f"Loading config from: {config_path}", flush=True)
    try:
        with open(config_path) as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print(f"Config file not found at: {config_path}", flush=True)
        # Try alternative paths
        alternatives = [
            "./config.json",
            "../config.json",
            "config.json"
        ]
        for alt_path in alternatives:
            try:
                abs_alt_path = os.path.abspath(alt_path)
                print(f"Trying alternative path: {abs_alt_path}", flush=True)
                with open(alt_path) as config_file:
                    print(f"Successfully loaded config from: {abs_alt_path}", flush=True)
                    return json.load(config_file)
            except FileNotFoundError:
                continue
        raise FileNotFoundError("Could not find config.json in any of the expected locations")


def save_config(config):
    config_path = get_config_path()
    print(f"Saving config to: {config_path}", flush=True)
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)


def get_app_access_token():
    config = load_config()
    params = {
        "client_id": config["twitch"]["client_id"],
        "client_secret": config["twitch"]["client_secret"],
        "grant_type": "client_credentials",
    }

    response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
    access_token = response.json()["access_token"]
    print(access_token, flush=True)
    return access_token


# Berechne die UNIX Zeit für 60 Tage in der Zukunft in diesem format: <t:UNIXTIME:R
def unix_time():
    now = datetime.now()
    future = now + timedelta(weeks=3)
    unix_time = future.timestamp()
    return int(unix_time)


def get_users(login_names):
    config = load_config()
    params = [("login", login) for login in login_names]

    headers = {
        "Authorization": "Bearer {}".format(config["twitch"]["access_token"]),
        "Client-Id": config["twitch"]["client_id"],
    }

    response = requests.get(
        "https://api.twitch.tv/helix/users", params=params, headers=headers
    )
    return {entry["login"]: entry["id"] for entry in response.json().get("data", [])}


def get_streams(users):
    config = load_config()
    params = []
    for user_id in set(users.values()):  # Use set() to ensure unique user IDs
        params.append(("user_id", user_id))

    headers = {
        "Authorization": "Bearer {}".format(config["twitch"]["access_token"]),
        "Client-Id": config["twitch"]["client_id"],
    }

    response = requests.get(
        "https://api.twitch.tv/helix/streams", params=params, headers=headers
    )

    streams_data = response.json().get("data", [])
    print(f"Streams data: {streams_data}", flush=True)  # Debugging response

    print({entry["user_login"]: entry for entry in streams_data}, flush=True)
    return {entry["user_login"]: entry for entry in streams_data}


# Make online_users a class variable instead of global
class twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.online_users = {}  # Move to instance variable
        print(f"Current working directory: {os.getcwd()}", flush=True)
        print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}", flush=True)
        print(f"Config path will be: {get_config_path()}", flush=True)
        print("Twitch cog initialized (but loops not started yet)", flush=True)

    async def cog_load(self):
        print("Twitch cog loaded – starting tasks", flush=True)

        if not self.check_twitch_access_token.is_running():
            self.check_twitch_access_token.start()
            print("Started access token loop", flush=True)
        else:
            print("Access token loop already running", flush=True)

        if not self.check_twitch_online_streamers.is_running():
            self.check_twitch_online_streamers.start()
            print("Started streamer check loop", flush=True)
        else:
            print("Streamer check loop already running", flush=True)

    async def cog_unload(self):
        """Clean up tasks when cog is unloaded"""
        if self.check_twitch_access_token.is_running():
            self.check_twitch_access_token.cancel()
        if self.check_twitch_online_streamers.is_running():
            self.check_twitch_online_streamers.cancel()

    def get_notifications(self):
        config = load_config()
        users = get_users(config["twitch"]["watchlist"])
        streams = get_streams(users)

        notifications = []
        for user_name in config["twitch"]["watchlist"]:
            print(f"Checking user: {user_name}", flush=True)

            if user_name not in self.online_users:
                self.online_users[user_name] = None  # Start as None to signify offline
                print(f"Initializing {user_name} as offline.", flush=True)

            if user_name not in streams:
                self.online_users[user_name] = None  # User is not online
                print(f"{user_name} is offline.", flush=True)
            else:
                stream_data = streams[user_name]
                print(f"{user_name} is online. Stream details: {stream_data}", flush=True)

                # Convert the started_at string to a datetime object
                started_at = datetime.strptime(
                    stream_data["started_at"], "%Y-%m-%dT%H:%M:%SZ"
                )

                # Print for debugging
                print(f"Checking if {started_at} > {self.online_users[user_name]}", flush=True)

                # Ensure we are comparing datetime objects
                if self.online_users[user_name] is None or started_at > self.online_users[user_name]:
                    print(f"Adding notification for {user_name}", flush=True)  # Debug line
                    notifications.append(stream_data)
                    self.online_users[user_name] = started_at  # Update with the new started_at

        print(f"Notifications: {notifications}", flush=True)  # Debug line
        return notifications

    @tasks.loop(minutes=60)  # Changed from 1 minute to 60 minutes
    async def check_twitch_access_token(self):
        try:
            print(f"Running Twitch access token check at {datetime.now()}", flush=True)
            current_time = datetime.now().timestamp()
            config = load_config()
            
            if int(current_time) >= config["twitch"]["expire_date"]:
                access_token = get_app_access_token()
                config["twitch"]["access_token"] = access_token
                config["twitch"]["expire_date"] = unix_time()
                save_config(config)
                print("Access token regenerated", flush=True)
            else:
                print("Access token still valid", flush=True)
        except Exception as e:
            print(f"Error in check_twitch_access_token: {e}", flush=True)

    @tasks.loop(seconds=90)
    async def check_twitch_online_streamers(self):
        try:
            config = load_config()
            print("Running streamer check loop", flush=True)
            
            channel_id = int(config["twitch"]["channel_id"])
            channel = self.bot.get_channel(channel_id)
            print(f"🔍 Checking channel_id: {channel_id} (type: {type(channel_id)})")
            print(f"📢 Found channel: {channel}")
            
            if not channel:
                print("Channel not found, skipping notification check", flush=True)
                return

            live_message = config["twitch"]["live_msg"]
            notifications = self.get_notifications()
            
            for notification in notifications:
                game = "{}".format(notification["game_name"])
                if game == "":
                    embed = discord.Embed(
                        title="{}".format(notification["title"]),
                        url="https://twitch.tv/{}".format(notification["user_login"]),
                        description="[Watch](https://twitch.tv/{})".format(
                            notification["user_login"]
                        ),
                        color=0x6034B2,
                    )
                    embed.set_author(
                        name="{} is now live on Twitch!".format(notification["user_name"]),
                        url="https://twitch.tv/{}".format(notification["user_login"]),
                    )
                    embed.add_field(name="Game", value="Unknown", inline=True)
                    embed.add_field(
                        name="Viewers",
                        value="{}".format(notification["viewer_count"]),
                        inline=True,
                    )
                    embed.set_image(
                        url="https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg?time=1526732772".format(
                            notification["user_login"]
                        )
                    )
                    await channel.send(
                        live_message, allowed_mentions=allowed_mentions, embed=embed
                    )
                else:
                    embed = discord.Embed(
                        title="{}".format(notification["title"]),
                        url="https://twitch.tv/{}".format(notification["user_login"]),
                        description="[Watch Here](https://twitch.tv/{})".format(
                            notification["user_login"]
                        ),
                        color=0x6034B2,
                    )
                    embed.set_author(
                        name="{} is now live on Twitch!".format(notification["user_name"]),
                        url="https://twitch.tv/{}".format(notification["user_login"]),
                    )
                    embed.add_field(
                        name="Game",
                        value="{}".format(notification["game_name"]),
                        inline=True,
                    )
                    embed.add_field(
                        name="Viewers",
                        value="{}".format(notification["viewer_count"]),
                        inline=True,
                    )
                    embed.set_image(
                        url="https://static-cdn.jtvnw.net/previews-ttv/live_user_{}-1920x1080.jpg?time=1526732772".format(
                            notification["user_login"]
                        )
                    )
                    await channel.send(
                        live_message, allowed_mentions=allowed_mentions, embed=embed
                    )
        except Exception as e:
            print(f"Error in check_twitch_online_streamers: {e}", flush=True)

    @app_commands.command(
        name="watchlist",
        description="Edit/ Show the list of Streamer",
    )
    @app_commands.describe(
        action="What do you want to do?",
        streamername="Who you are? (Not needed if your only viewing the list)",
    )
    async def watchlist(
        self,
        interaction: discord.Interaction,
        action: str,
        streamername: Optional[str],
    ):
        if interaction.user.id != twcord_userid:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        
        if action.lower() == "add":
            response = followstreamer(streamer=streamername)
            response = response.replace(", ", "\n")
            await interaction.response.send_message(response, ephemeral=True)
        elif action.lower() == "remove":
            response = unfollowstreamer(streamer=streamername)
            await interaction.response.send_message(response, ephemeral=True)
        elif action.lower() == "show":
            response = viewstreamers()
            embed = discord.Embed(
                title="Streamer List [Twitch]",
                description="Here is the list of streamers your listening for.",
            )
            for streamer in response:
                embed.add_field(name=f"{streamer}", value="")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="setlivechannel",
        description="Choose the channel you want to send the live notifications in.",
    )
    @app_commands.describe(channel="channel?")
    async def setlivechannel(self, interaction: discord.Interaction, channel: str):
        if interaction.user.id != twcord_userid:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        response = changelivechannel(channel=channel)
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(
        name="setlivemessage",
        description="Set the message that shows when someone goes live.",
    )
    @app_commands.describe(
        message="Input your message here", mentioned="Who are you @ing?"
    )
    async def setlivemessage(
        self, interaction: discord.Interaction, message: str, mentioned: str
    ) -> None:
        if interaction.user.id != twcord_userid:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.", ephemeral=True
            )
            return
        response = changemessage(newmessage=message, mentions=mentioned)
        await interaction.response.send_message(response, ephemeral=True)


def followstreamer(streamer):
    config = load_config()
    streamer = streamer.lower()
    if streamerinlist(streamer, config):
        return f"{streamer} is already on the list."
    else:
        config["twitch"]["watchlist"].append(streamer)
        try:
            save_config(config)
            return f"{streamer} has been successfully added to the list."
        except Exception as e:
            print(f"An error has occured in followstreamer : {e}", flush=True)
            return f"An error has occured in followstreamer : {e}"


def unfollowstreamer(streamer):
    config = load_config()
    streamer = streamer.lower()
    if not streamerinlist(streamer, config):
        return f"{streamer} is not in the list - cannot be removed."
    else:
        config["twitch"]["watchlist"].remove(streamer)
        try:
            save_config(config)
            return f"{streamer} has been successfully removed from the list."
        except Exception as e:
            print(f"An error has occured in unfollowstreamer : {e}", flush=True)
            return f"An error has occured in unfollowstreamer : {e}"


def viewstreamers():
    config = load_config()
    return config["twitch"]["watchlist"]


def changemessage(newmessage, mentions):
    config = load_config()
    try:
        config["twitch"]["live_msg"] = f"{mentions}! {newmessage}"
        save_config(config)
        newmessage = config["twitch"]["live_msg"]
        return f"Your new message has been set.\nNew Message = {newmessage}"
    except Exception as e:
        return f"An Error occurred when changing the message -> {e}"


def changelivechannel(channel):
    config = load_config()
    try:
        channel = channel.replace("<#", "").replace(">", "")
        config["twitch"]["channel_id"] = channel
        save_config(config)
        return f"The channel has been set to: {channel}"
    except Exception as e:
        return f"An Error occurred when changing the channel -> {e}"


def streamerinlist(streamer: str, config=None) -> bool:
    if config is None:
        config = load_config()
    streamer_list = config["twitch"]["watchlist"]
    return streamer in streamer_list


async def setup(bot):
    await bot.add_cog(twitch(bot))