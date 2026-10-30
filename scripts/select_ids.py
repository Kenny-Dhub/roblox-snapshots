#!/usr/bin/env python3
"""Choose which universe IDs get the hourly snapshot.

Tracked = (IDs on today's charts + IDs tracked before) minus excluded IDs,
keeping only games whose latest snapshot says they were created within
--max-age-days. IDs with no snapshot yet are kept so they get a first one;
older games drop out after that single snapshot.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def read_ids(path: Path) -> list:
    if not path.exists():
        return []
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line.isdigit():
            ids.append(line)
    return ids


def latest_created(history_dir: Path, uid: str):
    path = history_dir / (uid + ".jsonl")
    if not path.exists():
        return None, False
    created = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            created = json.loads(line).get("created") or created
    if not created:
        return None, True
    text = created.replace("Z", "+00:00")
    if "." in text:  # Roblox sends 1-7 fractional digits; keep seconds only
        head, rest = text.split(".", 1)
        digits = len(rest) - len(rest.lstrip("0123456789"))
        text = head + rest[digits:]
    return datetime.fromisoformat(text).astimezone(timezone.utc), True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-ids", type=Path, required=True)
    parser.add_argument("--tracked", type=Path, required=True, help="read and rewritten in place")
    parser.add_argument("--exclude", type=Path, required=True)
    parser.add_argument("--history-dir", type=Path, required=True)
    parser.add_argument("--max-age-days", type=int, default=60)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    excluded = set(read_ids(args.exclude))
    candidates = []
    for uid in read_ids(args.chart_ids) + read_ids(args.tracked):
        if uid not in candidates and uid not in excluded:
            candidates.append(uid)

    kept, dropped = [], 0
    for uid in candidates:
        created, seen = latest_created(args.history_dir, uid)
        if not seen or created is None or (now - created).days <= args.max_age_days:
            kept.append(uid)
        else:
            dropped += 1

    args.tracked.parent.mkdir(parents=True, exist_ok=True)
    args.tracked.write_text("".join(uid + "\n" for uid in sorted(kept, key=int)), encoding="utf-8")
    print(json.dumps({"tracked": len(kept), "dropped_old": dropped, "excluded": len(excluded)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
