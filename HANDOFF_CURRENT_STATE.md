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
- Produce a pre-odds Top 10 Probability Card consisting of exactly the 10 highest-probability eligible bets across the full slate.
- Odds must never influence or rewrite the locked Top 10 Probability Card.
- After FanDuel prices are supplied, create a separate **Official Playable Price Card** from the full eligible slate using model probability, market-specific edge, and expected-value gates.
- The Official Playable Price Card is not capped at 10; its size is determined only by which bets satisfy the documented price gates.
- Grade both official cohorts independently after every slate, then collect lessons and make code changes only when the prospective evidence justifies them.
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


## Through 2026-09-30
- Top 10 Probability cumulative: 13-7 (65.0%).
- Official Playable Price cumulative: 13-14 (48.15%), +0.3403u, +1.26% ROI.
- Slate 2: Top 10 6-4; Playable Price 6-4, +1.2905u.
- Current watchlists: goalie-save volume calibration, rookie/projection fallback props, low-probability/high-EV longshots.
- No structural model change yet; v0.1.0 remains active pending a larger prospective sample.


## Through 2026-10-02
- Oct. 1 remained intentionally skipped; no retroactive card was created.
- Oct. 2 Top 10 Probability: 7-3 (70.0%).
- Oct. 2 Official Playable Price: 6-2, +4.4427u (+55.53% ROI).
- Cumulative Top 10: 20-10 (66.67%).
- Cumulative Official Playable Price: 19-16, +4.7830u (+13.67% ROI).
- Top-10 puck-line cohort is 8-0 through three tracked slates; do not change weighting yet.
- Current watchlists: goalie-save workload (playable 3-5), rookie/fallback props, and sub-20% probability/high-EV longshots (0-3).
- No structural predictive-model change after Slate 3; v0.1.0 remains active.
