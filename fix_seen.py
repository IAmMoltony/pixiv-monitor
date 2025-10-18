#!/usr/bin/env python3

import illustlog
from seen import SeenIllustrations

def main():
    print("Creating a new seen.json file based on illustration log")
    illusts = illustlog.get_illust_log()["illusts"]
    seen = SeenIllustrations(False)
    seen.seen_illusts = set()
    total_illusts = len(illusts)
    for i, illust in enumerate(illusts):
        illust_id = illust["id"]
        print(f"[{i+1}/{total_illusts}] {illust_id}")
        seen.add_illust(illust_id)
    seen.flush()
    print("Done")

if __name__ == "__main__":
    main()
