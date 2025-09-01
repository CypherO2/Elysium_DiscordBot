<p align="center"><a href="https://CypherO2.github.io/work/#/ElysiumBot"><img class="logoimg" src="https://github.com/CypherO2/Elysium_DiscordBot/blob/main/assets/ElysiumBotIcon.png?raw=true" width="175" height="175" href="https://ritabot.org/"></a></p>
<h1 align="center">𝓔𝓵𝔂𝓼𝓲𝓾𝓶</h1>
<p align="center">A multi-purpose discord bot, with an expansive selection of commands.</p>

---

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/CypherO2/Elysium_DiscordBot.svg)](https://github.com/CypherO2/Elysium_DiscordBot/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/CypherO2/Elysium_DiscordBot.svg)](https://github.com/CypherO2/Elysium_DiscordBot/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

<h2>Contents 📃</h2>

> [!Note]
> The instance of this bot, that I host, is not available in any servers beyond the support server and a friend's. This is because it has very limited functionality at the moment.

- [Commands 🌐](#commands-)
  - [Twitch](#twitch)
  - [Moderation](#moderation)
  - [Utility](#utility)
  - [Music](#music)
- [Requirements 🔃](#requirements-)
  - [Python Requirements](#python-requirements)
  - [Twitch Requirements](#twitch-requirements)
  - [Discord Requirements](#discord-requirements)
- [Setup 🖥️](#setup-️)
  - [Discord Setup](#discord-setup)
  - [Python Setup](#python-setup)
  - [Twitch Integration Setup](#twitch-integration-setup)
- [Support 🤝](#support-)
- [License 🪪](#license-)

## Commands 🌐

### Twitch

| Command                                          | Description                                                                                                                                                                                                       |
| :----------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **/watchlist {show/remove/add} {streamer_name}** | Allows for the managing of the Twitch streamer list for to LIVE alerts - the streamer name is only needed when adding or removing and must be as is shown in their link e.g. `https://twitch.tv/{streamer_name}`. |
| **/setlivechannel {channel}**                    | Allows for the changing of the channel the bot sends notifications in. The channel must be input using discord's in-built channel handling e.g. `#{channel}`                                                      |
| **/setlivemessage {message} {@Role}**            | Allows for the creation of custom messages for stream notifications. The role must be added using the discord in-built role handling e.g. `@{role}`                                                               |

### Moderation

| Command | Description |
| :------ | :---------- |

### Utility

| Command                      | Description                                                                                                                                                                                                                                  |
| :--------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **/help**                    | Displays the help menu - contains a list of commands.                                                                                                                                                                                        |
| **/runtime**                 | Shows how long the bot has been online.                                                                                                                                                                                                      |
| **/shutdown {reason}**       | Shuts the bot down displaying a message to the bot log.                                                                                                                                                                                      |
| **/suggestion {suggestion}** | This command allows for the user to send a suggestion for update to the bot. (it is suggested that you keep the channel id for this the same as usual if you are deploying it on your own - so that suggestions might reach me and be added) |

### Music

| Command               | Description                                                    |
| :-------------------- | :------------------------------------------------------------- |
| **!play {song name}** | plays the selected song as long as the user is in a voice chat |
| **!skip**             | skips current song                                             |
| **!queue**            | displays the current song queue                                |
| **!stop**             | stops the bot from playing                                     |
| **!pause**            | pauses the current song                                        |
| **!resume**           | resumes the current song when paused                           |

## Requirements 🔃

### Python Requirements

| Requirement |  Version  |
| :---------- | :-------: |
| discord.py  |  >v2.5.0  |
| requests    | >v2.31.0  |
| typing      | >v3.7.4.3 |

### Twitch Requirements

Having a twitch developer account with 2FA enabled.

### Discord Requirements

Having a discord developer account with 2FA enabled.

## Setup 🖥️

### Discord Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers) and `login`.
2. Click on `New Application` in the upper-right hand side of your screen, under your profile picture.
3. Name your application, accept the Discord Developer Terms of Service and Developer Policy and click `Create`.
4. Now navigate to `OAuth2` in the sidebar and scroll to `OAuth2 URL Generator`.
5. Select `bot` as your scope and then set your bot's permissions, copy the Generated Url and save it in a safe place.
6. Next navigate to `Bot` on the sidebar and scroll to `Privileged Gateway Intents` and check `Presence Intent`, `Server Member Intent` and `Message Content Intent`
7. Save all your changes as they come.

---

### Python Setup

> [!CAUTION]
> Never share your discord bot token, it can be used to control your bot!!!

1. Ensure you have Python `v3.11` or greater installed and ensure that the following are installed:

   - discord.py
   - requests
   - asyncio
   - typing

2. In the root directory create a `.env` file.
   inside the `.env` file you will have a constant called `ELYSIUM_TOKEN`. Grab your Bot Token from the [Discord Developer Portal](https://discord.com/developers) and put it into your `.env` file like so:
   `.env
     ELYSIAN_TOKEN="KUFHSDIUHKUh-UHLIUkudshliughj89w3eyr"
     `

3. Edit the `main.py` file's constants, you'll need to change the `public_log` and `private_log` to the discord channel ids in which you want bot info such as, turning on and off to be displayed.

   Set the `dev_id` to the discord user id of yourself or the person managing the bot.

   Finally, change `twcord_userid` to the discord user id of the person that will have control over the bot's twitch notification commands.

   When your done it should look like so:

   ```py
   # Constants #
   public_log = 1234227629557547029  # Change to you public bot log channel ID
   private_log = 1234227628924207283  # Change to you private bot log channel ID
   dev_id = 876876129368150018  # If you are hosting this bot, change this to your Discord UserID
   twcord_userid = (
      972663150455451689  # The ID of the person handling the bot's Twitch notifications.
   )
   ```

---

### Twitch Integration Setup

> [!NOTE]
> Check out [this guide](https://github.com/Partymann2000/python-twtich-notification-system) by Partymann2000.

1. Go to the [Twitch Developer Portal](https://dev.twitch.tv/) and `login`.
2. Click on `Your Console`, should be located in the top-right in the navbar.
3. Navigate to `Applications` and click `Register your application`.
4. Name your application (Cannot contain the work Twitch).
5. Set the `OAuth Redirect URL` field to `https://localhost/`.
6. Set the `Catagory` to Other and complete the Captcha and click `Create`.
7. Now click on `Manage` on your application.
8. Grab you `clientID` and `clientSecret` and put them in your `config.json` file.

> [!CAUTION]
> Never share your ClientID or ClientSecret!!!

```json
config.json
{
    "twitch": {
        "client_id": "clientID",
        "client_secret": "clientSecret",
        "access_token": "xxx",
        "channel_id": 6523487523834,
        "expire_date": 1669483138,
        "watchlist": [
            "streamer1",
            "streamer2",
            "streamer3"
        ]
    }
}
```

9. Don't forget to rename `config_template.json` to `config.json` once its been populated.
10. Set the `channel_id` to the discord channel you want the bot to send the message in
11. Populate your `watchlist` with the streamers you want to recieve notifications for.

## Support 🤝

To get support for the Elysium discord bot, feel free to :

- Open an issue on Github
- Join the [discord server]()
- Or to visit my [website](https://CypherO2.github.io/work/#/ElysiumBot)

## License 🪪

This repository is listed under [the MIT License](/LICENSE)
