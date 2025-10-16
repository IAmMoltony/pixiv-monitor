#!/usr/bin/python3

# standard imports
import argparse
import json
import threading
import time
import os
import datetime
import logging
import logging.handlers
import smtplib
import sys
import queue
import random
import pathlib

# pixiv
from pixivpy3 import *
from pixivpy3.utils import PixivError

# third-party imports
import requests
import dotenv

# my imports
from tokenswitcher import TokenSwitcher
import illustlog
import settings
import notify
from pixivmodel import PixivIllustration
from hook import Hook
from seen import SeenIllustrations
import utility
from monitor import Monitor

def init_logging(config, debug_log):
    log_config = config.get("log", settings.DEFAULT_LOG_CONFIG)
    pathlib.Path(log_config["directory"]).mkdir(parents=True, exist_ok=True)

    string_level = log_config.get("level", "info")
    log_level = logging.INFO
    if debug_log:
        log_level = logging.DEBUG
    else:
        match string_level:
            case "debug":
                log_level = logging.DEBUG
            case "info":
                log_level = logging.INFO
            case "warning":
                log_level = logging.WARNING
            case "error":
                log_level = logging.ERROR
            case "critical":
                log_level = logging.CRITICAL

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s]:%(levelname)s %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_config["directory"], "pixiv-monitor.log"), encoding="utf-8", maxBytes=log_config["max_size"] * 1024 * 1024, backupCount=log_config["backup_count"])
    file_handler.setLevel(log_level)
    if debug_log:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

def list_artists(config, api, token_switcher):
    artist_ids = config["artist_ids"]
    print(f"Will list {len(artist_ids)} artists.")
    for artist_id in artist_ids:
        while True:
            user_json = api.user_detail(artist_id)
            if "error" in user_json:
                error_message = user_json["error"]["message"]
                if "invalid_grant" in error_message:
                    # TODO create some sort of function thing for this oauth handler thing
                    logging.getLogger().debug("OAuth error detected; refreshing access token")
                    utility.handle_oauth_error(api, token_switcher)
                    continue
                if "Rate Limit" in error_message:
                    #logging.getLogger().info("We got rate limited; trying again in 5 seconds...")
                    token_switcher.switch_token()
                    token_switcher.refresh_token()
                    #logging.getLogger().info(f"Switch to account {token_switcher.current_token}")
                    api.set_auth(token_switcher.get_access_token())
                    continue
            user_id = user_json["user"]["id"]
            user_name = user_json["user"]["name"]
            user_account = user_json["user"]["account"]
            print(f"{user_name} | ID: {user_id} | @{user_account}")
            break

def load_hooks(config):
    if "hooks" not in config:
        return []
    
    hooks = []
    for chook in config["hooks"]:
        hooks.append(Hook(chook))
    return hooks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-artists", action="store_true", help="List artists and exit.")
    parser.add_argument("--debug-log", action="store_true", help="Output debugging logs in the console.")
    args = parser.parse_args()

    config = settings.get_config()
    init_logging(config, args.debug_log)
    if not settings.check_config(config):
        sys.exit(1)
    hooks = load_hooks(config)
    seen = SeenIllustrations()

    check_interval = config["check_interval"]

    dotenv.load_dotenv()

    logging.getLogger().info("pixiv-monitor has started")
    
    if sys.platform.startswith("win"):
        try:
            import winotify
        except ImportError:
            logging.getLogger().warn("winotify isn't installed. System notifications will not be shown")

    token_switcher = TokenSwitcher(config)

    api = AppPixivAPI()
    api.set_auth(token_switcher.get_access_token())

    if args.list_artists:
        list_artists(config, api, token_switcher)
        sys.exit(0)

    Monitor(check_interval, config["artist_ids"], config, api, seen, token_switcher, hooks).run()
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Gracefully stopping...")
        sys.exit(0)
