# 2026-10-06 — Targeted Playable Selection Shadow Review

## Why this exists
Oct. 5 was a catastrophic clean Playable Price slate (1-26), but one slate is not enough to globally rewrite v0.1.0. The correct response is to isolate repeated weak cohorts and test targeted controls prospectively.

## Clean evidence through Oct. 5
- Limited-history / rookie fallback: 0-7 settled clean bets across Anton Frondell (2), Tristan Luneau (1), and Porter Martone (4). Four Martone bets are one correlated player-game cluster, so effective independent sample size is smaller than seven.
- All clean anytime-goal Playable bets: 1-7, -5.80u, with 2.1225 expected wins.
- Sub-25% model-probability anytime goals: 0-5, with only 0.8593 expected wins. That is a warning signal, not enough evidence for a permanent official ban.
- Clean goalie-save Playable cohort is 4-9; goalie v0.2 remains a separate shadow challenger.

## New shadow challenger
`src/wshlx_nhl/selection_shadow.py` adds `playable_price_shadow_v0_2`.

The shadow card:
1. applies the exact official Playable Price gate first;
2. withholds `limited_history_fallback` rows;
3. withholds anytime-goal candidates with model probability below 25%;
4. does not alter any model probability;
5. does not alter the official Top 10 or official Playable Price card.

`scripts/make_cards.py` can now optionally write this shadow card with `--shadow-playable-out`.

## Promotion discipline
- The retrospective filtered result is diagnostic only because the rule was chosen after seeing the outcomes.
- No promotion from retrospective improvement.
- Require at least 20 new clean independent shadow decisions.
- Promotion requires better prospective Brier/calibration and flat-stake ROI with no material damage to stronger/high-probability markets.
- Same-player clustered bets count as one diagnostic cluster when judging independence.

## Official status
**v0.1.0 remains official.** This is a challenger/learning layer only.
