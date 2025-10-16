import json
import logging
import os
import sys

# TODO Rewrite this

DEFAULT_LOG_CONFIG = {
    "backup_count": 5,
    "max_size": 10,
    "directory": "log",
    "level": "info"
}

def get_config():
    if not os.path.exists("./settings.json"):
        print("Settings file not found. Please follow the setup instructions and try again.")
        sys.exit(1)
    with open("./settings.json", "r", encoding="utf-8") as config_json:
        return json.load(config_json)

def save_config(config):
    with open("./settings.json", "w", encoding="utf-8") as config_json:
        config_json.write(json.dumps(config, indent=4))

def check_config(config):
    logger = logging.getLogger()

    if ("artist_ids" not in config or len(config["artist_ids"]) == 0) and "monitors" not in config:
        print("No artist IDs specified. Halting.")
        logger.error("Config check failed: artist_ids not specified or empty")
        return False

    for artist_id in config["artist_ids"]:
        if artist_id < 1:
            print("Artist ID cannot be less than 1. Halting.")
            logger.error("Config check failed: one of the specified artist IDs is less than 1")
            return False
        if not isinstance(artist_id, int):
            print("Artist ID must be an integer value. Halting.")
            logger.error("Config check failed: one of the specified artist IDs is not an integer value")
            return False

    if "check_interval" not in config:
        config["check_interval"] = 60 * 5 # default value 5 minutes

    if not isinstance(config["check_interval"], int) and not isinstance(config["check_interval"], float):
        print("Check interval must be either an integer or floating-point value. Halting.")
        logger.error("Config check failed: check_interval is not an integer or float value")
        return False

    if "num_accounts" not in config:
        config["num_accounts"] = 1

    if not isinstance(config["num_accounts"], int):
        print("Number of accounts must be an integer value. Halting.")
        logger.error("Config check failed: num_accounts is not an integer value")
        return False

    if "log" not in config:
        config["log"] = DEFAULT_LOG_CONFIG

    return True
