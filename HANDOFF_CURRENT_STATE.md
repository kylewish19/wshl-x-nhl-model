# NHL MODEL — CURRENT STATE

Version: v0.1.0
Season: 2026-27
Repository: kylewish19/wshl-x-nhl-model

## Repository status
- GitHub repository created and initialized on 2026-09-29.
- v0.1.0 source, configs, tests, CI, grading pipeline, selection pipeline, and lessons log are on `main`.
- Local scaffold tests passed 7/7 before the initial push.
- Opening-day bootstrap ML code, canonical team aliases, run metadata, locked Top 10, and priced playable card are committed.

## Locked project rules
- Use games supplied by the user for the daily slate.
- Produce a pre-odds Top 10 Probability Card.
- Odds must never influence or rewrite the locked Top 10 Probability Card.
- After FanDuel prices are supplied, create a separate Playable Price Card using model edge and expected value.
- Grade both cohorts independently the next day.
- Append completed 2026-27 games to the dataset and rolling features.
- Structural model changes require evidence and are logged; one bad slate alone does not justify overfitting.
- Never retroactively alter locked picks.

## 2026-09-29 locked outputs
- Top 10 Probability Card: `data/picks/2026-09-29_top10_probability.csv`
- Playable Price Card: `data/picks/2026-09-29_playable_price.csv`
- Model run metadata: `data/model_runs/2026-09-29_v0.1.0.json`
- A team-name mapping bug was found during the pre-lock dry run, corrected, logged, and the invalid dry run was discarded before any official picks were locked.

## Exact current task
Let the 2026-09-29 slate play. On the next grading request, collect final game/player/goalie results, grade the locked Top 10 and Playable Price cohorts separately, update cumulative W-L/hit rate/Brier/ROI, diagnose misses, append lessons, and change code only when evidence supports it.
