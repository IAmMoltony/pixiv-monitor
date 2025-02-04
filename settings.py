import json
import logging

def get_config():
    with open("./settings.json", "r", encoding="utf-8") as config_json:
        return json.load(config_json)

def save_config(config):
    with open("./settings.json", "w", encoding="utf-8") as config_json:
        config_json.write(json.dumps(config, indent=4))

def check_config(config):
    logger = logging.getLogger()

    if "artist_ids" not in config or len(config["artist_ids"]) == 0:
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

    if "email" not in config or not config["email"]:
        return True

    if "smtp" not in config:
        print("SMTP not configured. Halting.")
        logger.error("Config check failed: smtp settings not present")
        return False

    if "mail_host" not in config["smtp"]:
        print("SMTP mail host not specified. Halting.")
        logger.error("Config check failed: mail_host not specified in smtp settings")
        return False

    if "address" not in config["smtp"]["mail_host"]:
        print("SMTP mail host address not specified. Halting.")
        logger.error("Config check failed: address not specified in smtp mail_host settings")
        return False

    if not isinstance(config["smtp"]["mail_host"]["address"], str):
        print("SMTP mail host address must be a string value. Halting.")
        logger.error("Config check failed: smtp mail_host address is not a string value")
        return False

    if "port" not in config["smtp"]["mail_host"]:
        print("SMTP mail host port not specified. Halting.")
        logger.error("Config check failed: port not specified in smtp mail_host settings")
        return False

    if not isinstance(config["smtp"]["mail_host"]["port"], int):
        print("SMTP mail host address must be an integer value. Halting.")
        logger.error("Config check failed: smtp mail_host port is not a string value")
        return False

    if "from_address" not in config["smtp"]:
        print("SMTP sender address not specified. Halting.")
        logger.error("Config check failed: from_address not specified in smtp settings")
        return False

    if not isinstance(config["smtp"]["from_address"], str):
        print("SMTP sender address must be a string value. Halting.")
        logger.error("Config check failed: smtp from_address is not a string value")
        return False

    if "to_address" not in config["smtp"]:
        print("SMTP receiver address not specified. Halting.")
        logger.error("Config check failed: to_address not specified in smtp settings")
        return False

    if not isinstance(config["smtp"]["to_address"], str):
        print("SMTP receiver address must be a string value. Halting.")
        logger.error("Config check failed: smtp to_address is not a string value")
        return False

    if "credentials" not in config["smtp"]:
        print("SMTP credentials not specified. Halting.")
        logger.error("Config check failed: credentials not specified in smtp settings")
        return False

    if "login" not in config["smtp"]["credentials"]:
        print("SMTP login not specified. Halting.")
        logger.error("Config check failed: login not specified in smtp credentials settings")
        return False

    if not isinstance(config["smtp"]["credentials"]["login"], str):
        print("SMTP login must be a string value. Halting.")
        logger.error("Config check failed: smtp credentials login is not a string value")
        return False

    if "password" not in config["smtp"]["credentials"]:
        print("SMTP password not specified. Halting.")
        logger.error("Config check failed: password not specified in smtp credentials settings")
        return False

    if not isinstance(config["smtp"]["credentials"]["password"], str):
        print("SMTP password must be a string value. Halting.")
        logger.error("Config check failed: smtp credentials password is not a string value")
        return False

    return True

