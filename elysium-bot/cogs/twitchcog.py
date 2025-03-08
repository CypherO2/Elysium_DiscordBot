import discord
import json
import asyncio
import datetime
import requests
import time
from typing import Optional
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, date, time, timezone, timedelta


allowed_mentions = discord.AllowedMentions(roles=True)
twcord_userid = (
    972663150455451689  # The ID of the person handling the bot's Twitch notifications.
)


def load_config():
    with open("elysium-bot/config.json") as config_file:
        return json.load(config_file)


def get_app_access_token():

    params = {
        "client_id": config["twitch"]["client_id"],
        "client_secret": config["twitch"]["client_secret"],
        "grant_type": "client_credentials",
    }

    response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
    access_token = response.json()["access_token"]
    print(access_token)
    return access_token


# Berechne die UNIX Zeit für 60 Tage in der Zukunft in diesem format: <t:UNIXTIME:R
def unix_time():
    now = datetime.now()
    future = now + timedelta(weeks=3)
    unix_time = future.timestamp()
    return int(unix_time)


def get_users(login_names):

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
    # print(f"Streams data: {streams_data}")  # Debugging response

    # print({entry["user_login"]: entry for entry in streams_data})
    return {entry["user_login"]: entry for entry in streams_data}


online_users = {}


def get_notifications():

    users = get_users(config["twitch"]["watchlist"])
    streams = get_streams(users)

    notifications = []
    for user_name in config["twitch"]["watchlist"]:
        # print(f"Checking user: {user_name}")

        if user_name not in online_users:
            online_users[user_name] = None  # Start as None to signify offline
            # print(f"Initializing {user_name} as offline.")

        if user_name not in streams:
            online_users[user_name] = None  # User is not online
            # print(f"{user_name} is offline.")
        else:
            stream_data = streams[user_name]
            # print(f"{user_name} is online. Stream details: {stream_data}")

            # Convert the started_at string to a datetime object
            started_at = datetime.strptime(
                stream_data["started_at"], "%Y-%m-%dT%H:%M:%SZ"
            )

            # Print for debugging
            # print(f"Checking if {started_at} > {online_users[user_name]}")

            # Ensure we are comparing datetime objects
            if online_users[user_name] is None or started_at > online_users[user_name]:
                print(f"Adding notification for {user_name}")  # Debug line
                notifications.append(stream_data)
                online_users[user_name] = started_at  # Update with the new started_at

    # print(f"Notifications: {notifications}")  # Debug line
    return notifications


def followstreamer(streamer):
    streamer = streamer.lower()
    if streamerinlist(streamer):
        return f"{streamer} is already on the list."
    else:
        config["twitch"]["watchlist"].append(streamer)
        try:
            with open("elysium-bot/config.json", "w") as config_file:
                json.dump(config, config_file, indent=4)
            return f"{streamer} has been successfully added to the list."
        except Exception as e:
            print(f"An error has occured in followstreamer : {e}")
            return f"An error has occured in followstreamer : {e}"


def unfollowstreamer(streamer):
    streamer = streamer.lower()
    if not streamerinlist(streamer):
        return f"{streamer} is not in the list - cannot be removed."
    else:
        config["twitch"]["watchlist"].remove(streamer)
        try:
            with open("elysium-bot/config.json", "w") as config_file:
                json.dump(config, config_file, indent=4)
            return f"{streamer} has been successfully removed from the list."
        except Exception as e:
            print(f"An error has occured in unfollowstreamer : {e}")
            return f"An error has occured in unfollowstreamer : {e}"


def viewstreamers():
    streamer_list = config["twitch"]["watchlist"]
    return streamer_list


def changemessage(newmessage, mentions):
    try:
        config["twitch"]["live_msg"] = f"{mentions}! {newmessage}"
        with open("elysium-bot/config.json", "w") as config_file:
            json.dump(config, config_file, indent=4)
        # print(f"Your new message has been set.\nNew Message = {newmessage}")
        newmessage = config["twitch"]["live_msg"]
        return f"Your new message has been set.\nNew Message = {newmessage}"
    except Exception as e:
        # print(f"An Error occurred when changing the message -> {e}")
        return f"An Error occurred when changing the message -> {e}"


def changelivechannel(channel):
    # print(f"LIVE Channel : {channel}")
    try:
        channel = channel.replace("<#", "").replace(">", "")
        config["twitch"]["channel_id"] = channel
        with open("elysium-bot/config.json", "w") as config_file:
            json.dump(config, config_file, indent=4)
        return f"The channel has been set to: {channel}"
    except Exception as e:
        return f"An Error occurred when changing the channel -> {e}"


def streamerinlist(streamer: str) -> bool:
    streamer_list = config["twitch"]["watchlist"]
    if streamer in streamer_list:
        return True
    else:
        return False


class twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_twitch_online_streamers.start()
        self.check_twitch_access_token.start()
        print("check twitch online started")

    @tasks.loop(seconds=60)
    async def check_twitch_access_token(self):

        print("Access token is checked")
        time = datetime.now()
        current_time = time.timestamp()
        # print(f"Current time: {current_time}")
        # print(f"Expire date: {config.get('twitch', {}).get('expire_date', 'MISSING')}")
        # print(int(current_time) >= config["twitch"]["expire_date"])
        if int(current_time) >= config["twitch"]["expire_date"]:
            access_token = get_app_access_token()
            config["twitch"]["access_token"] = access_token
            config["twitch"]["expire_date"] = unix_time()
            print("The access token was regenerated")
            with open("elysium-bot/config.json", "w") as config_file:
                json.dump(config, config_file, indent=4)

    @tasks.loop(seconds=90)
    async def check_twitch_online_streamers(self):
        global config
        config = load_config()
        # print("Test loop 90")
        channel_id = int(config["twitch"]["channel_id"])
        channel = self.bot.get_channel(channel_id)
        # print(f"🔍 Checking channel_id: {channel_id} (type: {type(channel_id)})")
        # print(f"📢 Found channel: {channel}")  # Should NOT be None
        if not channel:
            return

        live_message = config["twitch"]["live_msg"]
        notifications = get_notifications()
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
            # response = response.
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


async def setup(bot):
    await bot.add_cog(twitch(bot))
