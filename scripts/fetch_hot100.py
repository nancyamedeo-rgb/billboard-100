#!/usr/bin/env python3
"""
Fetches the current Billboard Hot 100 chart and writes it to
data/hot100.json for the Dakboard widget to consume via
raw.githubusercontent.com.

No API key required — Billboard doesn't offer a free official API, so
this uses billboard.py (https://github.com/guoguo12/billboard-charts), a
well-established open-source library (MIT licensed) that reads Billboard's
public chart pages directly. That happens here, server-side, on a
schedule; the browser widget never touches billboard.com directly, which
avoids CORS entirely.

Dependencies: billboard.py (installed by the GitHub Action).
"""

import json
import os
import sys
from datetime import datetime, timezone

import billboard

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hot100.json")
MAX_ROWS = 20  # how many ranked songs to keep


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    previous = None
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r") as f:
                previous = json.load(f)
        except (json.JSONDecodeError, OSError):
            previous = None

    try:
        chart = billboard.ChartData("hot-100")
        if not chart.entries:
            raise RuntimeError("billboard.py returned 0 entries — chart fetch may have failed silently.")

        songs = []
        for entry in chart.entries[:MAX_ROWS]:
            songs.append({
                "rank": entry.rank,
                "title": entry.title,
                "artist": entry.artist,
                "image": entry.image or None,
                "peakPos": entry.peakPos,
                "lastPos": entry.lastPos,
                "weeksOnChart": entry.weeks,
                "isNew": bool(entry.isNew),
            })

        output = {
            "chartDate": chart.date,
            "chartTitle": chart.title,
            "songs": songs,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "billboard.com (via billboard.py)",
            "status": "ok",
        }
        print(f"Fetched {len(songs)} songs for chart dated {chart.date}")

    except Exception as e:
        print(f"WARNING: fetch failed: {e}", file=sys.stderr)
        if previous:
            output = previous
            output["status"] = "stale"
            output["lastError"] = str(e)
            output["lastErrorAt"] = datetime.now(timezone.utc).isoformat()
            print("Falling back to previous cached data.")
        else:
            output = {
                "chartDate": None,
                "chartTitle": None,
                "songs": [],
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "source": "billboard.com (via billboard.py)",
                "status": "error",
                "lastError": str(e),
            }
            with open(OUTPUT_PATH, "w") as f:
                json.dump(output, f, indent=2)
            sys.exit(1)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
