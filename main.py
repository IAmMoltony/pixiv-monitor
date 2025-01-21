from pixivpy3 import *
import json
import threading
import time
import os
import requests

class PixivUser:
    def __init__(self, iden, name, account):
        self.iden = iden
        self.name = name
        self.account = account
    
    def __str__(self):
        return f"user #{self.iden} '{self.name}' (@{self.account})"
    
    @staticmethod
    def from_json(json_user):
        return PixivUser(json_user["id"], json_user["name"], json_user["account"])

class PixivTag:
    def __init__(self, name, translated_name):
        self.name = name
        self.translated_name = translated_name
    
    def __str__(self):
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
        tag_string = ", ".join(str(tag) for tag in self.tags)
        return f"pixiv #{self.iden}\nTitle: '{self.title}'\nCaption: '{self.caption}'\nArtist: {str(self.user)}\nTags: {tag_string}"
    
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


def get_config():
    with open("./settings.json", "r", encoding="utf-8") as config_json:
        return json.load(config_json)

g_config = None
g_seen = None
g_api = None

def save_config():
    with open("./settings.json", "w", encoding="utf-8") as config_json:
        config_json.write(json.dumps(g_config, indent=4))

USER_AGENT = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"

def get_new_access_token():
    global g_config
    
    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": g_config["refresh_token"],
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30
    )
    
    data = response.json()
    g_config["access_token"] = data["access_token"]
    g_config["refresh_token"] = data["refresh_token"]
    save_config()

def check_illustrations(check_interval):
    global g_config
    global g_api
    global g_seen
    
    while True:
        for artist_id in g_config["artist_ids"]:
            user_illusts_json = None
            while True:
                try:
                    user_illusts_json = g_api.user_illusts(artist_id)
                    if "error" in user_illusts_json:
                        get_new_access_token()
                        g_api.set_auth(g_config["access_token"])
                        user_illusts_json = g_api.user_illusts(artist_id)
                    break
                except Exception as e:
                    if isinstance(e, KeyboardInterrupt) or isinstance(e, SystemExit):
                        raise
            illusts = user_illusts_json["illusts"]
            for illust_json in illusts:
                illust = PixivIllustration.from_json(illust_json)
                if not g_seen.query_illust(illust.iden):
                    g_seen.add_illust(illust.iden)
                    print(f"Found new illustration:\n{str(illust)}")
            g_seen.flush()
        time.sleep(check_interval)

# TODO make everything not global

def main():
    global g_config
    global g_seen
    global g_api

    g_config = get_config()
    g_seen = SeenIllustrations()
    
    check_interval = g_config["check_interval"]
    
    g_api = AppPixivAPI()
    g_api.set_auth(g_config["access_token"])
    
    threading.Thread(target=check_illustrations, args=(check_interval,), daemon=True).start()
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()