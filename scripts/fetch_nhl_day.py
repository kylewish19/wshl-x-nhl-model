from __future__ import annotations

import argparse
import json
from pathlib import Path
from wshlx_nhl.nhl_api import NHLApi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="YYYY-MM-DD")
    ap.add_argument("--out-dir", default="data/raw/nhl")
    args = ap.parse_args()
    api = NHLApi()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    schedule = api.schedule(args.date)
    scores = api.scores(args.date)
    (out / f"schedule_{args.date}.json").write_text(json.dumps(schedule, indent=2))
    (out / f"scores_{args.date}.json").write_text(json.dumps(scores, indent=2))
    print(f"Saved NHL schedule/scores for {args.date}")


if __name__ == "__main__":
    main()
