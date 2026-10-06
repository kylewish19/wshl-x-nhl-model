from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from wshlx_nhl.bootstrap_models import build_skater_transitions, train_transition_rate_model
from wshlx_nhl.distributions import prob_at_least

STATS_BASE = "https://api.nhle.com/stats/rest/en"
WEB_BASE = "https://api-web.nhle.com/v1"
SEASONS = [20212022, 20222023, 20232024, 20242025, 20252026, 20262027]


def get_season_stats(season: int) -> pd.DataFrame:
    url = f"{STATS_BASE}/skater/summary"
    params = {
        "isAggregate": "false",
        "isGame": "false",
        "sort": '[{"property":"points","direction":"DESC"}]',
        "start": 0,
        "limit": 2000,
        "cayenneExp": f"gameTypeId=2 and seasonId={season}",
    }
    r = requests.get(url, params=params, timeout=60, headers={"User-Agent":"wshlx-nhl-model/skater-transition"})
    r.raise_for_status()
    data = r.json().get("data", [])
    df = pd.DataFrame(data)
    if df.empty:
        raise RuntimeError(f"No skater data returned for {season}")
    # NHL Stats REST fields are normally already named this way; aliases keep the
    # pipeline resilient if the public endpoint changes a label.
    aliases = {
        "powerPlayGoals": "ppGoals",
        "powerPlayPoints": "ppPoints",
        "playerId": "playerId",
        "gamesPlayed": "gamesPlayed",
        "timeOnIcePerGame": "timeOnIcePerGame",
        "shootingPct": "shootingPct",
        "positionCode": "positionCode",
    }
    for src, dst in aliases.items():
        if src in df.columns and dst not in df.columns:
            df[dst] = df[src]
    required = ["playerId","gamesPlayed","goals","assists","points","shots","ppGoals","ppPoints","timeOnIcePerGame","shootingPct","positionCode"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Season {season} missing fields {missing}; got {sorted(df.columns.tolist())}")
    return df[required + [c for c in ["skaterFullName","teamAbbrevs"] if c in df.columns]].copy()


def roster_map(team: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for url in [f"{WEB_BASE}/roster-current/{team}", f"{WEB_BASE}/roster/{team}/20262027"]:
        r = requests.get(url, timeout=30, headers={"User-Agent":"wshlx-nhl-model/skater-transition"})
        if not r.ok:
            continue
        payload = r.json()
        for group in ["forwards", "defensemen"]:
            for p in payload.get(group, []):
                first = p.get("firstName", {})
                last = p.get("lastName", {})
                if isinstance(first, dict): first = first.get("default") or first.get("en") or ""
                if isinstance(last, dict): last = last.get("default") or last.get("en") or ""
                name = f"{first} {last}".strip().casefold()
                pid = p.get("id") or p.get("playerId")
                if name and pid:
                    out[name] = int(pid)
        if out:
            break
    return out


def fallback_rate(current_row: pd.DataFrame, prior: pd.DataFrame, target: str, pos: str | None) -> float:
    rate_col = {"next_goals_pg":"goals", "next_assists_pg":"assists", "next_points_pg":"points"}[target]
    med = prior.copy()
    if pos and "positionCode" in med.columns:
        same = med[med["positionCode"].eq(pos)]
        if len(same) >= 20:
            med = same
    league_rate = float((med[rate_col] / med["gamesPlayed"].clip(lower=1)).median())
    if current_row.empty:
        return max(0.0, league_rate)
    gp = float(current_row.iloc[0]["gamesPlayed"] or 0)
    cnt = float(current_row.iloc[0][rate_col] or 0)
    # Early-season fallback: five pseudo-games at the positional median.
    return max(0.0, (cnt + 5.0 * league_rate) / max(gp + 5.0, 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--metrics", required=True)
    args = ap.parse_args()

    frames = {s: get_season_stats(s) for s in SEASONS}
    completed = [frames[s] for s in SEASONS[:-1]]
    transitions = build_skater_transitions(completed, min_games=10)
    models = {
        "goals": train_transition_rate_model(transitions, "next_goals_pg"),
        "assists": train_transition_rate_model(transitions, "next_assists_pg"),
        "points": train_transition_rate_model(transitions, "next_points_pg"),
    }

    board = pd.read_csv(args.board)
    rosters = {t: roster_map(t) for t in sorted(board["team"].dropna().unique())}
    prior = frames[20252026].copy(); prior["playerId"] = prior["playerId"].astype(int)
    current = frames[20262027].copy(); current["playerId"] = current["playerId"].astype(int)

    rows = []
    for _, r in board.iterrows():
        name = str(r["player_name"]); team = str(r["team"])
        pid = rosters.get(team, {}).get(name.casefold())
        pprev = prior[prior["playerId"].eq(pid)] if pid else prior.iloc[0:0]
        pcur = current[current["playerId"].eq(pid)] if pid else current.iloc[0:0]
        pos = None
        if not pprev.empty: pos = str(pprev.iloc[0]["positionCode"])
        elif not pcur.empty: pos = str(pcur.iloc[0]["positionCode"])

        pred_rates = {}
        bases = {}
        for key, target in [("goal","next_goals_pg"),("assist","next_assists_pg"),("point","next_points_pg")]:
            model = models[{"goal":"goals","assist":"assists","point":"points"}[key]]
            if not pprev.empty and float(pprev.iloc[0]["gamesPlayed"]) >= 10:
                mu = float(model.predict(pprev.iloc[[0]])[0]); basis = "transition_ml_anchor"
            else:
                mu = fallback_rate(pcur, prior, target, pos); basis = "limited_history_fallback_reconstruction"
            pred_rates[key] = mu; bases[key] = basis

        market = str(r["market"])
        if market == "anytime_goal": mu = pred_rates["goal"]; p = float(prob_at_least(1, mu, None)); basis = bases["goal"]
        elif market == "anytime_assist": mu = pred_rates["assist"]; p = float(prob_at_least(1, mu, None)); basis = bases["assist"]
        elif market == "point_1plus": mu = pred_rates["point"]; p = float(prob_at_least(1, mu, None)); basis = bases["point"]
        elif market == "point_2plus": mu = pred_rates["point"]; p = float(prob_at_least(2, mu, None)); basis = bases["point"]
        else: raise ValueError(f"Unsupported market {market}")
        rows.append({**r.to_dict(), "player_id": pid, "expected_count": mu, "model_probability": p, "model_basis": basis})

    out = pd.DataFrame(rows)
    Path(args.predictions).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.predictions, index=False)
    metrics = {
        "transition_rows": int(len(transitions)),
        "validation_mae": {k: float(v.validation_mae) for k,v in models.items()},
        "alpha": {k: float(v.alpha) for k,v in models.items()},
        "rows_scored": int(len(out)),
    }
    Path(args.metrics).write_text(json.dumps(metrics, indent=2))
    print(out.to_string(index=False))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
