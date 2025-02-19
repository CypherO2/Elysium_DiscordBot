import json


with open("elysium-bot/config.json") as config_file:
    config = json.load(config_file)


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


def streamerinlist(streamer: str) -> bool:
    streamer_list = config["twitch"]["watchlist"]
    if streamer in streamer_list:
        return True
    else:
        return False
