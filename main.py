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
from loginit import init_logging

def list_artists(config, api, token_switcher):
    artist_ids = config["artist_ids"]
    print(f"Will list {len(artist_ids)} artists.")
    for artist_id in artist_ids:
        user_json = utility.api_wrapper(api, token_switcher, api.user_detail, artist_id)
        user_id = user_json["user"]["id"]
        user_name = user_json["user"]["name"]
        user_account = user_json["user"]["account"]
        print(f"{user_name} | ID: {user_id} | @{user_account}")

def load_hooks(config):
    if "hooks" not in config:
        return []
    
    hooks = []
    for chook in config["hooks"]:
        hooks.append(Hook(chook))
    return hooks

def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-artists", action="store_true", help="List artists and exit.")
    parser.add_argument("--debug-log", action="store_true", help="Output debugging logs in the console.")
    return parser.parse_args()

def main():
    args = parse_cli_args()
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

    token_switcher = TokenSwitcher(config["num_accounts"])

    api = AppPixivAPI()
    api.set_auth(token_switcher.get_access_token())

    if args.list_artists:
        list_artists(config, api, token_switcher)
        sys.exit(0)

    if "monitors" in config:
        monitors = []
        for monitor in config["monitors"]:
            monitors.append(Monitor.from_json(monitor, config, api, seen, token_switcher, hooks))
        for monitor in monitors:
            monitor.run()
    else:
        Monitor(check_interval, config["artist_ids"], config, api, seen, token_switcher, hooks, config.get("num_threads", 3)).run()
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Gracefully stopping...")
        sys.exit(0)
