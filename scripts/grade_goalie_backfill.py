from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


VERSIONS = ["v0_1", "v0_2", "v0_3"]


def grade_pick(side: str, line: float, actual: float) -> str:
    if side == "Over":
        if actual > line:
            return "WIN"
        if actual == line:
            return "PUSH"
        return "LOSS"
    if side == "Under":
        if actual < line:
            return "WIN"
        if actual == line:
            return "PUSH"
        return "LOSS"
    return "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--pred-dir", required=True)
    ap.add_argument("--dates", nargs="+", required=True)
    ap.add_argument("--late-lock-dates", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args()

    starts = pd.read_parquet(args.features).copy()
    starts["date"] = pd.to_datetime(starts["date"]).dt.strftime("%Y-%m-%d")
    starts["goalie_id"] = starts["goalie_id"].astype(str)
    actual = starts[["date", "goalie_id", "goalie_name", "team", "saves"]].rename(
        columns={"saves": "actual_saves"}
    )

    rows = []
    for date in args.dates:
        base = pd.read_csv(Path(args.pred_dir) / f"{date}_v01_v02.csv")
        v03 = pd.read_csv(Path(args.pred_dir) / f"{date}_v03.csv")
        base["goalie_id"] = base["goalie_id"].astype(str)
        v03["goalie_id"] = v03["goalie_id"].astype(str)
        merged = base.merge(
            v03[[
                "date","game","goalie_id","v0_3_expected_saves","v0_3_pick",
                "v0_3_pick_probability","v0_3_over_probability","v0_3_under_probability"
            ]],
            on=["date","game","goalie_id"],
            how="inner",
        ).merge(actual, on=["date","goalie_id"], how="left", suffixes=("","_actual"))

        for _, r in merged.iterrows():
            if pd.isna(r["actual_saves"]):
                continue
            for ver in VERSIONS:
                side = str(r[f"{ver}_pick"])
                prob = float(r[f"{ver}_pick_probability"])
                exp = float(r[f"{ver}_expected_saves"])
                result = grade_pick(side, float(r["line"]), float(r["actual_saves"]))
                rows.append({
                    "date": date,
                    "game": r["game"],
                    "goalie_name": r["goalie_name"],
                    "team": r["team"],
                    "line": float(r["line"]),
                    "actual_saves": float(r["actual_saves"]),
                    "version": ver,
                    "pick": side,
                    "pick_probability": prob,
                    "expected_saves": exp,
                    "absolute_error": abs(exp - float(r["actual_saves"])),
                    "result": result,
                    "late_lock": date in set(args.late_lock_dates),
                })

    graded = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    graded.to_csv(args.out, index=False)

    summaries = []
    for scope, frame in [
        ("ALL", graded),
        ("CLEAN_ONLY", graded[~graded["late_lock"]]),
        ("LATE_LOCK_ONLY", graded[graded["late_lock"]]),
    ]:
        for ver in VERSIONS:
            g = frame[frame["version"] == ver]
            settled = g[g["result"].isin(["WIN","LOSS"])]
            if g.empty:
                continue
            wins = int((settled["result"] == "WIN").sum())
            losses = int((settled["result"] == "LOSS").sum())
            y = (settled["result"] == "WIN").astype(float)
            brier = float(np.mean(np.square(settled["pick_probability"].to_numpy() - y.to_numpy()))) if len(settled) else np.nan
            summaries.append({
                "scope": scope,
                "version": ver,
                "rows": int(len(g)),
                "wins": wins,
                "losses": losses,
                "hit_rate": wins / max(wins + losses, 1),
                "saves_mae": float(g["absolute_error"].mean()),
                "pick_brier": brier,
                "over_picks": int((g["pick"] == "Over").sum()),
                "under_picks": int((g["pick"] == "Under").sum()),
            })
    summary = pd.DataFrame(summaries)
    summary.to_csv(args.summary, index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
