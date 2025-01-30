#!/usr/bin/python3

from pixivpy3 import *
from pixivmodel import PixivUser, PixivIllustration
import illustlog
import settings
import json
import threading
import time
import os
import requests
import datetime
import logging
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SeenIllustrations:
    def __init__(self):
        self.lock = threading.Lock()
        self.seen_illusts = set()
        if os.path.exists("./seen.json"):
            with open("./seen.json", "r", encoding="utf8") as seen_json:
                jseen = json.load(seen_json)
                self.seen_illusts = set(jseen["illusts"])

    def flush(self):
        with open("./seen.json", "w", encoding="utf8") as seen_json:
            json.dump({"illusts": list(self.seen_illusts)}, seen_json)

    def add_illust(self, iden):
        with self.lock:
            self.seen_illusts.add(iden)

    def query_illust(self, iden):
        return iden in self.seen_illusts

def init_logging():
    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("pixiv-monitor.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s]:%(levelname)s %(message)s")
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

def hrdatetime():
    return datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S")

def send_email(subject, message_text, config):
    if "email" in config and config["email"]:
        smtp_config = config["smtp"]

        login = smtp_config["credentials"]["login"]
        password = smtp_config["credentials"]["password"]
        mail_host = smtp_config["mail_host"]["address"]
        mail_port = smtp_config["mail_host"]["port"]

        sender = smtp_config["from_address"]
        receiver = smtp_config["to_address"]

        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = f"pixiv-monitor alert - {subject}"
        message.attach(MIMEText(message_text, "plain"))

        try:
            smtp = smtplib.SMTP(mail_host, mail_port)
            smtp.starttls()
            smtp.login(login, password)
            smtp.sendmail(sender, receiver, message.as_string())
        except Exception as exc:
            logging.getLogger().error(f"Error sending e-mail: {exc}")
        finally:
            smtp.quit()

USER_AGENT = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"

def get_new_access_token(config):
    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": config["refresh_token"],
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30
    )
    
    data = response.json()
    config["access_token"] = data["access_token"]
    config["refresh_token"] = data["refresh_token"]
    settings.save_config(config)

def handle_oauth_error(api, config):
    logging.getLogger().info("Refreshing access token")
    get_new_access_token(config)
    api.set_auth(config["access_token"])

def check_artist(artist_id, api, config, seen):
    user_illusts_json = None
    while True:
        try:
            user_illusts_json = api.user_illusts(artist_id)
            if "error" in user_illusts_json:
                logging.getLogger().info(f"Pixiv returned error response: {user_illusts_json}")
                error_message = user_illusts_json["error"]["message"]
                if "invalid_grant" in error_message:
                    logging.getLogger().info("OAuth error detected; refreshing access token")
                    handle_oauth_error(api, config)
                elif "Rate Limit" in error_message:
                    logging.getLogger().info("We got rate limited; trying again")
                    continue # this is what I call the slam our head against the wall until the wall breaks technique
                else:
                    logging.getLogger().error("Unknown error. Should be handled properly.")
                user_illusts_json = api.user_illusts(artist_id)
            break
        except Exception as e:
            if isinstance(e, KeyboardInterrupt) or isinstance(e, SystemExit):
                logging.getLogger().error(f"Unhandled exception while trying to fetch illustrations: {e}")
                raise
    illusts = user_illusts_json["illusts"]
    for illust_json in illusts:
        illust = PixivIllustration.from_json(illust_json)
        if not seen.query_illust(illust.iden):
            seen.add_illust(illust.iden)
            print(f"[{hrdatetime()}] \033[0;32mFound new illustration:\033[0m\n{str(illust)}\n")
            log_message = f"New illustration: pixiv #{illust.iden} '{illust.title}' by {illust.user.name} (@{illust.user.account}). Tags: {illust.get_tag_string(False)}"
            logging.getLogger().info(log_message)
            illustlog.log_illust(illust)
            threading.Thread(target=send_email, args=(f"{illust.title} by {illust.user.name}", log_message, config), daemon=True).start()

def check_illustrations(check_interval, config, api, seen):
    while True:
        for artist_id in config["artist_ids"]:
            threading.Thread(target=check_artist, args=(artist_id, api, config, seen)).start()
        seen.flush()
        time.sleep(check_interval)

def main():
    init_logging()
    config = settings.get_config()
    seen = SeenIllustrations()

    if not settings.check_config(config):
        sys.exit(1)

    check_interval = config["check_interval"]
    
    api = AppPixivAPI()
    api.set_auth(config["access_token"])

    logging.getLogger().info("pixiv-monitor has started")
    
    threading.Thread(target=check_illustrations, args=(check_interval, config, api, seen), daemon=True).start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Gracefully stopping...")
        seen.flush()
        sys.exit(0)

if __name__ == "__main__":
    main()
