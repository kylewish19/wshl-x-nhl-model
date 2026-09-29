# NHL MODEL — CURRENT STATE

Version: v0.1.0
Season: 2026-27
Repository: kylewish19/wshl-x-nhl-model

## Repository status
- GitHub repository created and initialized on 2026-09-29.
- v0.1.0 source, configs, tests, CI, grading pipeline, selection pipeline, and lessons log are on `main`.
- Local scaffold tests passed 7/7 before the initial push.

## Locked project rules
- Use games supplied by the user for the daily slate.
- Produce a pre-odds Top 10 Probability Card.
- Odds must never influence or rewrite the locked Top 10 Probability Card.
- After FanDuel prices are supplied, create a separate Playable Price Card using model edge and expected value.
- Grade both cohorts independently the next day.
- Append completed 2026-27 games to the dataset and rolling features.
- Structural model changes require evidence and are logged; one bad slate alone does not justify overfitting.
- Never retroactively alter locked picks.

## Markets
ML, spread/puck line, total goals O/U, anytime goal scorer, anytime assist, goalie saves, player 1+ point, player 2+ points.

## Exact current task
Build the first 2026-27 daily slate from the games/screenshots supplied by the user. Gather current team/player/goalie context, run the pre-odds models, and lock the first Top 10 Probability Card before reviewing FanDuel prices.
