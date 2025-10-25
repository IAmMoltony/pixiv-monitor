import json
import os
import threading
from pixivmodel import PixivIllustration

LOCK = threading.Lock()

def get_illust_log():
    with LOCK:
        if not os.path.exists("./illustlog.json"):
            return {"illusts": []}
        with open("./illustlog.json", encoding="utf-8") as illustlog_json:
            return json.load(illustlog_json)

def save_illust_log(illust_log):
    with LOCK:
        temp_path = "./illustlog.json.tmp"
        with open(temp_path, "w", encoding="utf-8") as illustlog_json:
            json.dump(illust_log, illustlog_json, ensure_ascii=False, indent=2)
        os.replace(temp_path, "./illustlog.json")

# TODO i think we can add some shit to make the json module recognize our class (i have done this before)
def serialize_illust(illust):
    return {
        "id": illust.iden,
        "create_date": illust.create_date,
        "title": illust.title,
        "caption": illust.caption,
        "user": {
            "name": illust.user.name,
            "account": illust.user.account,
        },
        "tags": illust.get_tag_string(False),
        "is_sensitive": illust.is_sensitive
    }

def log_illust(illust):
    log = get_illust_log()
    illusts = log["illusts"]

    illusts.append(serialize_illust(illust))
    illusts.sort(key=lambda x: x["create_date"], reverse=True) # Sort by date so the newest ones come first in the json file

    save_illust_log(log)
