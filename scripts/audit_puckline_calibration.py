"""Read-only calibration audit of clean settled +1.5 official picks.
Run: python scripts/audit_puckline_calibration.py
Does not fit models, change picks, or read late-lock cards.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data/results"

def load(cohort):
    rows = []
    seen = set()
    for path in sorted(RESULTS.glob(f"*_{cohort}_graded.csv")):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}_" + cohort + r"_graded\.csv", path.name):
            continue
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if row["market"] != "spread" or float(row["line"]) != 1.5:
                    continue
                if row["result"] not in {"WIN", "LOSS"}:
                    continue
                p = float(row["model_probability"])
                if not 0 <= p <= 1:
                    raise ValueError("Invalid probability")
                key = (row["date"], row["game"], row["selection"], row["line"])
                if key in seen:
                    raise ValueError(f"Duplicate pick {key}")
                seen.add(key)
                rows.append(dict(date=row["date"], p=p, y=int(row["result"] == "WIN"),
                                 profit=float(row["profit_units"]) if cohort == "playable" else None))
    return rows

def summarize(rows):
    n = len(rows)
    if not n:
        return {"n": 0}
    w = sum(r["y"] for r in rows)
    e = sum(r["p"] for r in rows)
    profit = sum(r["profit"] for r in rows) if all(r["profit"] is not None for r in rows) else None
    return dict(n=n, wins=w, losses=n-w, expected_wins=e, mean_probability=e/n,
                hit_rate=w/n, calibration_gap=e/n-w/n,
                brier=sum((r["p"]-r["y"])**2 for r in rows)/n,
                profit_units=profit, roi=profit/n if profit is not None else None)

def report(rows):
    groups = {"all": rows}
    for month in sorted({r["date"][:7] for r in rows}):
        groups[month] = [r for r in rows if r["date"].startswith(month)]
    for lo, hi in [(0,.6),(.6,.65),(.65,.7),(.7,.75),(.75,1.01)]:
        groups[f"band_{lo}_{hi}"] = [r for r in rows if lo <= r["p"] < hi]
    return {k:summarize(v) for k,v in groups.items()}

if __name__ == "__main__":
    print(json.dumps({c:report(load(c)) for c in ("top10","playable")}, indent=2))
