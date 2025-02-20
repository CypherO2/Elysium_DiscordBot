<p align="center"><a href="https://CypherO2.github.io/work/#/ElysiumBot"><img class="logoimg" src="https://github.com/CypherO2/Elysium_DiscordBot/blob/main/assets/ElysiumBotIcon.png?raw=true" width="175" height="175" href="https://ritabot.org/"></a></p>
<h1 align="center">𝓔𝓵𝔂𝓼𝓲𝓾𝓶</h1>
<p align="center">A multi-purpose discord bot, with an expansive selection of commands.</p>

------

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
- [Requirements 🔃](#requirements-)
  - [Python Requirements](#python-requirements)
  - [Twitch Requirements](#twitch-requirements)
  - [Discord Requirements](#discord-requirements)
- [Setup 🖥️](#setup-️)
  - [Discord Setup](#discord-setup)
  - [Python Setup](#python-setup)
    - [Step 1](#step-1)
    - [Step 2](#step-2)
    - [Step 3](#step-3)
  - [Twitch Integration Setup](#twitch-integration-setup)
- [Support 🤝](#support-)
- [License 🪪](#license-)

## Commands 🌐

|Command|Description|
|:------|:---------|
|**/help**|Displays the help menu - contains a list of commands. |
|**/runtime**|Shows how long the bot has been online. |
|**/watchlist {action} {streamer_name}**| Adds a Twitch streamer to the list of streamers to alert when they go Live. |
|**/setlivechannel {channel}**| Allows for the changing of the channel the bot sends notifications in. |
|**/setlivemessage {message} {@Role}**| Allows for the creation of custom messages for stream notifications. |
|**/shutdown**| Shuts the bot down displaying a message to the bot log. |
|**/maintainance**|Shuts the bot down displaying a message to the bot log about being down for maintainance. |

## Requirements 🔃

### Python Requirements
|Requirement|Version|
|:----------|:-----:|
| discord.py | >v2.5.0 |
| requests | >v2.31.0|
| typing | >v3.7.4.3 |

### Twitch Requirements
Having a twitch developer account with 2FA enabled.

### Discord Requirements
Having a discord developer account with 2FA enabled.

## Setup 🖥️

### Discord Setup

1) Go to the [Discord Developer Portal](https://discord.com/developers) and `login`.
2) Click on `New Application` in the upper-right hand side of your screen, under your profile picture.
3) Name your application, accept the Discord Developer Terms of Service and Developer Policy and click `Create`.
4) Now navigate to `OAuth2` in the sidebar and scroll to `OAuth2 URL Generator`.
5) Select `bot` as your scope and then set your bot's permissions, copy the Generated Url and save it in a safe place.
6) Next navigate to `Bot` on the sidebar and scroll to `Privileged Gateway Intents` and check `Presence Intent`, `Server Member Intent` and `Message Content Intent`
7) Save all your changes as they come.

------
### Python Setup

#### Step 1
Ensure you have Python `v3.11` or greater installed.

#### Step 2
Ensure that the following are installed:
- discord.py
- requests
- asyncio
- typing

#### Step 3
In the root directory create a `.env` file.
inside the `.env` file you will have a constant called `ELYSIUM_TOKEN`.

Grab your Bot Token from the [Discord Developer Portal](https://discord.com/developers) and put it into your `.env` file like so:
```.env
ELYSIAN_TOKEN="KUFHSDIUHKUh-UHLIUkudshliughj89w3eyr"
```
> [!CAUTION]
> Never share your discord bot token, it can be used to control your bot!!!

------
### Twitch Integration Setup

> [!NOTE]
> Check out [this guide](https://github.com/Partymann2000/python-twtich-notification-system) by Partymann2000.

1) Go to the [Twitch Developer Portal](https://dev.twitch.tv/) and `login`.
2) Click on `Your Console`, should be located in the top-right in the navbar.
3) Navigate to `Applications` and click `Register your application`.
4) Name your application (Cannot contain the work Twitch).
5) Set the `OAuth Redirect URL` field to `https://localhost/`.
6) Set the `Catagory` to Other and complete the Captcha and click `Create`.
7) Now click on `Manage` on your application.
8) Grab you `clientID` and `clientSecret` and put them in your `config.json` file.

>[!CAUTION]
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

9) Don't forget to rename `config_template.json` to `config.json` once its been populated.
10) Set the `channel_id` to the discord channel you want the bot to send the message in
11)  Populate your `watchlist` with the streamers you want to recieve notifications for.

## Support 🤝
To get support for the Elysium discord bot, feel free to :
- Open an issue on Github
- Join the [discord server]()
- Or to visit my [website](https://CypherO2.github.io/work/#/ElysiumBot) 


## License 🪪

This repository is listed under [the MIT License](/LICENSE)
