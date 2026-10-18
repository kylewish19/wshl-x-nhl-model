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
- If the goalie starts and later leaves injured, the prop remains graded from his recorded saves unless the sportsbook itself voids it; Oct. 9 Shesterkin U26.5 therefore graded WIN after he started and made 13 saves.

## Official modeling state
- **v0.1.0 remains the production model.**
- Training seasons: 2021-22 through 2025-26, with current 2026-27 context appended prospectively.
- Team/game markets: team-goal Poisson hybrid plus opening-season strength/current context.
- Skater goal/assist/point thresholds: transition/count-rate models with probability transforms.
- Official goalie v0.1: documented season-transition reconstruction.
- No official predictive version change has been justified through Oct. 9 grading.

## Clean prospective record through 2026-10-09
- Sep 29 Top 10: 7-3; Playable: 7-10, -0.9502u.
- Sep 30 Top 10: 6-4; Playable: 6-4, +1.2905u.
- Oct 1 skipped.
- Oct 2 Top 10: 7-3; Playable: 6-2, +4.4427u.
- Oct 3 LATE_LOCK; excluded from clean cumulative.
- Oct 4 Top 10: 7-3; Playable: 5-5, -0.8231u.
- Oct 5 Top 10: 3-6 + 1 VOID; Playable: 1-26, -25.0909u.
- Oct 6 Top 10: 7-3; Playable: 6-14, -9.4475u.
- Oct 8 LATE_LOCK; excluded from clean cumulative.
- Oct 9 Top 10: **4-6**; Playable: **1-3, -2.2424u**.

Clean cumulative:
- **Top 10: 41-28 settled (59.42%)**, expected wins 47.7692, Brier 0.2418.
- **Official Playable: 32-64 (33.33%)**, **-32.8209u**, **-34.19% ROI**, Brier 0.2403.

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
- Oct. 8 was LATE_LOCK and does not count.
- Oct. 9 was the **first clean v0.3 decision**: Rangers ML +118, LOSS. Current clean v0.3 record: **0-1, -1.0u**. No promotion inference.

## Goalie v0.2 shadow status
- v0.2 architecture: expected shots faced -> save rate -> expected saves -> negative-binomial O/U probability.
- It remains **SHADOW_ONLY**.
- Promotion requires matched prospective FanDuel-listed comparisons, no earlier than 20 clean settled props, and convincing improvement in expected-save MAE plus Brier/calibration without directional bias.
- Oct. 5 matched six-goalie diagnostic favored v0.2 on MAE/Brier.
- Oct. 6 clean 17-goalie comparison also favored v0.2: directional 10-7 vs v0.1 7-10; Brier about 0.2584 vs 0.2896; expected-saves MAE about 4.64 vs 5.03.
- Oct. 8 LATE_LOCK diagnostic went the other way slightly: v0.1 12-7 vs v0.2 11-8; Brier 0.2546 vs 0.2570; MAE 6.5225 vs 6.7184.
- Oct. 9 clean two-goalie comparison: both versions went **1-1** directionally. v0.2 had better Brier (**0.1732 vs 0.2611**) and expected-saves MAE (**6.0907 vs 7.5031**), but two props are far too few for promotion.
- Evidence remains mixed, so **no promotion yet**.

## 2026-10-08 grading — LATE_LOCK diagnostic only
The full Oct. 8 model workflow began at 7:00:11 PM ET, seconds after the first scheduled puck drop. No live scores, outcomes, in-game odds or Oct. 8 game data were used, but standing rules require exclusion from clean records.

Top 10:
- **8-2 (80.0%)**
- Expected wins 7.6314
- Brier 0.1551

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

## 2026-10-09 grading — CLEAN
Final: Washington 3, Rangers 1.

Top 10:
- **4-6 (40.0%)**
- Expected wins 5.8096
- Brier 0.2987
- Wins: Shesterkin U26.5 saves, J.T. Miller 1+ point, Tom Wilson 1+ point, Pavel Dorofeyev 1+ point.
- Losses: NYR +1.5, Zibanejad 1+ point, Thompson O22.5 saves, Over 5.5, Adam Fox 1+ point, Ovechkin 1+ point.

Official Playable:
- **1-3 (25.0%)**
- **-2.2424u, -56.06% ROI**
- Brier 0.3293
- Only winner: Shesterkin U26.5 saves.

Playable v0.3:
- Rangers ML +118 — LOSS.
- Clean record now **0-1, -1.0u**.

## Ladder Challenge
- 2026-10-A: Day 1 VAN +1.5 WIN; Day 2 OTT-BOS O5.5 LOSS — challenge ended.
- 2026-10-B: Day 1 Dobes U26.5 saves LOSS — challenge ended.
- 2026-10-C Day 1 (Oct. 8): Devin Cooley U28.5 saves -120 — WIN.
- 2026-10-C Day 2 (Oct. 9): Logan Thompson O22.5 saves -104 — **LOSS (21 saves)**.
- **Challenge 2026-10-C ended on Day 2.**

## Current lessons / actions
- Keep v0.1.0 official and do not change Top 10 structure from one one-game 4-6 slate.
- Keep Official Playable as the control; performance remains poor enough that v0.3 testing is still justified.
- Keep Playable v0.3 shadow-only and maintain the ATG quarantine; it has only one clean decision so far.
- Keep goalie v0.2 shadow-only; continue matched clean comparisons rather than promoting on mixed/small-sample evidence.
- Full-slate lock must be completed before the first scheduled puck drop to count toward clean records or shadow promotion.
- Do not retroactively apply v0.3 to historical official records as if it had been live.

## Key current files
- `data/results/season_summary.csv`
- `data/results/ladder_summary.csv`
- `data/results/2026-10-09_top10_graded.csv`
- `data/results/2026-10-09_playable_graded.csv`
- `data/results/2026-10-09_playable_shadow_v0.3_graded.csv`
- `data/results/2026-10-09_goalie_shadow_graded.csv`
- `data/results/2026-10-09_summary.csv`
- `data/model_runs/2026-10-09_postgame_review.json`
- `data/model_runs/2026-10-09_postgrade_review.json` (this file contains Oct. 8 grading review created on Oct. 9)
- `config/playable_price_shadow_v0.3.yaml`
- `src/wshlx_nhl/selection_shadow.py`

## Next-task rule
For the next user-supplied slate: refresh current context; score v0.1 probabilities odds-blind; include FanDuel-listed goalie-save props immediately; lock the full Top 10 **before first puck**; apply Official Playable prices afterward; also generate Playable v0.3 shadow for prospective comparison; continue matched goalie v0.1/v0.2 tracking; and start a fresh ladder challenge if the user wants to continue the ladder.
