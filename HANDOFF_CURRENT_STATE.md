# NHL MODEL — CURRENT STATE

Version: v0.1.0
Season: 2026-27

## Locked project rules
- Use games supplied by the user for the daily slate.
- Produce a pre-odds Top 10 Probability Card.
- Later apply FanDuel prices to create a separate Playable Price Card.
- Grade both cohorts independently the next day.
- Append every game immediately to the dataset/rolling features.
- Structural model changes require evidence and are logged; bad single slates alone do not justify overfitting.
- Never retroactively alter locked picks.

## Markets
ML, spread/puck line, total goals O/U, anytime goal scorer, anytime assist, goalie saves, player 1+ point, player 2+ points.

## Exact next task
Create the blank GitHub repository `wshl-x-nhl-model`, push this v0.1.0 scaffold, then build the first 2026-27 slate from the games/screenshots supplied by the user.
