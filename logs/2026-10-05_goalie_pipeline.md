# 2026-10-05 Goalie Saves Pipeline Rebuild

## Eligibility policy
Effective 2026-10-05, a goalie-save prop supplied by the user from FanDuel is sufficient to make that goalie/line eligible for model evaluation. No separate external starter-confirmation wait is required. If FanDuel voids a wager because the listed goalie does not start, grade the pick VOID rather than LOSS.

## Reproducible data/model rebuild
The original persisted v0.1 goalie artifact/feature table was not present in the repository. To avoid improvised probabilities, a reproducible goalie pipeline was built from NHL regular-season boxscores.

- Historical starter rows: 13,198
- Source games: 6,599 completed regular-season games
- Historical seasons: 2021-22 through 2025-26, with pre-Oct-5 2026-27 context available for current features
- Feature builder: `scripts/build_goalie_features.py`
- Board runner: `scripts/run_goalie_board.py`
- GitHub Actions workflow: `.github/workflows/goalie-shadow.yml`
- Successful workflow run: 37387752810

### v0.1 reconstruction
- 265 season-to-season transition rows
- Ridge alpha: 0.3
- Chronological validation MAE: 1.53894 saves/start
- O/U distribution: Poisson
- This is an explicit reproducible reconstruction using the committed v0.1 transition methodology. It is not represented as a byte-for-byte recovery of the missing original artifact and does not rewrite historical locked picks.

### v0.2 shadow
Still SHADOW_ONLY and cannot affect official selections.
- Validation rows: 2,624
- Shots MAE: 5.42623
- Save% MAE: 0.05397
- Saves MAE: 5.42366
- NB alpha: 0.03757
- The first validation pass does not justify promotion over v0.1. Continue prospective comparison and revise the workload/skill architecture if needed.

## Oct. 5 FanDuel goalie board
Official v0.1 reconstructed probabilities were generated for all eight supplied lines.

Qualified before their games started and appended to the Playable Price Card:
- Linus Ullmark Over 21.5 -118 — p 62.80%, edge +8.67%, EV +16.01%
- Clay Stevenson Under 25.5 -118 — p 74.44%, edge +20.31%, EV +37.53%
- Sergei Murashov Over 22.5 -110 — p 56.52%, edge +4.14%, EV +7.90%
- Yaroslav Askarov Over 23.5 -130 — p 64.79%, edge +8.26%, EV +14.62%
- Jake Oettinger Over 22.5 -102 — p 56.62%, edge +6.13%, EV +12.13%

Not added:
- Jeremy Swayman Under 25.5 -132 — did not clear the 4% goalie edge and 5% EV gates.
- Dan Vladar Under 26.5 -128 and Andrei Vasilevskiy Over 21.5 -112 qualified numerically, but PHI@TBL had already started before the rebuilt pipeline finished. They remain non-official to preserve clean prospective tracking.

## Integrity notes
- The locked Oct. 5 Top 10 was not changed or reordered.
- The original 22 Playable Price selections were preserved; five goalie saves were appended as a clean pre-puck supplement for the 7:30/8:00 games.
- v0.2 remains shadow-only despite being trained/validated; no shadow output influences the official card.
- Stevenson (5 historical NHL starts) and Murashov (4) are low-history goalie cases and should be flagged in postgame diagnostics even though they qualified under the official reconstructed model.
