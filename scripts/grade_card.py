from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from wshlx_nhl.grading import grade_binary_picks, card_summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    picks = pd.read_csv(args.picks, dtype={"game_id": str})
    results = pd.read_csv(args.results, dtype={"game_id": str})
    graded = grade_binary_picks(picks, results)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    graded.to_csv(args.out, index=False)
    print(json.dumps(card_summary(graded), indent=2))


if __name__ == "__main__":
    main()
