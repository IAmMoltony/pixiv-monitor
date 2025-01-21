#!/usr/bin/python3

from pixivpy3 import *
import json
import threading
import time
import os
import requests
import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class PixivUser:
    def __init__(self, iden, name, account):
        self.iden = iden
        self.name = name
        self.account = account
    
    def __str__(self):
        return f"\033[0;36m{self.name}\033[0m (@{self.account})"
    
    @staticmethod
    def from_json(json_user):
        return PixivUser(json_user["id"], json_user["name"], json_user["account"])

class PixivTag:
    def __init__(self, name, translated_name):
        self.name = name
        self.translated_name = translated_name
    
    def __str__(self, use_color=True):
        if use_color:
            if self.translated_name is None:
                return "\033[0;31mR-18\033[0m" if self.name == "R-18" else f"\033[0;36m{self.name}\033[0m"
            return f"\033[0;36m{self.name} / {self.translated_name}\033[0m"
        if self.translated_name is None:
            return self.name
        return f"{self.name} / {self.translated_name}"
    
    @staticmethod
    def from_json(tag_json):
        return PixivTag(tag_json["name"], tag_json["translated_name"])
    
    @staticmethod
    def from_json_list(tags_json):
        tags = []
        for tag in tags_json:
            tags.append(PixivTag.from_json(tag))
        return tags

class PixivIllustration:
    def __init__(self, iden, title, caption, user, tags):
        self.iden = iden
        self.title = title
        self.caption = caption
        self.user = user
        self.tags = tags
    
    def __str__(self):
        return f"pixiv \033[0;36m#{self.iden}\033[0m\nTitle: \033[0;36m{self.title}\033[0m\nCaption: \033[0;36m{self.caption}\033[0m\nArtist: {str(self.user)}\nTags: {self.get_tag_string()}"

    def get_tag_string(self, use_color=True):
        return ", ".join(tag.__str__(use_color) for tag in self.tags)
    
    @staticmethod
    def from_json(json_illust):
        return PixivIllustration(
            json_illust["id"],
            json_illust["title"],
            json_illust["caption"],
            PixivUser.from_json(json_illust["user"]),
            PixivTag.from_json_list(json_illust["tags"])
        )

class SeenIllustrations:
    def __init__(self):
        self.seen_illusts = []
        if os.path.exists("./seen.json"):
            with open("./seen.json", "r", encoding="utf8") as seen_json:
                jseen = json.load(seen_json)
                self.seen_illusts = jseen["illusts"]

    def flush(self):
        with open("./seen.json", "w", encoding="utf8") as seen_json:
            json.dump({"illusts": self.seen_illusts}, seen_json)

    def add_illust(self, iden):
        self.seen_illusts.append(iden)

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

def get_config():
    with open("./settings.json", "r", encoding="utf-8") as config_json:
        return json.load(config_json)

def save_config(config):
    with open("./settings.json", "w", encoding="utf-8") as config_json:
        config_json.write(json.dumps(config, indent=4))

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
        message["Subject"] = f"{smtp_config['subject']} - {subject}"
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
    save_config(config)

def check_illustrations(check_interval, config, api, seen):
    while True:
        for artist_id in config["artist_ids"]:
            user_illusts_json = None
            while True:
                try:
                    user_illusts_json = api.user_illusts(artist_id)
                    if "error" in user_illusts_json:
                        logging.getLogger().info("Pixiv returned error response; refreshing access token.")
                        get_new_access_token(config)
                        api.set_auth(config["access_token"])
                        user_illusts_json = api.user_illusts(artist_id)
                    break
                except Exception as e:
                    if isinstance(e, KeyboardInterrupt) or isinstance(e, SystemExit):
                        raise
            illusts = user_illusts_json["illusts"]
            for illust_json in illusts:
                illust = PixivIllustration.from_json(illust_json)
                if not seen.query_illust(illust.iden):
                    seen.add_illust(illust.iden)
                    print(f"[{hrdatetime()}] \033[0;32mFound new illustration:\033[0m\n{str(illust)}\n")
                    log_message = f"New illustration: pixiv #{illust.iden} '{illust.title}' by {illust.user.name} (@{illust.user.account}). Tags: {illust.get_tag_string(False)}"
                    logging.getLogger().info(log_message)
                    send_email(f"{illust.title} by {illust.user.name}", log_message, config)
            seen.flush()
        time.sleep(check_interval)

def main():
    global seen
    global api

    init_logging()
    config = get_config()
    seen = SeenIllustrations()

    check_interval = config["check_interval"]
    
    api = AppPixivAPI()
    api.set_auth(config["access_token"])

    logging.getLogger().info("pixiv-monitor has started")
    
    threading.Thread(target=check_illustrations, args=(check_interval, config, api, seen), daemon=True).start()
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
