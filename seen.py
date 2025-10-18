import threading
import os
import json

class SeenIllustrations:
    def __init__(self):
        self.lock = threading.Lock()
        self.seen_illusts = set()
        if os.path.exists("./seen.json"):
            with open("./seen.json", "r", encoding="utf8") as seen_json:
                jseen = json.load(seen_json)
                self.seen_illusts = set(jseen["illusts"])

    def flush(self):
        with self.lock:
            temp_path = "./seen.json.tmp"
            with open(temp_path, "w", encoding="utf8") as seen_json:
                json.dump({"illusts": list(self.seen_illusts)}, seen_json)
            os.replace(temp_path, "./seen.json")

    def add_illust(self, iden):
        with self.lock:
            self.seen_illusts.add(iden)

    def query_illust(self, iden):
        return iden in self.seen_illusts
