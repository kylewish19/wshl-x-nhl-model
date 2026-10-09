# NHL MODEL — CURRENT STATE

Version: **v0.1.0 official**  
Shadow experiments: **goalie saves v0.2** and **Playable Price shadow v0.3**  
Season: **2026-27**  
Repository: **kylewish19/wshl-x-nhl-model**  
Branch: `main`

## Core workflow / locked rules
- Use only games the user supplies for the daily slate.
- Refresh current rosters, injuries, projected lines/PP roles, rest/back-to-back context and current goalie context before the final run.
- Probability stage is **odds-blind**: sportsbook markets/thresholds define the candidate universe, but prices cannot influence model probabilities or Top 10 ranking.
- Produce exactly **10 highest model-probability eligible bets** across the full slate for the Top 10 Probability Card. No forced diversity.
- Lock Top 10 before applying FanDuel prices.
- Apply the Official Playable Price Gate to the full eligible candidate universe. Official card remains uncapped.
- Official playable gates: minimum EV 5%; edge thresholds ML/spread/total 3%, anytime goal 5%, assist 4%, goalie saves 4%, 1+ point 4%, 2+ point 5%.
- Grade Top 10 and Official Playable separately; track W-L, hit rate, Brier/calibration, and flat-stake units/ROI for Playable.
- Structural predictive changes require repeated prospective evidence; implementation/data bugs may be fixed immediately and logged.
- Never rewrite historical locked picks.
- Any slate finalized after the first scheduled puck drop is tagged **LATE_LOCK** and excluded from clean prospective cumulative records and shadow-promotion samples.
- Skipped dates stay skipped.

## Goalie-save eligibility policy — effective 2026-10-05
- If the user sends a FanDuel goalie-save line, use that goalie and exact line immediately.
- Separate starter confirmation is not required.
- If the listed goalie does not start and FanDuel voids the wager, grade **VOID** rather than loss.

## Official modeling state
- **v0.1.0 remains the production model.**
- Training seasons: 2021-22 through 2025-26, with current 2026-27 context appended prospectively.
- Team/game markets: team-goal Poisson hybrid plus opening-season strength/current context.
- Skater goal/assist/point thresholds: transition/count-rate models with probability transforms.
- Official goalie v0.1: documented season-transition reconstruction.
- No official predictive version change has been justified through Oct. 8 grading.

## Clean prospective record through 2026-10-06
- Sep 29 Top 10: 7-3; Playable: 7-10, -0.9502u.
- Sep 30 Top 10: 6-4; Playable: 6-4, +1.2905u.
- Oct 1 skipped.
- Oct 2 Top 10: 7-3; Playable: 6-2, +4.4427u.
- Oct 3 LATE_LOCK; excluded from clean cumulative.
- Oct 4 Top 10: 7-3; Playable: 5-5, -0.8231u.
- Oct 5 Top 10: 3-6 + 1 VOID; Playable: 1-26, -25.0909u.
- Oct 6 Top 10: 7-3; Playable: 6-14, -9.4475u.

Clean cumulative remains:
- **Top 10: 37-22 settled (62.71%)**, expected wins 41.9596, Brier 0.2321.
- **Official Playable: 31-61 (33.70%)**, **-30.5785u**, **-33.24% ROI**, Brier 0.2364.

## Playable Price shadow v0.3 — active shadow, started 2026-10-08
Official Playable remains the control. v0.3 does not alter v0.1 probabilities or Top 10.

v0.3 rules:
1. One-sided market-level reliability haircut using only clean settled Official Playable observations strictly before the target slate; it may reduce raw probability but never increase it.
2. Exclude same-day results and LATE_LOCK evidence from the reliability haircut.
3. Quarantine `limited_history_fallback` and `rookie_projection_fallback` rows.
4. Temporarily quarantine **all anytime-goal wagers** while the market is recalibrated.
5. Absolute adjusted-probability floors: spread 55%, total 55%, assist 50%, goalie saves 58%, 1+ point 55%, 2+ points 45%; moneyline has no hard probability floor.
6. Apply the same official market-specific edge thresholds and 5% minimum EV to the adjusted probability.
7. One executable shadow wager per substantially correlated player/team/goalie cluster; prefer higher calibrated hit probability, then EV.

Promotion review:
- At least **20 new clean independent decisions**, preferably 20-30+.
- Must beat the Official Playable control prospectively on calibration/Brier and flat-stake ROI without materially harming stronger markets.
- LATE_LOCK decisions do not count.

## Goalie v0.2 shadow status
- v0.2 architecture: expected shots faced -> save rate -> expected saves -> negative-binomial O/U probability.
- It remains **SHADOW_ONLY**.
- Promotion requires matched prospective FanDuel-listed comparisons, no earlier than 20 clean settled props, and convincing improvement in expected-save MAE plus Brier/calibration without directional bias.
- Oct. 5 matched six-goalie diagnostic favored v0.2 on MAE/Brier.
- Oct. 6 clean 17-goalie comparison also favored v0.2: directional 10-7 vs v0.1 7-10; Brier about 0.2584 vs 0.2896; expected-saves MAE about 4.64 vs 5.03.
- Oct. 8 LATE_LOCK diagnostic went the other way slightly: v0.1 12-7 vs v0.2 11-8; Brier 0.2546 vs 0.2570; MAE 6.5225 vs 6.7184.
- Evidence is mixed, so **no promotion yet**.

## 2026-10-08 grading — LATE_LOCK diagnostic only
The full Oct. 8 model workflow began at 7:00:11 PM ET, seconds after the first scheduled puck drop. No live scores, outcomes, in-game odds or Oct. 8 game data were used, but standing rules require exclusion from clean records.

Top 10:
- **8-2 (80.0%)**
- Expected wins 7.6314
- Brier 0.1551
- Wins: MacKinnon 1+ point, Kucherov 1+ point, Pastrnak 1+ point, Eichel 1+ point, Cooley U28.5 saves, Hildeby O23.5 saves, Kaprizov 1+ point, Robertson 1+ point.
- Losses: Bobrovsky U26.5 saves, Buffalo +1.5.

Official Playable:
- **14-15 (48.28%)**
- **-2.0136u**, **-6.94% ROI**
- Expected wins 15.7256
- Brier 0.2166
- ATG went 0-4; goalie saves 6-5; assists 2-0; totals 3-3.

Playable v0.3 shadow:
- **4-4**, **-0.1721u**, **-2.15% ROI**
- Calibrated expected wins 4.5063
- Brier 0.2635
- It avoided all four Official Playable ATG losses and materially reduced the loss, but selected-subset Brier was worse and it withheld several winning props.
- **Does not count toward promotion sample because Oct. 8 was LATE_LOCK.**

## Ladder Challenge
- 2026-10-A: Day 1 VAN +1.5 WIN; Day 2 OTT-BOS O5.5 LOSS — challenge ended.
- 2026-10-B: Day 1 Dobes U26.5 saves LOSS — challenge ended.
- **2026-10-C Day 1 (Oct. 8): Devin Cooley U28.5 saves -120 — WIN, 23 saves.**
- This ladder ticket was locked at 7:10:59 PM ET for the 9:00 PM COL-CGY game, so it is a valid pregame ladder decision despite the full-slate LATE_LOCK label.
- Challenge 2026-10-C advances to Day 2 on the next eligible slate.

## Current lessons / actions
- Keep v0.1.0 official and leave Top 10 logic unchanged.
- Keep Official Playable as the control.
- Keep Playable v0.3 shadow-only and maintain the ATG quarantine.
- Keep goalie v0.2 shadow-only; continue matched clean comparisons rather than promoting on mixed evidence.
- Full-slate lock must be completed before the first scheduled puck drop to count toward clean records or shadow promotion.
- Do not retroactively apply v0.3 to historical official records as if it had been live.

## Key current files
- `data/results/season_summary.csv`
- `data/results/ladder_summary.csv`
- `data/results/2026-10-08_top10_graded_LATE_LOCK.csv`
- `data/results/2026-10-08_playable_graded_LATE_LOCK.csv`
- `data/results/2026-10-08_playable_shadow_v0.3_graded_LATE_LOCK.csv`
- `data/results/2026-10-08_goalie_shadow_graded_LATE_LOCK.csv`
- `data/results/2026-10-08_summary_LATE_LOCK.csv`
- `data/model_runs/2026-10-09_postgrade_review.json`
- `logs/2026-10-09_OCT08_GRADING.md`
- `config/playable_price_shadow_v0.3.yaml`
- `src/wshlx_nhl/selection_shadow.py`

## Next-task rule
For the next user-supplied slate: refresh current context; score v0.1 probabilities odds-blind; include FanDuel-listed goalie-save props immediately; lock the full Top 10 **before first puck**; apply Official Playable prices afterward; also generate Playable v0.3 shadow for prospective comparison; continue matched goalie v0.1/v0.2 tracking; and continue Challenge 2026-10-C with Day 2 if the user wants the ladder.
