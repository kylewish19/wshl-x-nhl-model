from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from wshlx_nhl.game_markets import simulate_game


def blended_team_rates(team_games: pd.DataFrame, target_date: str, prior_pseudo_games: float = 10.0) -> tuple[dict, dict]:
    tg = team_games.copy()
    tg['date'] = pd.to_datetime(tg['date'])
    target = pd.Timestamp(target_date)
    tg = tg[tg['date'] < target].copy()
    prior = tg[tg['season'].astype(str).eq('20252026')]
    current = tg[tg['season'].astype(str).eq('20262027')]

    league_gf = float(prior['goals_for'].sum() / max(len(prior), 1))
    rates = {}
    counts = {}
    teams = sorted(set(prior['team']).union(set(current['team'])))
    for team in teams:
        p = prior[prior['team'].eq(team)]
        c = current[current['team'].eq(team)]
        p_gf = float(p['goals_for'].mean()) if len(p) else league_gf
        p_ga = float(p['goals_against'].mean()) if len(p) else league_gf
        n = float(len(c))
        c_gf_total = float(c['goals_for'].sum())
        c_ga_total = float(c['goals_against'].sum())
        gf = (prior_pseudo_games * p_gf + c_gf_total) / (prior_pseudo_games + n)
        ga = (prior_pseudo_games * p_ga + c_ga_total) / (prior_pseudo_games + n)
        rates[team] = {'gf': gf, 'ga': ga, 'prior_gf': p_gf, 'prior_ga': p_ga}
        counts[team] = int(n)
    return {'league': league_gf, 'teams': rates}, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--team-games', required=True)
    ap.add_argument('--board', required=True)
    ap.add_argument('--target-date', required=True)
    ap.add_argument('--predictions', required=True)
    ap.add_argument('--metrics', required=True)
    args = ap.parse_args()

    tg = pd.read_parquet(args.team_games)
    strength, counts = blended_team_rates(tg, args.target_date)
    league = strength['league']
    board = pd.read_csv(args.board)
    rows = []
    means = {}
    for _, r in board.iterrows():
        away = str(r['away']); home = str(r['home']); game = str(r['game'])
        ar = strength['teams'][away]; hr = strength['teams'][home]
        away_mu = float(np.sqrt(ar['gf'] * hr['ga']) * 0.98)
        home_mu = float(np.sqrt(hr['gf'] * ar['ga']) * 1.02)
        away_mu += float(r.get('away_context_adjustment', 0.0) or 0.0)
        home_mu += float(r.get('home_context_adjustment', 0.0) or 0.0)
        away_mu = max(1.5, away_mu); home_mu = max(1.5, home_mu)

        home_spread = float(r['home_spread'])
        away_spread = float(r['away_spread'])
        # simulate_game expects home_mu first, then away_mu, and returns a dataclass.
        probs = simulate_game(
            home_mu,
            away_mu,
            runs=20_000,
            home_spread=home_spread,
            total_line=float(r['total_line']),
            rng_seed=42,
        )
        means[game] = {'away': away_mu, 'home': home_mu}
        rows += [
            {'game':game,'market':'moneyline','selection':away,'line':'','model_probability':probs.away_ml,'model_basis':'team_goal_hybrid_v0.1_reconstruction'},
            {'game':game,'market':'moneyline','selection':home,'line':'','model_probability':probs.home_ml,'model_basis':'team_goal_hybrid_v0.1_reconstruction'},
            {'game':game,'market':'spread','selection':away,'line':away_spread,'model_probability':probs.away_cover,'model_basis':'team_goal_hybrid_v0.1_reconstruction'},
            {'game':game,'market':'spread','selection':home,'line':home_spread,'model_probability':probs.home_cover,'model_basis':'team_goal_hybrid_v0.1_reconstruction'},
            {'game':game,'market':'total','selection':'Over','line':float(r['total_line']),'model_probability':probs.over,'model_basis':'team_goal_hybrid_v0.1_reconstruction'},
            {'game':game,'market':'total','selection':'Under','line':float(r['total_line']),'model_probability':probs.under,'model_basis':'team_goal_hybrid_v0.1_reconstruction'},
        ]
    out = pd.DataFrame(rows)
    Path(args.predictions).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.predictions, index=False)
    meta = {
        'target_date': args.target_date,
        'prior_pseudo_games': 10.0,
        'league_prior_goals_per_team_game': league,
        'current_games_before_target': counts,
        'team_goal_means': means,
        'rows_scored': len(out),
    }
    Path(args.metrics).write_text(json.dumps(meta, indent=2))
    print(out.to_string(index=False)); print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
