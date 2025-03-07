import discord
import json
import asyncio
import datetime
import requests
import time
from discord.ext import commands, tasks
from datetime import datetime, date, time, timezone, timedelta


allowed_mentions = discord.AllowedMentions(roles=True)


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


async def setup(bot):
    await bot.add_cog(twitch(bot))
