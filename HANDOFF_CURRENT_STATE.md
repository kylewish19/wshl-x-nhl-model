# NHL MODEL — CURRENT STATE

Version: **v0.2.0 official**  
Shadow experiments: **Playable Price shadow v0.3**, **goalie simulation v0.3 research**, and skater/ATG research tracks  
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
- **v0.2.0 is the production model effective 2026-11-11.** The only promoted predictive component is goalie saves; team/game and skater components remain the prior v0.1.0 implementations.
- Training seasons: 2021-22 through 2025-26, with current 2026-27 context appended prospectively.
- Team/game markets: team-goal Poisson hybrid plus opening-season strength/current context.
- Skater goal/assist/point thresholds: transition/count-rate models with probability transforms.
- Official goalie v0.2: two-stage expected-shots-faced + save-rate model with negative-binomial O/U probabilities. v0.1 remains stored as a diagnostic comparator.
- Goalie v0.2 promotion was justified on 2026-11-11 after clearing the pre-written clean prospective review rule.

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

## Goalie v0.2 historical shadow / current official status
- v0.2 architecture: expected shots faced -> save rate -> expected saves -> negative-binomial O/U probability.
- **Promoted to OFFICIAL effective 2026-11-11.** v0.1 remains the diagnostic control.
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


## 2026-11-08 RESUME REFRESH — COMPLETE
After the Oct. 9 slate, the project paused for roughly one month. Before resuming betting, the model was refreshed through the Nov. 8 current-season sample without rewriting official historical predictions.

Refresh scope:
- **276 completed 2026-27 regular-season games**
- **552 team-game rows**
- **32 teams**
- **74 goalies with at least one 2026-27 start**
- **717 current-roster skaters**
- **727 current-season skater stat rows**

Team/game and goalie-current-context pipelines now include the missed month of completed games. Same-day injuries, scratches, projected lines, PP units, rest and goalie context still must be refreshed before each slate.

### New skater current-season shadow
Audit found that established-skater official v0.1 remains primarily anchored to 2025-26 transition inputs. To measure the value of November form without corrupting the official comparison, a new shadow was added:

**SKATER_CURRENT_SEASON_BLEND_SHADOW_V0_2 — SHADOW_ONLY**

Formula: empirical-Bayes blend of official v0.1 expected rate with actual 2026-27 counts.
- goals: 12-game prior weight
- assists: 10-game prior weight
- points: 10-game prior weight

It has **no Official Top 10 or Official Playable influence yet** and must be tracked prospectively before promotion.

Key files:
- `scripts/build_resume_snapshot.py`
- `scripts/build_current_season_fast_snapshot.py`
- `config/skater_current_season_shadow_v0.2.yaml`
- `data/context/2026-11-08_resume_context.md`
- `logs/2026-11-08_RESUME_REFRESH.md`
- `data/model_runs/2026-11-08_resume_refresh.json`

Both full and fast Nov. 8 refresh workflows completed successfully.

Historical clean record remains unchanged:
- Top 10: **41-28 (59.42%)**
- Official Playable: **32-64 (33.33%), -32.8209u, -34.19% ROI**
- Playable v0.3: **0-1, -1.0u**

Skipped dates remain skipped. Do not retroactively manufacture picks for the break.


## Market scope change — effective 2026-11-08
From this point forward, the active NHL betting workflow is limited to:
- **Spread / puck line**
- **Moneyline**
- **Game total goals O/U**
- **Anytime goal scorer**
- **Goalie total saves O/U**

Temporarily excluded from daily cards and tracking unless the user explicitly re-adds them:
- 1+ point
- 2+ points
- 1+ assist / anytime assist
- other skater props

Top 10 Probability Card and Official/Shadow Playable systems should rank/filter only the active market universe above.
Goalie v0.1/v0.2 shadow tracking continues.
Playable Price v0.3 continues, with the ATG quarantine policy still active unless separately changed.


## 2026-11-08 CORE MARKET SLATE — CLEAN PREGAME LOCK
Market universe was restricted by user to spread, moneyline, game total, anytime goal, and goalie saves only.

User-supplied games:
- VGK@BUF
- TBL@WPG
- NJD@TOR
- PHI@CGY
- PIT@ANA

Lock completed about **2:08 PM ET**, before the first supplied game (VGK@BUF, 3:30 PM ET). Same-day Nov. 8 games were excluded from pregame training/current-form tables.

Top 10 expected wins sum: **6.8222**.
Official Playable: **10 selections**.
Playable Price v0.3: **1 selection — Toronto ML +128**, calibrated probability 48.88%, calibrated expected ROI +11.45%.

Top 10:
1. Calgary +1.5 — 74.995%
2. Buffalo +1.5 — 72.84%
3. Toronto +1.5 — 72.25%
4. Pittsburgh +1.5 — 70.10%
5. Colten Ellis O22.5 saves — 70.01%
6. Devin Cooley O22.5 saves — 69.93%
7. Anthony Stolarz U27.5 saves — 68.44%
8. Winnipeg +1.5 — 64.83%
9. Dan Vladar U24.5 saves — 60.03%
10. Tampa Bay ML — 58.80%

Official Playable contains four fallback ATG longshots (William Stromgren, Zack MacEwen, Cole Knuble, Trevor Connelly), four goalie props, Toronto ML, and Toronto +1.5. v0.3 quarantines all ATGs and all four goalie props after reliability/floor rules, leaving only Toronto ML.

Goalie v0.1/v0.2 directional agreements:
- Ellis Over
- Skinner Over
- Hellebuyck Over
- Stolarz Under
- Cooley Over
- Vladar Under
- Silovs Under
Vasilevskiy is near 50/50 in both versions; both preferred Over by price-selection logic even though raw Under probability is slightly higher.

Current-season ATG shadow leaders:
- Kyle Connor 47.38%
- Cutter Gauthier 46.14%
- Auston Matthews 42.35%
- Tage Thompson 41.35%
- Jack Hughes 41.35%
- Jake Guentzel 40.75%
- William Nylander 40.24%

Identity audit corrected naming variants (Mitch Marner, Nick Paul, Jake McCabe, Nick Robertson, Viggo Bjorck/Björck). Audit had **no impact** on Top 10, Official Playable, or v0.3 card.

Key files:
- `data/model_runs/2026-11-08_top10.csv`
- `data/model_runs/2026-11-08_playable.csv`
- `data/model_runs/2026-11-08_playable_shadow_v0.3.csv`
- `data/model_runs/2026-11-08_goalie_predictions.csv`
- `data/model_runs/2026-11-08_atg_current_shadow_summary.json`
- `data/model_runs/2026-11-08_core_lock_summary.json`


## 2026-11-08 GRADING — COMPLETE
Final scores:
- VGK 4-1 BUF
- WPG 4-3 TBL
- NJD 4-0 TOR
- CGY 4-3 PHI (OT)
- ANA 5-2 PIT

### Top 10
**5-5 (50.0%)**, expected wins 6.8222, Brier 0.2916.
Wins: Calgary +1.5; Devin Cooley O22.5 saves; Anthony Stolarz U27.5 saves; Winnipeg +1.5; Dan Vladar U24.5 saves.
Losses: Buffalo +1.5; Toronto +1.5; Pittsburgh +1.5; Colten Ellis O22.5 saves; Tampa Bay ML.

### Official Playable
**3-7, -4.3974u, -43.97% ROI**, Brier 0.1871.
The four limited-history fallback ATGs (William Stromgren, Zack MacEwen, Cole Knuble, Trevor Connelly) all lost.
Winners: Stolarz U27.5; Cooley O22.5; Vladar U24.5.

### Playable v0.3
Toronto ML +128 — LOSS.
Clean prospective record now **0-2, -2.0u**.
v0.3 correctly withheld all four fallback ATG losses, but still has only two clean decisions and remains SHADOW_ONLY.

### Goalie v0.1 vs v0.2
Both directional cards: **4-4**.
- v0.1 Brier 0.2316, expected-saves MAE 3.3029
- v0.2 Brier 0.2420, expected-saves MAE 3.6486
v0.1 was slightly better on this slate; no promotion.

### Current-season ATG shadow
Top 10 shadow scorers: **2-8**, expected 4.1034, Brier 0.2048.
Winners: Cutter Gauthier (3 goals) and Brandon Hagel.
Official v0.1 ATG top 10 went **3-7**, expected 3.6145, Brier 0.2206.
The shadow had a better Brier but fewer hits on one slate; keep SHADOW_ONLY.

### Updated clean records
- Top 10: **46-33 (58.23%)**, Brier 0.2481
- Official Playable: **35-71 (33.02%)**, **-37.2183u, -35.11% ROI**, Brier 0.2353
- Playable v0.3: **0-2, -2.0u**

### Lessons
- Official Playable remains vulnerable to limited-history fallback ATG inflation; v0.3 quarantine continues to be justified.
- Do not promote v0.3 yet: only two clean prospective selections.
- Do not promote goalie v0.2: this slate favored v0.1 slightly.
- Do not promote the current-season ATG shadow from one slate.
- No official v0.1 structural change from this single restart slate.


## 2026-11-09 POST-GRADE DEVELOPMENT
Active-market clean Official Playable diagnostics through Nov. 8:
- Anytime goal: **1-15, -13.80u, -86.25% ROI**
- Goalie saves: **11-18, -8.2832u, -28.56% ROI**
- Moneyline: **6-8, +0.3349u, +2.39% ROI**
- Spread: **7-7, -2.7325u, -19.52% ROI**
- Total: **4-2, +1.2109u, +20.18% ROI**

Official v0.1 remains unchanged. Playable v0.3 keeps the full ATG quarantine.

New research track:
**ATG_CONSENSUS_SHADOW_V0_1 — SHADOW_ONLY**
- excludes limited-history / rookie fallback projections
- requires current GP >= 8 when available
- consensus probability = lower of official v0.1 ATG probability and current-season ATG shadow probability
- consensus probability >= 30%
- model disagreement <= 12 percentage points
- edge >= 5%
- expected ROI >= 5%
- promotion review no earlier than 25 clean prospective decisions

Files:
- `src/wshlx_nhl/atg_consensus_shadow.py`
- `scripts/build_atg_consensus_shadow.py`
- `config/atg_consensus_shadow_v0.1.yaml`
- `tests/test_atg_consensus_shadow.py`
- `data/results/market_diagnostics_through_2026-11-08.csv`
- `logs/2026-11-09_POSTGRADE_DEVELOPMENT.md`

The ATG consensus shadow does not alter Official Top 10, Official Playable, or Playable v0.3.


## 2026-11-09 CORE MARKET SLATE — CLEAN PREGAME LOCK
Games supplied:
- NYR@EDM — 8:00 PM ET
- PHI@VAN — 9:30 PM ET
- NYI@SJS — 10:00 PM ET

Lock completed about **7:11:54 PM ET**, before the 8:00 PM opener. Same-day Nov. 9 games were excluded from training/current-form inputs.

Luke Glendening was excluded from ATG eligibility after NHL projected lineup listed him scratched.

### Top 10
1. Joseph Woll O22.5 saves — 79.00%
2. Vancouver +1.5 — 71.59%
3. San Jose +1.5 — 70.16%
4. Rangers +1.5 — 66.10%
5. Yaroslav Askarov O23.5 saves — 64.79%
6. Devon Levi O22.5 saves — 63.72%
7. Leevi Merilainen O22.5 saves — 63.72%
8. NYI-SJS U6.5 — 59.12%
9. Ilya Sorokin O23.5 saves — 58.77%
10. Edmonton ML — 57.19%
Expected wins sum: **6.5416**.

### Official Playable
8 selections:
- Cole Knuble ATG +550 — 24.39%
- Joseph Woll O22.5 -112 — 79.00%
- Devon Levi O22.5 -102 — 63.72%
- Yaroslav Askarov O23.5 -118 — 64.79%
- Connor McDavid ATG +115 — 53.36%
- Leevi Merilainen O22.5 -132 — 63.72%
- Ilya Sorokin O23.5 -118 — 58.77%
- NYI-SJS U6.5 -120 — 59.12%

### Playable v0.3 shadow
2 selections:
- Joseph Woll O22.5 -112 — calibrated 60.06%
- NYI-SJS U6.5 -120 — calibrated 59.12%

### Goalie v0.1 vs v0.2
Same direction:
- Garand O24.5
- Levi O22.5
- Merilainen O22.5
- Askarov O23.5
- Sorokin O23.5

Strong disagreement:
- **Joseph Woll O22.5:** v0.1 Over 79.00%; v0.2 Under 60.44%.

### ATG research tracks
Official v0.1 top scorers:
McDavid 53.36%, Draisaitl 43.19%, Celebrini 42.41%, Horvat 33.84%, Zibanejad 33.32%.

Current-season shadow top:
Draisaitl 53.52%, McDavid 47.39%, Celebrini 37.50%, Horvat 34.69%, Bouchard 33.68%.

ATG consensus shadow produced **0 qualifying selections**. No player passed all consensus, disagreement, edge and EV gates.

Key files:
- `data/model_runs/2026-11-09_top10.csv`
- `data/model_runs/2026-11-09_playable.csv`
- `data/model_runs/2026-11-09_playable_shadow_v0.3.csv`
- `data/model_runs/2026-11-09_goalie_predictions.csv`
- `data/model_runs/2026-11-09_atg_official_top10.csv`
- `data/model_runs/2026-11-09_atg_current_shadow_top10.csv`
- `data/model_runs/2026-11-09_atg_consensus_shadow.csv`
- `data/model_runs/2026-11-09_core_lock_summary.json`

## Next-task rule
For the next user-supplied slate: refresh current context; score v0.1 probabilities odds-blind; include FanDuel-listed goalie-save props immediately; lock the full Top 10 **before first puck**; apply Official Playable prices afterward; also generate Playable v0.3 shadow for prospective comparison; continue matched goalie v0.1/v0.2 tracking; and start a fresh ladder challenge if the user wants to continue the ladder.

## 2026-11-10 grading — LATE_LOCK diagnostic
- Top 10: **8-2 (80.0%)**, expected wins 7.1492, Brier 0.1634.
- Official Playable: **8-5, +1.0451u (+8.04% ROI)**, Brier 0.1414.
- Playable Price v0.3: **2-0, +1.8130u**; diagnostic only.
- Official goalie v0.1 directional board: **8-5**.
- Goalie v0.2 directional board: **5-8**.
- This slate remains excluded from clean cumulative records because the computational lock finished after the first puck drop.

## 2026-11-11 GOALIE MODEL REVIEW / PROMOTION
The goalie market was audited across the recorded clean prospective v0.1/v0.2 matched slates from Oct. 6, Oct. 9, Nov. 8 and Nov. 9.

Clean prospective matched sample (**33 goalie props**):
- **v0.1:** 15-18 (45.5%), saves MAE **5.298**, pick Brier **0.275**.
- **v0.2:** 19-14 (57.6%), saves MAE **4.963**, pick Brier **0.244**.

This clears the Oct. 5 pre-written promotion rule: at least 20 clean matched props plus improvement in expected-save MAE and probability calibration/Brier without a worse directional record.

### Promotion decision
- Overall official model version advances to **v0.2.0** effective **2026-11-11**.
- **Goalie v0.2 becomes the official goalie-save probability source** for both Top 10 ranking and Official Playable Price evaluation.
- v0.1 goalie probabilities remain recorded as a diagnostic control.
- The normal goalie playable gate remains unchanged: **4% minimum edge + 5% minimum expected EV**.
- Historical cards are never rewritten.

### Goalie simulation v0.3 research result
A separate v0.3 experiment was built with current-season retraining, 20-game/start baselines and shots-faced -> save-rate Monte Carlo simulation. Seven normalized FanDuel boards (72 matched starts; clean and LATE_LOCK kept separate) were replayed with date-safe training cutoffs.

Clean backfill comparison (40 rows):
- v0.1: 17-23, MAE 5.794, Brier 0.293.
- v0.2: **20-20, MAE 5.358, Brier 0.248**.
- v0.3: 20-20, MAE 5.538, Brier 0.260.

At the existing 4% goalie edge gate on clean rows:
- v0.2: **9-6, +1.7342u, +11.56% ROI**.
- v0.3: **6-9, -3.6844u, -24.56% ROI**.

Therefore **v0.3 is NOT promoted**. It remains research-only. More complexity did not improve the actionable goalie card.

## Next-task rule — effective 2026-11-11
For the next user-supplied slate: refresh current context; run team/game and ATG components as before; run **goalie v0.2 as the official goalie-save model**; retain v0.1 goalie diagnostics and v0.3 research only; lock Top 10 before first puck; then apply FanDuel prices to the full universe for Official Playable. Do not revert official goalie probabilities to v0.1.

## 2026-11-11 CORE MARKET SLATE — CLEAN PREGAME LOCK
Six supplied games:
- TBL@BUF
- NYR@CGY
- PHI@EDM
- UTA@VGK
- PIT@SJS
- NSH@ANA

Final lock completed at approximately **5:46 PM ET**, before the 7:00 PM ET opener. No same-day outcomes/live data entered the model.

This is the first official slate under **v0.2.0**, with promoted goalie v0.2 probabilities feeding Top 10 and Official Playable.

Top 10 expected wins sum: **6.5789**.
Official Playable: **8 selections**.
Playable Price v0.3: **0 selections**.

Top 10:
1. Nashville +1.5 — 70.925%
2. Calgary +1.5 — 70.145%
3. Buffalo +1.5 — 69.950%
4. San Jose +1.5 — 69.915%
5. Utah +1.5 — 68.030%
6. Edmonton ML — 63.560%
7. Laurent Brossoit O22.5 saves — 62.375% (official goalie v0.2)
8. Dan Vladar U24.5 saves — 61.823% (official goalie v0.2)
9. Tristan Jarry O20.5 saves — 60.621% (official goalie v0.2)
10. Philadelphia +1.5 — 60.550%

Official Playable:
- Tristan Luneau ATG +800
- Connor McDavid ATG +115
- Dan Vladar U24.5 saves -125
- Laurent Brossoit O22.5 saves -130
- Yaroslav Askarov O24.5 saves -120
- PIT-SJS U6.5 +110
- Tristan Jarry O20.5 saves -128
- San Jose +1.5 -192

Lineup validation:
- Nico Myatovic was excluded from Anaheim ATG eligibility after being returned to the AHL.
- Utah Mammoth team-name mapping was corrected before the final lock.

Goalie v0.2 official notable plays:
- Vladar U24.5: 61.82%, expected saves 22.96.
- Brossoit O22.5: 62.37%, expected saves 25.12.
- Askarov O24.5: 60.03%, expected saves 26.82.
- Jarry O20.5: 60.62%, expected saves 22.65.

Goalie v0.3 remains research-only and Playable Price v0.3 produced no qualifying selections.

## 2026-11-11 GRADING
- Clean prospective Top 10: **6-4**, Brier **0.2597**.
- Clean Official Playable: **5-3, +1.0354u, +12.94% ROI**.
- Playable Price shadow v0.3: **0 plays / PASS**.
- Official goalie v0.2 executable plays: **3-1, +1.4146u**.
- Full goalie directional diagnostics: v0.1 **8-3**, v0.2 **6-5**, v0.3 research **8-3**.
- After adding this slate to the promotion-era clean matched sample, v0.2 still leads v0.1 overall: **25-19 vs 23-21**, with better approximate cumulative MAE and Brier.
- No predictive code change. Official version remains **v0.2.0**.

## 2026-11-12 CORE MARKET SLATE — CLEAN PREGAME LOCK
Ten supplied games:
- COL@OTT
- WSH@NJD
- TBL@CBJ
- MIN@TOR
- MTL@BOS
- DET@FLA
- BUF@CHI
- WPG@DAL
- STL@UTA
- NYI@LAK

Final model-card lock completed at approximately **4:49:52 PM ET**, before the 7:00 PM ET opener. No Nov. 12 outcomes/live data entered the model.

Model version: **v0.2.0**.
Official goalie component: **v0.2**.
Top 10 expected wins sum: **7.0176**.
Official Playable: **17 selections**.
Playable Price shadow v0.3: **2 selections**.

Top 10:
1. Utah +1.5 — 75.795%
2. Colorado +1.5 — 75.485%
3. NY Islanders +1.5 — 73.965%
4. Washington +1.5 — 70.205%
5. John Gibson O24.5 saves — 69.382%
6. Detroit +1.5 — 68.780%
7. Spencer Knight O24.5 saves — 67.978%
8. Toronto +1.5 — 67.190%
9. Columbus +1.5 — 66.775%
10. Montreal +1.5 — 66.210%

Official Playable:
- Matthew Poitras ATG +650
- Teddy Blueger ATG +900
- John Gibson O24.5 saves -108
- Alex Ovechkin ATG +370
- Nathan MacKinnon ATG +140
- Spencer Knight O24.5 saves -114
- Roman Kantserov ATG +240
- Jacob Fowler O24.5 saves -106
- Utah ML +105
- Anthony Stolarz U25.5 saves -108
- Toronto +1.5 -160
- STL-UTA O5.5 -130
- Detroit ML +142
- Utah +1.5 -235
- Connor Hellebuyck U22.5 saves -125
- Tampa Bay ML -114
- Detroit +1.5 -188

Playable Price shadow v0.3:
1. STL-UTA O5.5 -130
2. Utah ML +105

Official v0.2 goalie playable subset:
- Gibson O24.5 — 69.38%, expected saves 28.78.
- Knight O24.5 — 67.98%, expected saves 28.47.
- Fowler O24.5 — 57.50%, expected saves 26.34.
- Stolarz U25.5 — 57.62%, expected saves 24.64.
- Hellebuyck U22.5 — 59.99%, expected saves 21.35.

Important goalie disagreements to grade prospectively:
- Hellebuyck: v0.1 Over 22.5 (64.06%) vs official v0.2 Under 22.5 (59.99%).
- Gibson: v0.1 Under 24.5 (54.58%) vs official v0.2 Over 24.5 (69.38%).
- Fowler: v0.1 Under 24.5 (58.47%) vs official v0.2 Over 24.5 (57.50%).
- Wallstedt: v0.1 Over 24.5 vs v0.2 Under 24.5.
- Swayman: v0.1 Over 24.5 vs v0.2 Under 24.5.

Lineup validation:
- Linus Ullmark confirmed to return/start for Ottawa.
- MacKinnon and Makar confirmed available.
- Emil Lilleberg excluded from ATG because NHL projected lineups list him scratched.
- Logan Cooley and Dylan Guenther are out for Utah and were not on the submitted ATG board.
- Kevin Fiala expected to return for Los Angeles.
- Patrick Kane and Nick Schmaltz remained eligible because they were not ruled out at lock; grade VOID if they do not play.
- Jack Roslovic remained eligible because NHL's projected lineup listed him despite an injury-list inconsistency; grade VOID if he does not play.

Current-season ATG shadow top group at lock included Kaprizov, Kyle Connor, MacKinnon, Jason Robertson, Cole Caufield, Tage Thompson, Alex Tuch and Brandon Hagel. ATG consensus shadow produced no qualifying card.

