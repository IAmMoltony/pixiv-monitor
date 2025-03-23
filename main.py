#!/usr/bin/python3

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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pixivpy3 import *
from pixivpy3.utils import PixivError

import requests
import dotenv

import illustlog
import settings
import notify
from pixivmodel import PixivIllustration

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

def init_logging(config):
    log_config = config.get("log", settings.DEFAULT_LOG_CONFIG)
    pathlib.Path(log_config["directory"]).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)
    file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_config["directory"], "pixiv-monitor.log"), encoding="utf-8", maxBytes=log_config["max_size"] * 1024 * 1024, backupCount=log_config["backup_count"])
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
            logging.getLogger().error("Error sending e-mail: %s", exc)
        finally:
            smtp.quit()

USER_AGENT = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"

def get_new_access_token():
    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": os.getenv("REFRESH_TOKEN"),
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30
    )
    
    data = response.json()
    os.environ["REFRESH_TOKEN"] = data["refresh_token"] # pretty sure its constant
    return data["access_token"]

def handle_oauth_error(api):
    logging.getLogger().info("Refreshing access token")
    access_token = get_new_access_token()
    api.set_auth(access_token)

def get_json_illusts(api, artist_id):
    user_illusts_json = None
    while True:
        try:
            user_illusts_json = api.user_illusts(artist_id)
            if "error" in user_illusts_json:
                error_message = user_illusts_json["error"]["message"]
                if "invalid_grant" in error_message:
                    logging.getLogger().info("OAuth error detected; refreshing access token")
                    handle_oauth_error(api)
                    continue
                if "Rate Limit" in error_message:
                    #logging.getLogger().info("We got rate limited; trying again in 5 seconds...")
                    time.sleep(5)
                    continue
                logging.getLogger().error("Unknown error. Please handle it properly. %s", user_illusts_json)
                user_illusts_json = api.user_illusts(artist_id)
            break
        except Exception as e:
            if not isinstance(e, KeyboardInterrupt) and not isinstance(e, SystemExit):
                logging.getLogger().error("Unhandled exception while trying to fetch illustrations: %s. Retrying in 5 seconds.", e)
                time.sleep(5)
                continue
    return user_illusts_json

def illust_worker(api, seen, artist_queue, config):
    while True:
        try:
            artist_id = artist_queue.get()
            if artist_id is None:
                break

            user_illusts_json = get_json_illusts(api, artist_id)
            if not user_illusts_json:
                continue

            illusts = user_illusts_json["illusts"]
            num_new_illusts = 0
            for illust_json in illusts:
                illust = PixivIllustration.from_json(illust_json)
                if not seen.query_illust(illust.iden):
                    num_new_illusts += 1
                    seen.add_illust(illust.iden)
                    print(f"[{hrdatetime()}] \033[0;32mFound new illustration:\033[0m\n{str(illust)}\n")

                    log_message = f"New illustration: pixiv #{illust.iden} '{illust.title}' by {illust.user.name} (@{illust.user.account}). Tags: {illust.get_tag_string(False)}"
                    logging.getLogger().info(log_message)

                    if not config["notifications_off"]:
                        notify.send_notification(f"'{illust.title}' by {illust.user.name} (@{illust.user.account})", illust.pixiv_link())
                    illustlog.log_illust(illust)

                    threading.Thread(target=send_email, args=(f"{illust.title} by {illust.user.name}", log_message, config), daemon=True).start()
            if "ntfy_topic" in config:
                if num_new_illusts > 1:
                    # as to not spam ntfy's servers, we send one (1) notification with a summary of the pictures
                    # link to the pixiv url instead of the individual pictures
                    notify.send_ntfy(config["ntfy_topic"], f"{num_new_illusts} new illustrations from {illust.user.name}", illust.user.pixiv_link())
                else:
                    # just like usual
                    notify.send_ntfy(config["ntfy_topic"], f"'{illust.title}' by {illust.user.name}", illust.pixiv_link())

            seen.flush()
        except Exception as e:
            if "crash_on_exception" in config and config["crash_on_exception"]:
                raise
            logging.getLogger().error("Error in worker thread: %s", e)
        finally:
            artist_queue.task_done()

def check_illustrations(check_interval, config, api, seen):
    artist_queue = queue.Queue()

    num_threads = config.get("num_threads", 3)
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=illust_worker, args=(api, seen, artist_queue, config), daemon=True)
        thread.start()
        threads.append(thread)

    shuffled_ids = random.sample(config["artist_ids"], len(config["artist_ids"]))

    while True:
        for artist_id in shuffled_ids:
            artist_queue.put(artist_id)

        artist_queue.join()
        time.sleep(check_interval)

def main():
    config = settings.get_config()
    init_logging(config)
    seen = SeenIllustrations()

    check_interval = config["check_interval"]

    dotenv.load_dotenv()

    logging.getLogger().info("pixiv-monitor has started")

    api = AppPixivAPI()
    api.set_auth(get_new_access_token())

    threading.Thread(target=check_illustrations, args=(check_interval, config, api, seen), daemon=True).start()
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Gracefully stopping...")
        sys.exit(0)
