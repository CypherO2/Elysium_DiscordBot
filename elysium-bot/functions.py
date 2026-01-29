import json
import os


def load_config():
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path) as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print(f"⚠️ Config file not found at: {config_path}")
        # Try alternative paths
        alternatives = [
            "./config.json",
            "../config.json",
            "config.json"
        ]
        for alt_path in alternatives:
            try:
                with open(alt_path) as config_file:
                    print(f"✅ Successfully loaded config from: {alt_path}")
                    return json.load(config_file)
            except FileNotFoundError:
                continue
        raise FileNotFoundError("Could not find config.json in any of the expected locations")
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing config file: {e}")
        raise

# Load config on import
try:
    config = load_config()
except Exception as e:
    print(f"⚠️ Warning: Could not load config: {e}")
    config = {}


