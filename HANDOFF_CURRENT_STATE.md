# NHL MODEL — CURRENT STATE

Version: **v0.1.0 official**  
Shadow experiment: **goalie saves v0.2**  
Season: **2026-27**  
Repository: **kylewish19/wshl-x-nhl-model**  
Branch: `main`

## Core workflow / locked rules
- Use only games the user supplies for the daily slate.
- Refresh current rosters, injuries, projected lines/PP roles, rest/back-to-back context and current goalie context before the final run.
- Probability stage is **odds-blind**: sportsbook markets/thresholds define the candidate universe, but prices cannot influence model probabilities or Top 10 ranking.
- Produce exactly **10 highest model-probability eligible bets** across the full slate for the Top 10 Probability Card. No forced diversity.
- Lock Top 10 before applying FanDuel prices.
- Apply the Playable Price Gate to the full eligible candidate universe. The playable card is uncapped.
- Default playable gates: minimum EV 5%; edge thresholds ML/spread/total 3%, anytime goal 5%, assist 4%, goalie saves 4%, 1+ point 4%, 2+ point 5%.
- Grade Top 10 and Playable Price separately; track W-L, hit rate, Brier/calibration, and flat-stake units/ROI for Playable.
- Structural predictive changes require repeated prospective evidence; implementation/data bugs may be fixed immediately and logged.
- Never rewrite historical locked picks.
- Same-player/team/game correlation is tracked diagnostically; pure Top 10 remains marginal-probability ranked unless a documented rule changes it.
- Any slate finalized after puck drop is tagged **LATE_LOCK** and excluded from the clean prospective cumulative record.
- Skipped dates stay skipped.

## Goalie-save eligibility policy — effective 2026-10-05
- **If the user sends a FanDuel goalie-save line, use that goalie and that exact line immediately.**
- A separate external starter confirmation is **not required** anymore.
- A FanDuel-listed goalie-save prop supplied by the user is sufficient for candidate eligibility in Top 10, Playable Price, and Ladder workflows, provided the model has a valid probability for that market.
- If the goalie ultimately does not start and FanDuel voids the wager, grade it according to sportsbook settlement (normally **VOID**), not as a model loss.
- This is a workflow/eligibility rule change, not a predictive-model version change; **v0.1.0 remains official**.
- `src/wshlx_nhl/selection.py` now treats a priced/listed goalie-save row as eligible even when `starter_confirmed` is false.

## Modeling state
- **v0.1.0 remains the official production model.**
- Training seasons: 2021-22 through 2025-26, with 2026-27 current context appended prospectively.
- Skater transition sample: 2,594 rows; latest chronological validation 640 rows.
- Ridge transition models: goal/game alpha 10, assist/game alpha 0.3, point/game alpha 0.3.
- Team/game markets use the team-goal Poisson hybrid plus opening-season strength context.
- Skater goal/assist/point thresholds use count-rate models with probability transforms.
- Current known limitations: early-season role changes, rookie/limited-history fallback, independent team-goal structure, lineup/goalie uncertainty, and raw implied-probability edge rather than fully no-vig-normalized price comparison.

## Goalie saves v0.2 shadow experiment
- Started 2026-10-05 and remains **shadow-only**.
- Architecture: expected shots faced model -> save-rate model -> expected saves -> negative-binomial O/U probabilities.
- Files: `src/wshlx_nhl/goalie_shadow.py`, `config/goalie_shadow_v0.2.yaml`, `scripts/train_goalie_shadow.py`, `tests/test_goalie_shadow.py`, `data/results/goalie_shadow_v0.2.csv`.
- Promotion review begins only after at least 20 clean prospective goalie props with usable model outputs; v0.2 must beat v0.1 on save-count MAE and probability calibration/Brier without introducing a new directional bias.
- The repo still needs the historical goalie feature dataset/artifact population before the shadow can produce a complete reproducible comparison slate-by-slate.

## Clean prospective grading through 2026-10-04
- Sep 29 Top 10: 7-3; Playable: 7-10, -0.9502u.
- Sep 30 Top 10: 6-4; Playable: 6-4, +1.2905u.
- Oct 1: skipped.
- Oct 2 Top 10: 7-3; Playable: 6-2, +4.4427u.
- Oct 4 Top 10: 7-3; Playable: 5-5, -0.8231u.
- Clean cumulative Top 10 through Oct 4: **27-13 (67.50%)**, expected wins 28.3544, Brier 0.2119.
- Clean cumulative Playable through Oct 4: **24-21 (53.33%)**, **+3.9599u**, **+8.80% ROI**, Brier 0.2193.
- Oct 3 remains a separate LATE_LOCK cohort and is excluded from clean totals.

## Current watchlists
- Goalie saves: workload/shot-volume calibration remains a priority; official clean goalie-save cohort was 3-5 through Oct 2 before the new listing policy.
- Rookie/limited-history fallback: volatile; keep tagged separately and do not treat as equally mature evidence.
- Low-probability/high-EV anytime goals: clean cohort was 0-4 through Oct 4; continue review before changing thresholds.
- Top-10 puck lines: clean cohort 10-2 through Oct 4; do not upweight from a small sample.
- Moneylines and correlation remain monitored separately.

## 10-Day NHL Ladder Challenge
- Separate from Top 10 and Playable Price.
- Challenge ID: **2026-10-A**.
- Day 1 (Oct 4): Vancouver +1.5 -108 — **WIN**.
- Day 2 (Oct 5): OTT-BOS Over 5.5 -115 — pending at lock.
- Ladder goal: one ticket per day with final FanDuel odds between -120 and +100, maximizing modeled survival probability.
- FanDuel-listed goalie-save props are now eligible for ladder consideration without separate starter confirmation if the model has a valid probability.

## Current slate — 2026-10-05
Games:
- PHI@TBL
- OTT@BOS
- WPG@PIT
- SJS@DAL

Official Top 10 file: `data/picks/2026-10-05_top10_probability.csv`  
Official Playable file: `data/picks/2026-10-05_playable_price.csv`  
Run metadata: `data/model_runs/2026-10-05_v0.1.0.json`

The Oct 5 Top 10 and Playable cards were locked before this goalie eligibility-policy change. Do not retroactively rewrite those locked cards unless the user explicitly requests a pre-puck rerun while all affected games are still unstarted. Going forward, the FanDuel listing rule applies automatically.

## Next-task rule
For future supplied slates: refresh context, generate probabilities odds-blind, include FanDuel-listed goalie-save candidates immediately when valid model probabilities are available, lock exactly 10 Top-Probability picks, apply prices to the full universe for Playable, select the ladder ticket, and grade all cohorts after games.
