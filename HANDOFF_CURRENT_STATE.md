# NHL MODEL — CURRENT STATE

Version: v0.1.0
Season: 2026-27
Repository: kylewish19/wshl-x-nhl-model

## Repository status
- GitHub repository created and initialized on 2026-09-29.
- v0.1.0 source, configs, tests, CI, grading pipeline, selection pipeline, lessons log, opening-day bootstrap ML, and team aliases are on `main`.
- First slate (2026-09-29) has been fully graded and saved.

## Locked project rules
- Use games supplied by the user for the daily slate.
- Produce a pre-odds Top 10 Probability Card.
- Odds must never influence or rewrite the locked Top 10 Probability Card.
- After FanDuel prices are supplied, create a separate Playable Price Card using model edge and expected value.
- Grade both cohorts independently the next day.
- Append completed 2026-27 games to the dataset and rolling features.
- Structural model changes require evidence and are logged; one bad slate alone does not justify overfitting.
- Never retroactively alter locked picks.

## 2026-09-29 results
- Top 10 Probability Card: 7-3 (70.0%), Brier 0.2080.
- Playable Price Card: 7-10 (41.2%), -0.9502u, -5.59% ROI, Brier 0.2586.
- Results files: `data/results/2026-09-29_top10_graded.csv` and `data/results/2026-09-29_playable_graded.csv`.
- Cumulative tracker: `data/results/season_summary.csv`.
- Lessons logged in `logs/LESSONS.md`.
- No structural model change was made after one slate. Goalie-save calibration and rookie-fallback props are flagged for continued monitoring.

## Exact current task
Prepare the next user-supplied NHL slate using v0.1.0 plus the logged opening-night lessons. Continue tracking Top 10 and Playable Price cards separately. Revisit code changes only when a repeatable error pattern is supported by a larger prospective sample.
