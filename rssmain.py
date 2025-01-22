#!/usr/bin/python3

import feedgen.feed
import illustlog
import logging
import time
import datetime
from pixivmodel import PixivIllustration

def make_rss_feed(illust_log):
    gen = feedgen.feed.FeedGenerator()
    gen.id("pixiv-monitor")
    gen.title("pixiv-monitor RSS feed")
    gen.description("pixiv monitoring and whatnot")
    gen.link(href="http://192.168.1.46/files/dev/pixiv-monitor/pixiv.atom")

    for illust in illust_log["illusts"]:
        illust_id = illust["id"]
        illust_create_date = illust["create_date"]
        illust_title = illust["title"]
        illust_caption = illust["caption"]
        illust_artist_name = illust["user"]["name"]
        illust_artist_account = illust["user"]["account"]
        illust_tags = illust["tags"]
        illust_sample_image = illust["sample_image"]

        entry = gen.add_entry()
        entry.id(f"pixiv-{illust_id}")
        entry.title(f"{illust_title} by {illust_artist_name} (@{illust_artist_account})")
        entry.link(href=f"https://www.pixiv.net/en/artworks/{illust_id}")
        entry.description(illust_caption if illust_caption else "no description specified")
        entry.pubDate(datetime.datetime.fromisoformat(illust_create_date).strftime("%a, %d %b %Y %H:%M:%S +0000")) # placeholder tz

    gen.rss_file("pixiv.atom")

def main():
    logging.basicConfig(filename="rss.log", level=logging.INFO)
    logger = logging.getLogger()

    formatter = logging.Formatter("[%(asctime)s]:%(levelname)s %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("pixiv-monitor RSS feed started")

    make_rss_feed(illustlog.get_illust_log())

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
