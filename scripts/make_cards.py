from __future__ import annotations

import argparse
import glob
from pathlib import Path

import pandas as pd

from wshlx_nhl.selection import top_probability_card, playable_price_card
from wshlx_nhl.selection_shadow import playable_price_shadow_v0_2, playable_price_shadow_v0_3


def load_shadow_history(pattern: str, target_date: str | None) -> pd.DataFrame:
    """Load only clean official Playable grading files strictly before target_date."""
    frames: list[pd.DataFrame] = []
    for path in sorted(glob.glob(pattern)):
        if "LATE_LOCK" in Path(path).name.upper():
            continue
        try:
            frame = pd.read_csv(path)
        except (OSError, pd.errors.EmptyDataError):
            continue
        if frame.empty or "result" not in frame.columns:
            continue
        frame["source_file"] = Path(path).name
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    history = pd.concat(frames, ignore_index=True, sort=False)
    if target_date and "date" in history.columns:
        history["date"] = pd.to_datetime(history["date"], errors="coerce")
        history = history[history["date"].notna() & (history["date"] < pd.Timestamp(target_date))]
    return history


def infer_target_date(df: pd.DataFrame, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    if "date" not in df.columns:
        return None
    dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.strftime("%Y-%m-%d").unique()
    if len(dates) == 1:
        return str(dates[0])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--top10-out", required=True)
    ap.add_argument("--playable-out")
    ap.add_argument("--shadow-playable-out", help="Optional legacy v0.2 shadow output")
    ap.add_argument("--shadow-v03-out", help="Optional Playable Price shadow v0.3 output")
    ap.add_argument(
        "--shadow-history-glob",
        default="data/results/*_playable_graded.csv",
        help="Clean graded Playable history used only for v0.3 one-sided reliability haircuts",
    )
    ap.add_argument("--shadow-target-date", help="YYYY-MM-DD; defaults to the candidates date when unambiguous")
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

    if args.shadow_playable_out:
        shadow = playable_price_shadow_v0_2(df)
        Path(args.shadow_playable_out).parent.mkdir(parents=True, exist_ok=True)
        shadow.to_csv(args.shadow_playable_out, index=False)
        print(
            f"Selected {len(shadow)} Playable Price shadow-v0.2 picks "
            f"-> {args.shadow_playable_out}"
        )

    if args.shadow_v03_out:
        target_date = infer_target_date(df, args.shadow_target_date)
        if target_date is None:
            raise ValueError(
                "Playable Price shadow v0.3 requires --shadow-target-date or one unique candidates date"
            )
        history = load_shadow_history(args.shadow_history_glob, target_date)
        shadow_v03 = playable_price_shadow_v0_3(
            df,
            history=history,
            target_date=target_date,
        )
        Path(args.shadow_v03_out).parent.mkdir(parents=True, exist_ok=True)
        shadow_v03.to_csv(args.shadow_v03_out, index=False)
        print(
            f"Selected {len(shadow_v03)} Playable Price shadow-v0.3 picks "
            f"using {len(history)} strictly prior clean grading rows -> {args.shadow_v03_out}"
        )


if __name__ == "__main__":
    main()
