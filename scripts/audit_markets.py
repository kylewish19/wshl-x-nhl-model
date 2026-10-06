from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def summarize(files: list[str]) -> pd.DataFrame:
    frames = [pd.read_csv(path) for path in files]
    df = pd.concat(frames, ignore_index=True)
    df = df[df["result"].isin(["WIN", "LOSS"])].copy()
    df["hit"] = df["result"].eq("WIN").astype(float)
    df["brier"] = (df["model_probability"] - df["hit"]) ** 2

    rows = []
    for market, g in df.groupby("market", sort=True):
        n = int(len(g))
        profit = float(g["profit_units"].sum()) if "profit_units" in g else np.nan
        rows.append({
            "through_date": str(pd.to_datetime(g["date"]).max().date()),
            "market": market,
            "bets": n,
            "wins": int(g["hit"].sum()),
            "losses": int(n - g["hit"].sum()),
            "hit_rate": float(g["hit"].mean()),
            "expected_wins": float(g["model_probability"].sum()),
            "avg_model_probability": float(g["model_probability"].mean()),
            "brier": float(g["brier"].mean()),
            "profit_units": profit,
            "roi": float(profit / n) if n and np.isfinite(profit) else np.nan,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description="Audit settled clean Playable Price results by market.")
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    out = summarize(args.inputs)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    print(out.to_string(index=False))
    print(f"Wrote {len(out)} market rows -> {path}")


if __name__ == "__main__":
    main()
