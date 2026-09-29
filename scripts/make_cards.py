from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from wshlx_nhl.selection import top_probability_card, playable_price_card


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--top10-out", required=True)
    ap.add_argument("--playable-out")
    ap.add_argument("--top-n", type=int, default=10)
    args = ap.parse_args()

    df = pd.read_csv(args.candidates)
    top = top_probability_card(df, n=args.top_n)
    Path(args.top10_out).parent.mkdir(parents=True, exist_ok=True)
    top.to_csv(args.top10_out, index=False)
    print(f"Locked {len(top)} Top Probability picks -> {args.top10_out}")

    if args.playable_out:
        playable = playable_price_card(df)
        Path(args.playable_out).parent.mkdir(parents=True, exist_ok=True)
        playable.to_csv(args.playable_out, index=False)
        print(f"Selected {len(playable)} Playable Price picks -> {args.playable_out}")


if __name__ == "__main__":
    main()
