# NHL MODEL — CURRENT STATE

Version: **v0.1.0 official**  
Shadow experiments: **goalie saves v0.2** and **Playable selection shadow v0.2**  
Season: **2026-27**  
Repository: **kylewish19/wshl-x-nhl-model**  
Branch: `main`

## Core workflow / locked rules
- Use only games the user supplies for the daily slate.
- Refresh current rosters, injuries, projected lines/PP roles, rest/back-to-back context and current goalie context before the final run.
- Probability stage is **odds-blind**: sportsbook markets/thresholds define the candidate universe, but prices cannot influence model probabilities or Top 10 ranking.
- Produce exactly **10 highest model-probability eligible bets** across the full slate for the Top 10 Probability Card. No forced diversity.
- Lock Top 10 before applying FanDuel prices.
- Apply the Playable Price Gate to the full eligible candidate universe. The official playable card is uncapped.
- Default playable gates: minimum EV 5%; edge thresholds ML/spread/total 3%, anytime goal 5%, assist 4%, goalie saves 4%, 1+ point 4%, 2+ point 5%.
- Grade Top 10 and Playable Price separately; track W-L, hit rate, Brier/calibration, and flat-stake units/ROI for Playable.
- Structural predictive changes require repeated prospective evidence; implementation/data bugs may be fixed immediately and logged.
- Never rewrite historical locked picks.
- Same-player/team/game correlation is tracked diagnostically; pure Top 10 remains marginal-probability ranked unless a documented rule changes it.
- Any slate finalized after puck drop is tagged **LATE_LOCK** and excluded from the clean prospective cumulative record.
- Skipped dates stay skipped.

## Goalie-save eligibility policy — effective 2026-10-05
- **If the user sends a FanDuel goalie-save line, use that goalie and exact line immediately.**
- Separate starter confirmation is not required.
- A FanDuel-listed goalie-save prop supplied by the user is sufficient for candidate eligibility in Top 10, Playable Price and Ladder workflows, provided the model has a valid probability.
- If the goalie does not start and FanDuel voids the wager, grade it **VOID** rather than a loss.
- This is a workflow/eligibility rule change, not a predictive-model version change.

## Modeling state
- **v0.1.0 remains the official production model after Oct. 5 grading.**
- Training seasons: 2021-22 through 2025-26, with current 2026-27 context appended prospectively.
- Team/game markets use the team-goal Poisson hybrid plus opening-season strength context.
- Skater goal/assist/point thresholds use transition/count-rate models with probability transforms.
- Known limitations: early-season role changes, rookie/limited-history fallback, independent team-goal structure, correlation concentration, and raw implied-probability edge rather than fully no-vig-normalized price comparison.

## Goalie model status
- Historical goalie pipeline is populated reproducibly from NHL regular-season data: **6,599 games / 13,198 goalie-start rows** through the pre-Oct. 5 training window.
- Official goalie v0.1 reconstruction uses the documented season-transition model and remains the official goalie model.
- v0.2 remains **shadow-only**: workload (expected shots) -> save rate -> expected saves -> negative-binomial O/U probability.
- Historical v0.1 and v0.2 validation metrics have different target granularities, so do not compare the old 1.54 vs 5.42 MAE numbers directly.
- Promotion uses matched per-game prospective comparisons on FanDuel-listed props.
- Oct. 5 matched six-goalie comparison: v0.1 preferred sides 2-4, v0.2 preferred sides 3-3; expected-saves MAE v0.1 **8.0574**, v0.2 **6.9017**; Brier v0.1 **0.3467**, v0.2 **0.2405**. Sample is only six, so no promotion.
- Promotion review remains no earlier than 20 clean settled listed goalie props, excluding DNP/voids.

## Clean prospective grading through 2026-10-05
- Sep 29 Top 10: 7-3; Playable: 7-10, -0.9502u.
- Sep 30 Top 10: 6-4; Playable: 6-4, +1.2905u.
- Oct 1: skipped.
- Oct 2 Top 10: 7-3; Playable: 6-2, +4.4427u.
- Oct 4 Top 10: 7-3; Playable: 5-5, -0.8231u.
- **Oct 5 Top 10: 3-6 with 1 VOID**, expected settled wins 6.4025, Brier 0.3511.
- **Oct 5 Playable: 1-26**, -25.0909u, -92.93% ROI, Brier 0.2754.
- Clean cumulative Top 10: **30-19 on settled bets (61.22%)**, plus one void; expected settled wins **34.7569**, Brier **0.2375**.
- Clean cumulative Playable: **25-47 (34.72%)**, **-21.1310u**, **-29.35% ROI**, Brier **0.2403**.
- Oct 3 remains a separate LATE_LOCK cohort and is excluded from clean totals.

## Oct. 5 lessons
- Top 10 wins: Kucherov 1+ point, Robertson 1+ point, Rantanen 1+ point.
- Macklin Celebrini 1+ point was **VOID** after a late scratch.
- Playable Price had one winner: **Sergei Murashov Over 22.5 saves (-110), 31 saves**.
- Goalie supplement went **1-4**; clean goalie-save Playable cohort is now **4-9**.
- Clean limited-history/fallback bets are **0-7** through Oct. 5, but four are one Porter Martone player-game cluster, so effective independent sample size is lower.
- All clean anytime-goal Playable bets are **1-7, -5.80u**; sub-25% anytime-goal candidates are **0-5** with only 0.8593 expected wins.
- Do not globally restructure v0.1.0 from one catastrophic slate; use targeted shadow tests and prospective promotion rules.

## Playable selection shadow v0.2 — started 2026-10-06
- Official v0.1.0 Playable Price rules remain unchanged.
- Added `src/wshlx_nhl/selection_shadow.py` and tests.
- Shadow logic first applies the exact official price gate, then withholds:
  - rows tagged `limited_history_fallback`;
  - `anytime_goal` rows with model probability below 25%.
- The shadow does **not** change model probabilities and does **not** change the official Top 10 or official Playable card.
- `scripts/make_cards.py` supports optional `--shadow-playable-out` output.
- The post-hoc counterfactual through Oct. 5 removes 11 losses and no wins, but this is **not promotion evidence** because the rule was chosen after seeing those results.
- Require at least **20 new clean independent shadow decisions**, better prospective Brier/calibration and flat-stake ROI, and no material harm to stronger markets before considering promotion.
- Same-player clusters count as one diagnostic cluster when judging independence.
- Reproducible clean market audit is in `data/results/market_diagnostics_through_2026-10-05.csv`; generator is `scripts/audit_markets.py`.

## 10-Day NHL Ladder Challenge
- Challenge `2026-10-A` ended:
  - Day 1 Oct. 4: Vancouver +1.5 -108 — WIN.
  - Day 2 Oct. 5: OTT-BOS Over 5.5 -115 — LOSS.
- A new 10-day run may start on the next eligible slate.

## Key current files
- `data/results/2026-10-05_top10_graded.csv`
- `data/results/2026-10-05_playable_graded.csv`
- `data/results/2026-10-05_summary.csv`
- `data/results/season_summary.csv`
- `data/results/market_diagnostics_through_2026-10-05.csv`
- `data/results/goalie_shadow_v0.2.csv`
- `data/model_runs/2026-10-05_goalie_predictions.csv`
- `data/model_runs/2026-10-05_goalie_model_validation.json`
- `data/model_runs/2026-10-05_postgrade_review.json`
- `data/model_runs/2026-10-06_selection_shadow_review.json`
- `logs/2026-10-06_SELECTION_SHADOW_REVIEW.md`

## Next-task rule
For the next supplied slate: keep v0.1.0 official; refresh context; generate probabilities odds-blind; include FanDuel-listed goalie-save candidates immediately; lock Top 10; apply official prices to the full universe; also output the Playable selection shadow v0.2 for prospective comparison; continue matched goalie v0.1/v0.2 tracking; and start a new ladder challenge if the user wants to continue it.
