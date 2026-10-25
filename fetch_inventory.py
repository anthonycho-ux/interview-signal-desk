#!/usr/bin/env python3
"""Fetch Cem Karsan interview inventory via yt-dlp channel listings.

RSS feeds are dead (YouTube returns 400/404), so we use yt-dlp's full
channel metadata as the stable programmatic source. Full metadata (not
flat playlist) is required because upload dates only come with it. The
JSON file is the single source of truth; new entries are merged and
deduped by video id.

Usage: python3 fetch_inventory.py [--days 30]
Writes karsan-videos.json next to this script.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "karsan-videos.json")

CHANNELS = [
    # tastylive — many Karsan segments
    "https://www.youtube.com/@tastyliveshow/videos",
    # Kai Media — his own shop
    "https://www.youtube.com/channel/UChrx0LQWgRhTuVqUXEbM6Cg/videos",
]
KEYWORD = re.compile(r"karsan", re.I)

MAX_PER_CHANNEL = 120


def fetch_channel(url, dateafter, limit=MAX_PER_CHANNEL):
    cmd = [
        "yt-dlp", "--skip-download",
        "--playlist-items", "1-%d" % limit,
        "--dateafter", dateafter,
        "--print", "%(upload_date)s\t%(id)s\t%(title)s\t%(url)s",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        sys.stderr.write("yt-dlp failed for %s: %s\n" % (url, proc.stderr[-500:]))
        return []
    rows = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            rows.append({
                "date": parts[0],
                "id": parts[1],
                "title": parts[2],
                "url": parts[3],
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    dateafter = cutoff.strftime("%Y%m%d")
    print("cutoff:", dateafter, flush=True)

    existing = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            for item in json.load(fh):
                existing[item["id"]] = item

    seen = set(existing)
    for ch in CHANNELS:
        for row in fetch_channel(ch, dateafter):
            vid = row["id"]
            if vid in seen or not KEYWORD.search(row["title"]):
                continue
            seen.add(vid)
            existing[vid] = {
                "id": vid,
                "title": row["title"],
                "url": row["url"],
                "date": row["date"],
                "channel": ch,
                "added": datetime.now(timezone.utc).isoformat(),
            }

    items = sorted(existing.values(), key=lambda x: x.get("date", ""), reverse=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=2, ensure_ascii=False)

    print("inventory: %d videos (%d new), %d channels" %
          (len(items), len(seen) - len(existing) + len(seen) - (len(existing) if existing else 0), len(CHANNELS)))


if __name__ == "__main__":
    main()
