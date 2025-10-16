from pixivpy3 import *
import logging
import threading
from seen import SeenIllustrations
from tokenswitcher import TokenSwitcher
import queue
import time
from pixivmodel import PixivIllustration
import illustlog
import utility
import notify
import random
import sys

def get_json_illusts(api, artist_id, token_switcher):
    user_illusts_json = None
    while True:
        try:
            user_illusts_json = utility.api_wrapper(api, token_switcher, api.user_illusts, artist_id)
        except Exception as e:
            if not isinstance(e, KeyboardInterrupt) and not isinstance(e, SystemExit):
                logging.getLogger().error("Unhandled exception while trying to fetch illustrations: %s. Retrying in 5 seconds.", e)
                time.sleep(5)
                continue
    return user_illusts_json

class Monitor:
    def __init__(self, check_interval, artist_ids, config, api, seen, token_switcher, hooks):
        self.check_interval = check_interval
        self.artist_ids = artist_ids
        self.config = config
        self.api = api
        self.seen = seen
        self.token_switcher = token_switcher
        self.hooks = hooks

    def run(self):
        logging.getLogger().debug("Starting monitor: check interval=")
        threading.Thread(target=self.loop).start()

    def loop(self):
        artist_queue = queue.Queue()

        num_threads = self.config.get("num_threads", 3)
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self.illust_worker, args=(artist_queue,), daemon=True)
            thread.start()
            threads.append(thread)

        stop_event = threading.Event()
        
        def progress_worker(artist_queue, max):
            while not stop_event.is_set():
                print(f"\033]0;pixiv-monitor: {artist_queue.qsize()}/{max} left\007", end="")
                sys.stdout.flush()
                time.sleep(2)

        while True:
            shuffled_ids = random.sample(self.artist_ids, len(self.artist_ids))

            for artist_id in shuffled_ids:
                artist_queue.put(artist_id)

            thread = threading.Thread(target=progress_worker, args=(artist_queue, artist_queue.qsize()))
            thread.start()
            artist_queue.join()
            stop_event.set()
            thread.join()
            stop_event.clear()
            time.sleep(self.check_interval)

    def illust_worker(self, artist_queue):
        while True:
            try:
                artist_id = artist_queue.get()
                if artist_id is None:
                    break

                user_illusts_json = get_json_illusts(self.api, artist_id, self.token_switcher)
                if not user_illusts_json:
                    continue

                illusts = user_illusts_json["illusts"]
                num_new_illusts = 0
                first_illust = None
                for illust_json in illusts:
                    illust = PixivIllustration.from_json(illust_json)
                    if not self.seen.query_illust(illust.iden):
                        num_new_illusts += 1
                        if num_new_illusts == 1:
                            first_illust = illust
                        self.seen.add_illust(illust.iden)

                        print(f"[{utility.hrdatetime()}] \033[0;32mFound new illustration:\033[0m\n{str(illust)}\n")

                        page_count_string = "" if illust.page_count == 0 else f" ({illust.page_count} pages)"
                        log_message = f"New illustration: pixiv #{illust.iden}{page_count_string} '{illust.title}' by {illust.user.name} (@{illust.user.account}). Tags: {illust.get_tag_string(False)}"
                        logging.getLogger().info(log_message)

                        # Run hooks
                        for hook in self.hooks:
                            logging.getLogger().info("Running hook %s", hook)
                            hook.run(illust)

                        if not self.config["notifications_off"]:
                            notify.send_notification(f"'{illust.title}' by {illust.user.name} (@{illust.user.account})", illust.pixiv_link(), illust.get_r18_tag())
                        illustlog.log_illust(illust)

                if "ntfy_topic" in self.config:
                    if num_new_illusts > 1:
                        # as to not spam ntfy's servers, we send one (1) notification with a summary of the pictures
                        # link to the pixiv url instead of the individual pictures
                        notify.send_ntfy(self.config["ntfy_topic"], f"{num_new_illusts} new illustrations from {illust.user.name}", illust.user.pixiv_link())
                    elif num_new_illusts > 0:
                        # just like usual
                        notify.send_ntfy(self.config["ntfy_topic"], f"'{first_illust.title}' by {first_illust.user.name}", first_illust.pixiv_link(), first_illust.get_r18_tag())

                self.seen.flush()
            except Exception as e:
                if self.config.get("crash_on_exception", False):
                    raise
                logging.getLogger().error("Error in worker thread: %s", e)
            finally:
                artist_queue.task_done()
