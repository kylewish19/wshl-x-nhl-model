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

## 2026-11-12 — grading completed 2026-11-25
- Clean Top 10 **5-5**, expected wins 7.01765, Brier 0.27318.
- Official Playable **5-12, -8.29604u, -48.80% ROI**, Brier 0.22903. ATG 0-5 (-5u), goalies 2-3 (-1.13068u), ML 1-2 (-1.12281u), spread 2-1 (-0.04255u), total 0-1 (-1u). All settled. MacKinnon played and exited injured, not a DNP.
- Playable shadow v0.3 **0-2, -2u**, Brier 0.32366; both plays STL@UTA. Consensus ATG shadow PASS. Current-season ATG top eight 4-4, winners Kyle Connor, Caufield, Tage Thompson, Hagel. This is a rank diagnostic, not executable price card.
- Goalie recorded picks v0.1 9-8, v0.2 10-7, v0.3 12-5; expected saves MAE 3.3981 / 3.5682 / 3.4034; over-event Brier 0.25396 / 0.25925 / 0.24636. Saved picks sometimes favor price rather than maximum probability; keep these distinct. Kuemper identity unresolved only in v0.3: keep locked fallback and flag; common 16 known-ID rows yield 9-7 / 9-7 / 11-5. Do not retroactively alter probabilities. Review identity resolver before next live run. Need compare maximum-probability directions and same price gates across versions.
- Official v0.2 goalie playable since promotion 5-4, +0.28391u. Two slates not enough to reverse promotion. Continue v0.1 and v0.3 research.
- Current clean cumulative Top 10 63-46; Official Playable 50-88, -41.8203u; Playable shadow 1-5, -4.1667u (six settled, not enough for promotion).
- Full clean market diagnostics saved: ATG 2-22 +1 void (-19.65u), goalie 19-24 (-7.3240u), ML 7-10 (-0.7879u), spread 10-8 (-2.2542u), totals 6-3 (+2.1442u). Prioritize ATG role/TOI/shot-volume calibration and matched goalie workload audits. Keep official control unchanged; recommend paper testing given substantial observed losses.
- Sources: https://www.nhl.com/news/st-louis-blues-utah-mammoth-game-recap-november-12-2026 ; https://www.nhl.com/news/nathan-mackinnon-cale-makar-exit-game-for-colorado-avalanche ; https://daily.hockey/starting-goalies/2026-11-12 ; https://www.agatetypes.com/hockey/november-12-2026 .
- Nov 13–24 skipped for betting; no retroactive official picks. Refresh completed historical games and current context for next slate. No predictive code change in this grading.

## 2026-11-25 — ATG game-level research and goalie identity audit
- Official NHL v0.2.0 remains active; no formula, card thresholds, or historical locks changed.
- Goalie identity: both goalie runners now prefer unique normalized historical full-name matches strictly before target date; ambiguous or initial-only identities are not guessed. Added regression tests. The original identity tests passed CI. New optional `--identity-board` in v0.3 validates the official board's date/game/name/team/line/player ID and rejects unresolved/mismatched rows. **Use this argument on the next new live workflow** (not retroactively on archived runs). Final CI for this additional guard was pending at checkpoint. This reduces API-dependent inconsistency but does not guarantee resolution if historical names are abbreviated and roster data unavailable.
- Added SHADOW_ONLY ATG game-level research: `src/wshlx_nhl/atg_game_shadow.py`, `scripts/train_atg_game_shadow.py`, `tests/test_atg_game_shadow.py`, `.github/workflows/atg-game-shadow.yml`.
- Compare fixed shrunk goal-rate baseline, shrunk shot-volume/finishing baseline, raw histogram gradient boosting, and logistic-calibrated boosting. Chronological split: 2021-22 warmup, 2022-23/2023-24 train, 2024-25 calibration, 2025-26 and 2026-27 through Nov 24 held out separately. No same-game realized shot, goal, or TOI features; no odds. Unit tests for current/future outcome invariance, probability bounds and duplicate rows passed.
- Historical ATG experiment is conditional on actual participation, not a prospective betting backtest. Missing xG, PP TOI, projected line/goalie and archived FanDuel odds. Baselines are not identical to the original official v0.1. No promotion or ROI claims before appropriate matched comparisons and prospective tracking.
- Refresh workflow run 45713367700 and ATG benchmark run 45713698148 were still running at checkpoint; benchmark test step succeeded, dataset/model results not yet verified. Check completion, coverage and metrics next. No new official picks generated. Full CI for later identity guard run 45713763159 pending.
- Next: verify data cutoff and completeness (including missing game counts), inspect benchmark calibration/Brier/log loss by season and experience/role band, compare with frozen official ATG on future supplied slates; investigate xG/PP TOI availability and prospective lineup inputs before adding them. Preserve all official and shadow tracking.

## 2026-11-25 — refresh verified, goalie matched audit, first ATG benchmark
- Resume refresh run 45713367700 succeeded: 6945 completed games, 13890 goalie starts and team-game rows, 385 current-season games through Nov 24, 32 teams, 78 current-season goalies, 732 current-roster skaters. Live skater aggregate not historical-cutoff certified. Metadata saved in data/model_runs/2026-11-25_resume_refresh.json.
- CI run 45713763159 passed all 23 tests including goalie matched identity guard.
- Nov 11–12 common resolved goalie sample 27 rows (Kuemper v0.3 unknown excluded). v0.1/v0.2/v0.3 odds-blind W-L 15-12/14-13/16-11; price-selected directions 17-10/15-12/19-8; MAE 4.38886/4.68378/4.48307; Brier .238868/.255206/.241564. Identical 4% edge and 5% EV gate on locked forecasts: 8-2 +4.93434u / 5-4 +0.28391u / 3-2 +0.65185u. Two slates only; not enough to reverse prior goalie promotion. Preserve earlier results. Detailed audit in data/results/goalie_matched_postpromotion_2026-11-12.csv and corresponding detail file.
- ATG initial run 45713698148 fetched 6945 games but stopped at invalid counts. Archive audit run 45714769216 succeeded using immutable first-run input. 249950 player-game rows, 23 goals>shots discrepancies (0.0092%); no missing/negative/PP>goals. Under predeclared research sensitivity policy, shots=goals lower-bound proxy only on those rows in lagged histories, exclude them from fitting/calibration/testing, original raw archive preserved. Not verified corrections. Audit and artifact contain rows and heldout predictions.
- First held-out ATG benchmark: train 94423, calibration 47221, test 47221 (2025-26) and 13857 (2026-27 to Nov 24). Brier 2025-26 / 2026-27: goal baseline .1219985/.1235268; shot/finish .1206734/.1220343; raw boosting .1216648/.1235569; calibrated boosting .1204703/.1221938. Shot model improves over goal baseline both seasons, calibrated boosting narrowly better in 2025-26 but not 2026-27. No clear dominance of complex model. Limited-history (<10 prior dataset GP) actual 9.59%/11.03%; goal baseline 14.08%/13.75%; shot 12.97%/12.15%; calibrated boost 11.10%/10.69%. Promising calibration but not proof of profit or superiority over official v0.1. Metrics and bands committed in data/model_runs/2026-11-25_atg_game_shadow_metrics.json and data/results/2026-11-25_atg_game_shadow_bands.csv.
- Decision: retain shot-volume baseline and calibrated boosting as separate research comparators. Do not select a new official ATG or tune on these now-observed holdout seasons. Next build strictly pregame future-board scoring, match original official predictions on identical eligible players, freeze both challengers and log prospective probabilities and FanDuel prices independently. Add role/PP TOI/xG only with dated source and new untouched test window. No official model change, no retroactive picks.

## 2026-11-25 — ATG pregame integration checkpoint
- Added src/wshlx_nhl/atg_pregame.py and scripts/run_atg_pregame.py. Both new ATG challengers score strictly prior player and team history using benchmark-consistent rolling features; use frozen calibrated model bundle from archive audit run 45714769216 and immutable history from run 45713698148, extending only completed regular-season games before target when needed.
- Match against full official ATG candidate CSV using date/game/player ID, listed/resolved teams, and active status. Unknown position, unresolved IDs, inactive and mismatched-team rows audited and excluded from the matched comparison only; original official universe untouched. Historical positions used unless verified position provided; actual participation remains unverified.
- Save odds-free probabilities before matched FanDuel pricing; compare official, shot/finish and calibrated boosting using identical 5pp edge and 5% expected ROI gate. All shadow cards paper only; official v0.2.0 unchanged.
- Live runner verifies Eastern date, NHL schedule matchup and all scheduled games FUT/PRE before first puck, checks time again after scoring, refuses overwrite of nonempty output directory and hashes input, model and output files. Manifest status remains PREGAME_PENDING_ARTIFACT_VERIFICATION until external artifact timestamp is verified. Replay always RETROSPECTIVE_SMOKE_ONLY; no retrospective official selections.
- Added tests/test_atg_pregame.py for training/pregame feature parity, odds invariance, future-date rejection, matching and price gates. Added .github/workflows/atg-pregame-shadow.yml; first archived full Nov 12 board integration test run 45715282170 initiated; final CI and replay outcome not yet verified. Historical artifact expires under GitHub retention policy; pin/recover frozen history and model before expiration. No new prospective predictions or results in this step.
- Next: inspect replay results and fix integration defects if any; save manifest/coverage and set up matched postgame grader before live use. Keep both challengers shadow-only; do not claim historical profit or change official model.

## 2026-11-25 — ATG integration and matched grading verified
- Pregame integration run 45715282170 succeeded; 30 tests passed. Archived Nov 12 full board: 343 candidates, 337 matched, 5 unresolved identities and 1 inactive excluded. Prior data cutoff Nov 11. Equal price gate qualified official 5, shot-based 2, calibrated boost 3. Manifest preserved in data/model_runs/2026-11-25_atg_pregame_smoke_manifest.json.
- Added src/wshlx_nhl/atg_grading.py, scripts/grade_atg_pregame.py, tests/test_atg_grading.py and .github/workflows/atg-shadow-grading.yml. Grader checks source workflow success/path, artifact metadata and timestamp, frozen probability and price hashes, matched player IDs, complete final games, and goal outcomes; DNP paper void. No refitting or postgame re-selection. Live dispatch by source run ID; replay permanently separate.
- Grading run 45715871716 succeeded through grading/artifact upload; 33 tests passed. Ten games, 337 matched, 332 settled, 5 DNP void. Official/shot/boost replay Top 10 4-6/6-4/6-4, Brier .126633/.122669/.124092, log loss .411120/.400432/.401642, AUC .695205/.719078/.710759. Equal price paper records 0-5 (-5u), 0-2 (-2u), 1-2 (+3.5u). RETROSPECTIVE_SMOKE_ONLY; no clean prospective or official season records changed; do not use this previously observed period as independent promotion evidence. Summary and manifest persisted in REPLAY_ONLY result and grading smoke manifest files.
- Frozen research provenance saved in config/atg_frozen_research_2026-11-25.json (hashes, source runs, dependency versions and artifact expiry). Original history artifact expires Dec 25 2026; trained model artifact expires Feb 23 2027. Repo is public, so did not publish binaries to main without explicit authorization. Download/save original artifacts privately before expiry. Refetching historical data may yield changed data; hashes must be checked. Long-term binary preservation still open.
- Next: prospective use with a full official candidate CSV and clean pregame verified upload; run matched grader after final games. Keep official v0.2.0 and both ATG challengers unchanged. Investigate PP TOI, xG and projected lines with dated sources and fresh holdout; improve goalie and team models through separate experiments. No new official picks.

## 2026-11-25 — advanced ATG source feasibility and team identity coverage
- Reviewed MoneyPuck data terms (https://moneypuck.com/data.htm): free noncommercial/ad-hoc journalist use with credit; no ingestion performed. NHL website terms (https://www.nhl.com/info/terms-of-service) also limit use and prohibit unauthorized automated collection. API-specific permission and intended commercial-use rights are not established; no new full-scale advanced-stat collection or redistribution authorized. Continue developing offline code with synthetic or appropriately licensed/authorized inputs; obtain applicable permission/source terms before bulk collection and commercial deployment. Earlier historical research artifacts are not a commercial license.
- Added scripts/probe_atg_advanced_sources.py, tests/test_atg_advanced_sources.py, .github/workflows/atg-advanced-source-audit.yml and docs/ATG_ADVANCED_DATA_PROTOCOL.md. Source audit run 45716267696 succeeded, 36 tests passed. First/middle/last archived game from each of six seasons: 18 games, 1,568 unblocked attempts including 111 goal events; 0 missing/unmatched shooter IDs, geometry, strength or opposing-goalie state; one missing shot type. NHL game-level timeonice and powerplay reports each returned 648 rows; observed ppTimeOnIce, evTimeOnIce, shTimeOnIce, ppShots and ppIndividualSatFor fields, including actual zeros. Sample feasibility only; not full coverage or verified all-row PP joins. Persisted source coverage CSV and example schemas JSON under data/results and data/model_runs. No xG fit yet.
- Fixed missing CAR and SEA in scripts/assemble_core_slate.py TEAM_NAMES map and added test requiring all 32 active teams; CI run 45716355962 pending at checkpoint. Identity mapping correction only; no predictive formula changed and no historical lock rewritten.
- Next: develop offline shot-level xG cross-fitting and PP usage feature ingestion with synthetic/authorized inputs, verify full coverage only once source rights resolved; retain frozen ATG challengers and focus also on existing-data goalie/team model diagnostics. No new official picks, no model promotion, official v0.2.0 unchanged.

## 2026-11-25 — direct final-score team-market research
- Existing official game_markets.simulate_game resolves simulated ties only for ML; spread and total calculations use unadjusted independent Poisson scores. This is a structural limitation, not evidence by itself of an advantage for any challenger. Official formulas and historical locks untouched.
- Added src/wshlx_nhl/team_market_shadow.py, scripts/benchmark_team_market_shadow.py, tests/test_team_market_shadow.py and .github/workflows/team-market-shadow.yml. Direct multinomial final-margin classes (away 2+, away 1, home 1, home 2+) and total classes (<=5, 6, >=7), regularized logistic classifiers with prior/current goal averages, lagged 5/20-game goals/shots and rest. Chronological feature tests passed; baseline is analytic infinite-simulation equivalent of official v0.1 team model with zero context. No new data downloads, reused archived refresh artifact.
- Benchmark run 45716648252 completed scoring, 40 tests passed. 6,945 games; 3,936 train (2022-23 through 2024-25), 1,312 2025-26 and 385 2026-27 diagnostic games through Nov 24. Direct model lost all five Brier comparisons in 2025-26; won two of five in 2026-27 (home ML .238001 vs .241238; away -1.5 .196028 vs .198435). Baseline won remaining eight of ten season-market comparisons. Direct model overpredicted home -1.5 (35.26% vs actual 30.11%; 34.70% vs actual 29.35%), underpredicted over 5.5 (52.27% vs 57.32%; 51.25% vs 59.48%). No promotion, no prospective challenger deployment justified by this benchmark. Metrics and manifest archived.
- Limitations: shots derived from goalie shots faced, not exact team SOG; no verified pregame goalie/lineup context, no archived odds; previously observed seasons are development diagnostics only. Do not tune to these results then claim independent validation.
- Next team research: isolate final-score tie treatment from rate-model changes, assess score distribution and era calibration on earlier training/calibration windows, freeze before genuinely new prospective slates; consider goalie quality only with dated pregame identities. Next goalie research: audit shots-faced workload prediction and short-start effects using existing archived data. Advanced xG/PP full collection still blocked by unresolved permissions; frozen ATG shadows ready. Official NHL v0.2.0 unchanged; no new picks or season record changes.

## 2026-11-25 — isolated team tie treatment and goalie workload audit
- Added team_tie_shadow.py, benchmark_team_tie_shadow.py, regression tests and team-tie-shadow workflow. Run 45717100136 succeeded, 42 tests passed. Analytic comparison on existing 6,945-game archive: unchanged baseline, resolve tied simulated score with one credited goal, preserve expected final total by solving regulation scale, and mean-preserving version with factor 0.993493 fitted on 2024-25 only. With fixed rates, tie resolution leaves ML, +/-1.5, and O5.5 unchanged; O6.5 gains probability of simulated 3-3. 2025-26/2026-27 baseline O6.5 Brier .250934/.253872; tie-only .248502/.250762; mean-preserving .249211/.251875; calibrated .249591/.252342. Actual O6.5 frequencies 46.875%/49.091%; baseline 41.946%/43.477%; tie-only 46.885%/48.348%. Mean reductions hurt O5.5 on both evaluation seasons. Tie-only promising diagnostic for totals, not promoted; regulation labels unavailable, expected means currently based on final scores (risk of double-counting), previously observed seasons not independent promotion evidence. Metrics and manifest saved.
- Added scripts/audit_goalie_workload.py and goalie-workload-audit workflow. Run 45717165583 succeeded through scoring/upload, 42 tests passed. Reconstructed official v0.2 trained from pre-July 2026 archive (13,120 input rows, internal chronological split); 770 actual 2026-27 starts through Nov 24 evaluated. Overall shots MAE 5.0602, saves MAE 5.0997, expected minus actual shots +0.4599, saves +0.6819. 38 starts under 50 min (4.94%) had actual shots 13.76 vs predicted 27.60, saves MAE 14.9084; 89 starts 50–<58 min saves MAE 4.3989; 643 starts >=58 min saves MAE 4.6171. Realized duration only diagnostic, never pregame feature; short starts not necessarily pulls. Actual total team shots minus starter shots averaged 12.32 in short cohort vs zero in >=58 min cohort. All 770 rows reported rest >=2 days: verify source goalie IDs/date order and rest feature distribution before using fatigue as a discriminator; no evidence for short-rest effects from this sample. Metrics and manifest persisted. Historical diagnostics conditional on actual starters, not frozen daily predictions or betting backtest.
- Next: investigate rest-feature coverage and archived starter identity integrity; test a pregame-only short-start mixture with fixed earlier-season training/calibration and common test rows, not actual minutes as input. Develop totals shadow integration only after evaluating regulation assumptions and freezing prospective protocol. Preserve existing official and shadow cards. No new picks, no promotion, official v0.2.0 unchanged.

## 2026-11-25 — goalie rest integrity and shortened-start mixture benchmark
- Added src/wshlx_nhl/goalie_short_shadow.py, scripts/benchmark_goalie_short_shadow.py, tests/test_goalie_short_shadow.py and .github/workflows/goalie-short-shadow.yml. Run 45717517239 succeeded through scoring/artifact upload, 44 tests passed. Reused existing archive only.
- Independently rebuilt days between starts and previous seven-day start counts by stable goalie ID/date. All 13,890 rows matched archived rest and seven-day counts exactly; all had explicit starter flag. Rest <=1 day by season: 66, 46, 16, 28, 35, 0 (2021-22 through current 2026-27). Thus the current zero is present in source history, not explained by a rest calculation bug. Not externally verified; no inference about relief appearances, true fatigue or league schedule. Do not fabricate back-to-back records.
- Short-start (TOI <3000s) risk model trained on 5,248 starts 2022-23/2023-24, calibration 2,624 starts 2024-25, fixed risk 4.8018%; 2025-26 and 2026-27 diagnostic sets 2,624 and 770. Lagged short-start rate, recent goalie/team stats, home, rest and prior starts only; realized duration is label only. Learned risk modestly beat constant risk on Brier (.048325 vs .048469; .046509 vs .046917) and log loss, AUC .57394/.62892. No independent prospective evidence.
- Compared matched simple Poisson regression means with calibrated NB single distribution, constant short/full mixture and learned mixture on synthetic half-goal save lines 20.5/24.5/28.5. Single distribution won all 3 Brier comparisons in 2025-26; current season constant mixture narrowly won 20.5 (.203108 vs single .203823), single won 24.5 (.239797), learned mixture marginally won 28.5 (.176965 vs single .176999). Single distribution had best saves MAE in both seasons (5.40925/5.07566 vs learned 5.41797/5.08048). No compelling overall mixture improvement. This is not a direct comparison to official v0.2, no actual FanDuel lines or prices, actual-starter conditional and previously examined evaluation windows.
- Decision: retain existing goalie v0.2 official and v0.1/v0.3 comparators. Do not promote or deploy short-start mixture; keep risk finding for future research. No historical record changes. Archive rest/risk/counts/metrics and manifest. Next: build a prospective paper-only totals tie-treatment comparator (only fixed 5.5/6.5 scope) and prepare one integrated workflow for existing ATG and goalie comparators on next user-submitted slate. Verify archived data source completeness before relying on unusual rest patterns; advanced-stat rights and artifact preservation remain unresolved.

## 2026-11-25 — unified daily shadow comparison
- Added src/wshlx_nhl/daily_shadow.py, scripts/run_daily_shadow.py, tests/test_daily_shadow.py and .github/workflows/daily-shadows.yml. New runner consumes successful frozen official core workflow artifact (date, game, model board, team means, goalie v0.1/v0.2/v0.3 files), checks source workflow metadata, frozen ATG model/history hashes, date and first-puck cutoff. Live result remains PREGAME_PENDING_ARTIFACT_VERIFICATION until independent output upload timestamp is checked. Archived replay is RETROSPECTIVE_SMOKE_ONLY; never counted toward prospective records.
- Totals shadow fixed to 5.5/6.5: official locked probabilities vs analytic Poisson control vs tie-only adjustment; 6.5 over gets probability of 3-3 tie, 5.5 unchanged. Uses exact archived team means, no estimated future score inputs; edge>=3pp, EV>=5%. Goalie comparison: matched resolved player IDs, game, team, half-line and prices across v0.1/v0.2/v0.3, excludes mismatches from research only; choose higher-EV side, edge>=4pp, EV>=5%. Nested frozen ATG paper boards use original 5pp/5% gates. No model/official threshold change.
- Unified workflow run 45718113354 initiated with Nov 12 archived board; final smoke result and CI not verified at time of initial entry. Existing original daily cards and earlier shadows remain separate. No live slate generated. Next verify run and persist manifest; implement unified postgame grading for totals/goalies, plus wrapper to verify parent artifact timestamp for nested ATG, and maintain separate prospective cumulative log. Live use requires a successful official pregame artifact in time before first puck; not a replacement for official core run. Long-term frozen artifact retention still unresolved.

## 2026-11-25 — unified daily comparison and grading verified
- Unified comparison run 45718113354 succeeded (46 tests). Archived Nov 12 slate: 10 total pairs, 16 matched goalie lines (1 identity mismatch excluded), 337 ATG candidates. Manifest saved data/model_runs/2026-11-25_unified_shadow_smoke_manifest.json.
- Added src/wshlx_nhl/daily_shadow_grading.py, scripts/grade_daily_shadow.py, tests/test_daily_shadow_grading.py, .github/workflows/daily-shadow-grading.yml. Validates parent/nested artifact hash and pregame timestamp chain, reads completed game-level team, starter and skater outcomes, grades paper selections without recomputation. Totals and goalie calibration use one Over probability per line. Goalie requires explicit starter flag and nonstarter void; ATG DNP void. Cumulative Brier/log loss observation-weighted; duplicate date/market/model blocked. No automatic official changes.
- Grading replay run 45719012128 completed successfully (49 tests), 10 games, 0 prospective ledger rows. ATG official/shot/boost Brier .126633/.122669/.124092 and price records 0-5 (-5u), 0-2 (-2u), 1-2 (+3.5u). Goalies v0.1/v0.2/v0.3 Brier .249003/.260592/.246601, price 4-2 (+1.42716u), 2-3 (-1.13068u), 2-2 (-.14815u); agree with earlier matched Nov 12 audit. Totals official/analytic/tie-only Brier .257549/.258349/.246890, price 0-1 (-1u), 0-1 (-1u), 1-1 (+.12u). Replay results never independent promotion evidence; no official record edits.
- Initialized data/results/prospective_shadow_ledger.csv (header only), docs/DAILY_SHADOW_GRADING.md. Live grader defaults to existing canonical ledger, outputs updated ledger/cumulative artifacts; reviewed commit required to persist, no automatic write rights. Last default-ledger-path change after replay is pending its own CI verification. Live requires a successful pregame official core and unified artifact plus authorized complete finalized outcome files; no live slate tested yet. Existing artifact retention and advanced data permissions still unresolved.
- Next: verify current CI, address retention/provenance, then execute next fresh user-submitted slate and record clean prospective results. Do not keep tuning on the already examined evaluation seasons. Official v0.2.0 remains unchanged.

## 2026-11-25 — slate readiness and frozen research recovery
- Latest canonical ledger default-path CI run 45719086287 succeeded; 49 tests passed. Prior prospective ledger still header-only.
- Added scripts/preflight_slate.py, tests/test_preflight_slate.py, .github/workflows/slate-readiness.yml. Offline exact-date and game/team validation, complementary spreads, finite numeric context, integer American odds, full six core prices per matchup, duplicate player/line checks, explicit missing ATG/goalie game coverage and input SHA-256 hashes. Requires four nonempty boards; partial/late boards remain separate, not silently filled. Does not independently authenticate sportsbook, current schedule, player eligibility or timestamp. Workflow 45719463447 succeeded (52 tests) on archived Nov 12: 10 games, 60 core rows, 343 ATG rows, 17 goalie lines, no games without either player market. Verified original artifact availability and expiry metadata (not payload hashes in this workflow); manifest data/model_runs/2026-11-25_slate_readiness_smoke.json. No new picks.
- Added scripts/verify_research_backup.py, tests/test_research_backup.py, docs/FROZEN_RESEARCH_RECOVERY.md. Verifies original four binary payload hashes from private ZIP copies without extraction/unpickling. Actual private backup has NOT been created; no private destination supplied, public raw-data publication avoided. Original history 15067769899 and team/goalie 15069296241 expire Dec 25 2026, ATG bundle 15068418480 expires Feb 23 2027; download before expiry, verify and retain privately. Current workflows still reference original runs; recovery after expiry requires reconfiguring authorized artifact source. Backup tests pending CI at checkpoint.
- Next: use next fresh user-supplied FanDuel slate; complete dated official core run with independently checked schedule, pregame context and authorized current data, then unified research grading. Generic reusable official core runner has not been built; existing date-specific workflow is the basis. No official predictive or record changes. Advanced data rights unresolved, no further historical tuning justified absent fresh prospective evidence.


## 2026-11-25 — first fresh official and unified live slate locked
- User supplied 14 games, 84 core prices, 481 ATG rows, 24 goalie lines; 613 raw selections. Source inputs and context committed. Four known scratches excluded (Raddysh, Chaffee, Mayfield, Ethen Frank); no unresolved IDs in official matching. Missing TBL/NSH/UTA/CHI goalie lines not invented. Reused verified Nov24 prior team/goalie history and Nov25 pregame skater transition snapshot; exact identity corrections logged in data/context/2026-11-25_pregame.md. No invented numeric context adjustments or new xG/PP features. Official formulas and gates unchanged.
- Official run 45723015990 success, artifact 15073700466 uploaded 18:40:24 ET before 19:00 ET first puck. Clean Top10 10 (expected 6.9189122759), Official Playable 20 (expected 9.6658369601), price shadow 4 (expected 2.0982105222), ATG consensus PASS. Frozen card CSVs, 24 goalie rows for each official/control and v0.3, current ATG top30 and core lock summary committed. Full original candidate/artifact remains authoritative; stdout CSV copies do not replace exact original artifact. No grades yet.
- Unified live run 45723215283 success (54 tests), artifact 15073920102 uploaded 18:41:33 ET, independently before cutoff; first clean prospective unified lock. 14 totals pairs, 24 common goalie lines, zero excluded goalie rows; qualifying totals official/analytic/tie 3/2/1; goalie v0.1/v0.2/v0.3 15/8/5. Frozen ATG comparisons included in artifact; exact ATG card counts not printed in parent manifest. Verified manifest committed data/model_runs/2026-11-25_unified_shadow_live_manifest.json. No promotion or grading yet. Workflow push fallback now references this live core run; use explicit date/run input for next slate rather than rerunning stale fallback.
- Next: grade Nov25 official and paper cohorts only after all games final, with authorized complete outcome data; preserve artifact hashes/timestamps and update season summary, lessons, reviewed prospective ledger. Private original-artifact backup and advanced data rights remain unresolved. No clean records change until grading.

## 2026-11-26 — Nov25 clean grading and prospective diagnostics
- Verified all 14 finalized games, original core artifact 15073700466 and research artifact 15073920102 against pregame timestamps/hashes. Grading run 45828937854 succeeded; artifact 15122245729. Official Top10 5–5 (expected 6.9189, Brier .29616), Playable 10–10 (+17.78056u, ROI .88903), price shadow 3–1 (+1.56210u). All official selections settled; no voids. Cumulative clean Top10 68–51 (57.14%), Playable 60–98 (37.97%, -24.0397u), price shadow 4–6 (-2.6046u). Late-lock cohorts unchanged. Cumulative Brier uses previous rounded aggregate.
- Top10 nine puck lines went 4–5, Oettinger O21.5 won with 24 saves. Do not force diversity or change weights after one slate. Investigate persistent puck-line calibration and underestimation of multi-goal margins using existing chronological data rather than this slate alone. Official price ATG 2–4 (+17u) because Simashev +1500 and Knuble +600 scored; five limited-history qualifiers 2–3, do not infer fallback calibration from two high-paying hits. Excluding ATG, official price 8–6 (+0.78056u). Totals 3–0, goalie saves 4–4, spread 1–1, ML 0–1.
- First clean unified prospective ledger: totals official 3–0 (+2.5621u), analytic 2–0 (+1.6530u), tie-only 1–0 (+.8197u); matched 14 Brier .241212/.240640/.249376 respectively. Goalie v0.1 9–6 (+2.02834u), v0.2 4–4 (-.32502u), v0.3 4–1 (+2.72552u); 24 matched/settled, Brier .252743/.249866/.243781, saves MAE 3.7758/4.0476/3.8557. Unanimous goalie directions 7–4; unanimous and v0.3 price gate 4–1; all three price gates 3–0 (Oettinger, Tarasov, Merilainen). These groups were displayed pregame, but not official cards; preserve as separate prospective diagnostic, sample too small, two picks share VAN@DET game. No promotion. ATG matched 476, 473 settled, 3 void; official/shot/boost Brier .133812/.131314/.131625; top10 2–8/5–5/4–6; price 2–4 (+17u)/0–4 (-4u)/0–4 (-4u). Current-season blend full-board top10 5–5, consensus pass. Different matched/full populations noted. No new ATG model promotion; lower Brier and higher top10 accuracy do not imply profitability.
- Persisted three official graded CSVs, grading summary JSON, updated season summary and first nine prospective ledger rows. No predictive code or gate changes. Next: retain frozen models, grade future slates on identical cohorts, maintain agreement diagnostic separately; analyze persistent calibration and limited-history risk only with chronological evidence. Grading fetched finalized box scores for this one slate, not a full historical refresh or advanced-data acquisition. Private backup/advanced-data permissions remain unresolved.

## 2026-11-26 — selected +1.5 puck-line calibration audit
- Re-read all 12 clean official Top10 and Playable graded cards, excluded late locks and voids; every tracked puck-line pick in these cohorts was +1.5. Top10 28–22/50 (56.00%) vs mean 70.5419%, expected 35.27096 wins, Brier .269413; before Nov25 24–17/41 vs expected 29.01821. Sep–Oct 13–6 vs 13.65036 expected; November 15–16 vs 21.6206 expected. Probability bands .60–.65: 3/3; .65–.70: 10/19; .70–.75: 11/22; .75+: 4/6. Playable 11–9, mean 69.2716%, -2.71074u, ROI -13.5537%; cohorts overlap and must not be pooled.
- Existing archived zero-context analytic benchmark (2026-11-25_team_tie_shadow_metrics.csv baseline) implies multi-goal margin frequencies predicted vs observed: 2024–25 53.91% vs 61.74%, 2025–26 53.86% vs 56.78%, current season through Nov24 54.48% vs 58.44%. This supports a broad margin underestimation issue, but full-schedule baseline and selected actual card gaps are not interchangeable. The direct final-score class challenger did not consistently beat baseline Brier across spread directions and seasons; tie-only correction leaves ±1.5 unchanged. No further tuning on observed holdouts, no arbitrary 14.5pp haircut, no official changes. Keep matched prospective spread comparison as next implementation task, alongside consensus goalie tracking.
- Created scripts/audit_puckline_calibration.py (read-only, exact clean filename matching; script not independently executed yet) and data/results/2026-11-26_puckline_calibration_audit.json (computed directly from archived graded rows and existing benchmark metrics). No new games or advanced data gathered, no new predictive fit or picks.

## 2026-11-26 — prospective margin and goalie consensus integration
- Added src/wshlx_nhl/margin_consensus_shadow.py, four parameterized/unit tests, extended unified runner/grader and workflows; original trained direct final-score classifier frozen (training seasons 2022–23 to 2024–25; no refit), archive and bundle hashes pinned. Strict pregame prior team data, extends with prior finalized games only; analytic same-means control and original official ±1.5 probabilities, 3pp/5% price gate, one +1.5 event per game for scoring, both sides eligible for price. Goalie unanimous direction uses strict probability sign, price groups require same direction to qualify, no ties counted; separate ledger and paper records, average probability diagnostic only. Older locks remain gradeable. Nov25 seed labeled PREGAME_DISPLAYED_DIAGNOSTIC, not independent new card: 7–4 direction, 4–1 (+2.72552u) v0.3 gate, 3–0 (+2.78213u) all gates. Future ledger rows CLEAN_SHADOW_PREGAME. Never pool overlapping groups.
- Successful Nov12 replay pregame 45830267675 artifact 15122077351 and grading 45830415087 artifact 15122427061; 58 tests passed; audit script executed. Spread official 2–1 (-.04255u), analytic 3–1 (+.34206u), direct 3–2 (+2.11553u), Brier .203713/.202461/.208852 on 10 pairs. Consensus 5–2 direction, 2–1 v0.3 gate, zero all gates. Archived summaries explicitly REPLAY_ONLY, no new clean entries or promotion. Final hash guard and empty-group flag validation committed after smoke; latest CI status to be checked. Docs MARGIN_CONSENSUS_SHADOW.md. Live dispatch explicitly requires date/core run; push fallback now Nov12 replay. Next verify first fresh live expanded lock and commit both prospective ledgers after grading; original private archive backup and advanced-data permission remain unresolved. No new predictive fit or official code/price changes.

## 2026-11-26 — ATG limited-history fallback and selected price audit
- Read actual official fallback code: previous-season GP<10 triggers current goals plus five games of prior position median, divided by current GP+5, Poisson ATG conversion; not career GP<10. No direct shot volume, TOI, finishing or opponent adjustment. All 12 clean official price cards: ATG 4–26, 1 void, 8.04368 expected wins, 26.8123% mean P vs 13.3333% hit, -2.65u (-8.8333% ROI); before Nov25 2–22 (-19.65u). Price bands +100–299 2–4 (-1.65u), +300–599 0–6 (-6u), +600–999 1–10 (-4u), +1000+ 1–6 (+9u). No odds cutoff inferred from small samples.
- Added scripts/audit_atg_fallback.py and workflow atg-fallback-audit.yml. Run 45830831807 artifact 15122162548, 58 tests passed, 6921 matched historical player-games with previous season GP<10 (5731 in 2025-26,1190 current through Nov24). Lagged current season counts, previous season medians from original archive, F/D rather than exact C/L/R/D codes so baseline is explicitly proxy, not exact official historical predictions. Actual-participant cohort, previously viewed seasons, no odds. Overall proxy P 11.164%/11.033% vs actual 11.063%/11.092%; Brier proxy .098356/.098138, shot .097208/.097224, frozen calibrated boosting .096643/.096988. Proxy P>=20%: 542 rows 2025-26 (24.10% vs 15.87% actual), 152 rows current (25.15% vs 22.37% actual), both challengers improve Brier there. No uniform overconfidence across all fallback players. No refit or threshold tuning.
- Nov25 immutable matched board 476 rows, 473 settled. Fallback 45 settled, 9 goalscorers (20%) vs official mean 11.95%; Brier .144804 official, .147044 shot, .151083 boosting. Fallback qualifiers 2–3 (+18u) official, 0–2 (-2u) shot, 0–1 (-1u) boosting. Established-anchor 428 settled/3 void; mean 13.81% official vs actual 16.12%, Brier .132656 official, .129660 shot, .129579 boosting. Official five fallback qualifiers included Simashev +1500 and Knuble +600; both alternatives would exclude both winners at identical 5pp/5% gates. Retrospective hybrid (official anchor, replace fallback with shot/boost) full-board Brier .134025/.134409 vs official .133812; paper 0–3/0–2 vs official 2–4. Do NOT promote hybrid or blanket-reduce fallback: historical proxy evidence modest, fresh slate contradictory. No new clean cohort created. Next implement basis-stratified matched prospective reporting and separate fallback/anchor price metrics; collect more slates before considering any architecture/gate changes. Audit output CSVs, manifest and workflow archived. Latest prior integration CI 45830614589 passed; no model promotion. Original data permissions/private backup outstanding.

## 2026-11-26 — ATG basis-stratified prospective grading integration
- Added src/wshlx_nhl/atg_basis_grading.py and 4 tests; exact pregame official model_basis retained in nested ATG probability/price outputs and checked against manifest counts and both file hashes. Three disjoint groups: limited_history (limited_history_fallback prefix), established_anchor (transition_ml_anchor), other_or_unknown. Identical matched participants, original frozen qualifying flags and profits; no new picks, fit, gate or promotion. Each group/model reports coverage, settled/void, observed and expected goalscorers, Brier/log loss/AUC, and paper records/ROI. Cumulative observation-weighted metrics, no pooled AUC. Separate ledger rejects duplicate date/group/model; excludes replay and segregates prior frozen-source subgroup review from clean future subgroup locks. Older locks remain gradeable.
- Verified Nov25 original core candidate hash, pregame unified artifact timestamps/hashes, exact identity/probability/price/flag match to original graded artifact. Frozen basis review workflow 45831401192 success, artifact 15122537876, 62 tests passed. Independently reproduced prior audit: 45 fallback settled, 9 scorers, 431 anchor matched/428 settled/3 void, 69 scorers, no unknown. Fallback official/shot/boost price 2–3 (+18u)/0–2 (-2u)/0–1 (-1u); anchor 0–1/0–2/0–3. Ledger data/results/atg_basis_ledger.csv seeded with 9 rows explicitly FROZEN_SOURCE_SUBGROUP_REVIEW (classification added after outcomes, not new clean validation). Docs ATG_BASIS_GRADING.md. New pregame runner and unified grader integration committed and unit-tested, not yet run end-to-end on a fresh live lock. Official and existing prospective ledgers unchanged. Next fresh slate: verify expanded lock and grade all research outputs, commit basis/consensus/spread ledgers separately. Do not keep tuning on viewed dates; consider reusable daily core runner and artifact retention before more research. Private backup and advanced-data permissions remain unresolved.

## 2026-11-26 — reusable daily core runner
- Added scripts/run_daily_core.py, core-slate.yml, reviewed date-specific context JSON, 3 tests and docs/DAILY_CORE_RUNNER.md. Explicit live workflow dispatch or commit config/daily_core_request.json with date/mode after four FanDuel input boards and dated context review. Same official model, odds-blind Top10/full price universe and gates. No date-specific workflow needed. Legacy assembler scratch preserved for archived workflows, reusable path uses explicit dated scratches only. Exact ATG identity/alias review and unresolved audit, goalie identities fail closed. Original 6945-game archive hashes verified; incremental prior finalized game fetch with identity/count/starter checks and lagged new goalie feature generation, original rows preserved. Live snapshot only before first puck, original replay snapshot/goalie IDs reused. No raw history or fitted binaries uploaded. Live request serialization, duplicate artifact guard and independent GitHub upload timestamp verification added. Unified shadow workflow auto-triggered on successful reusable core completion, only live-named artifact; replay/failure skips. Existing manual research dispatch supported. Official/shadow grading and ledger review still separate manual steps; context/screenshot ingestion manual.
- First replay 45831929445 failed strict float parity on tiny goalie solver drift (largest rounded-log difference about 6.54e-6 absolute), same card counts. Corrected parity requires exact identities, ranks, prices, active flags and order; non-goalie probability tolerance 1e-10, goalie max absolute 1e-4 (0.01 percentage point), actual differences reported. Successful replay 45832161726 artifact 15122339343 reproduced all 613 rows and 10/20/4 cards with zero reported probability drift. Final guarded workflow replay 45832211357 artifact 15122129759 passed; parity {"core_candidates":{"rows":613,"max_absolute_probability_delta":{"model_probability":0},"exact_selection_price_rank":true},"top10":{"rows":10,"max_absolute_probability_delta":{"model_probability":0},"exact_selection_price_rank":true},"playable":{"rows":20,"max_absolute_probability_delta":{"model_probability":0},"exact_selection_price_rank":true},"playable_shadow_v0.3":{"rows":4,"max_absolute_probability_delta":{"model_probability":0,"calibrated_probability":0},"exact_selection_price_rank":true}}; 65 tests passed, no research error. Manifest archived REPLAY_ONLY. Automatic research skip verified run 45832321618; independent full research replay 45832065555 succeeded with 65 tests. No original records changed, no new prospective evidence, no predictive weights/gates changed. Live-only duplicate/cutoff check and incremental history fetch not exercised end-to-end on fresh slate; first expanded live lock pending. Legacy Nov11 workflow was triggered by assembler edit; not an eligible new lock or grading source. Private artifact backup/advanced-data permissions remain outstanding. Reusable official runner is scoped to current 2026–27 season and requires nonempty four boards; fully missing market needs explicit supported partial handling. Next: verify fresh live end-to-end and improve reusable postgame grading/ledger review, address private archive retention before expiry. Do not repeatedly tune on old results.

## 2026-11-26 — reusable postgame grading
- Added scripts/grade_daily_core.py, grade-core.yml, 3 settlement/ledger tests and docs/DAILY_CORE_GRADING.md. Explicit target_date/core_run_id/optional research_run_id via workflow dispatch or config/postgame_grade_request.json. Verify successful main workflow metadata, clean original core timestamp, all frozen core hashes, candidate/card probabilities/prices, research artifact linkage and source hashes. Fetch finalized locked games only, strict date/game/team/start/participation validation via existing boxscore parsers; settle original frozen picks, no rescoring. Grade Top10, Playable, price shadow, ATG blend Top10, ATG consensus; unified grader handles totals, goalies, spreads, goalie consensus, ATG and basis where present. Pushes/DNP/nonstarter excluded from settled accuracy; empty cards supported. Raw outcome data not uploaded. Produce derived grading artifacts, proposed season summary and separate research ledgers, prior ledger hashes for publication review; no automatic canonical writes. Reject duplicate graded dates; optional official-only run explicitly marks research not supplied. Preserve existing historical cumulative rounding convention. Later research-only grading uses existing workflow.
- Original Nov25 frozen-source review run 45832841597 succeeded, artifact 15122942468; all 34 frozen official/price-shadow card rows and original summary metrics reproduced, all nine original unified research summary rows matched. Top10 5–5, Playable 10–10 +17.780559u, price shadow 3–1 +1.562096u; blend 5–5, ATG consensus no qualifiers. 14 finalized games. No duplicate prospective ledger appended; review output labeled FROZEN_SOURCE_REVIEW_ONLY. Archived verification manifest. Separate CI run 45832869469 passed 68 tests. Final dated-request and prior-ledger-hash safeguards committed; verification run 45833011900 started, status to verify before claiming final revision tested. No fresh slate has used the new live grading proposal, expanded research grading or incremental daily core yet. Private archive backup and advanced-data permissions remain unresolved. No model/gate promotion, no official historical record changes. Next prioritize archive retention and fresh live end-to-end, rather than further retrospective tuning.

- Final reusable grading verification 45833011900 succeeded; artifact 15124370152, 68 tests passed, same original grades and research summary, four prior ledger hashes recorded. Review manifest updated; no new canonical grade or live-slate evidence.

## 2026-11-26 — frozen archive retention and recovery audit
- Confirmed repository visibility public and original dependency archives still available: team/goalie 15069296241 and skater 15067769899 expire Dec25 2026; ATG bundle 15068418480 and margin bundle 15069647695 expire Feb23 2027. Added original Nov25 core 15073700466, research 15073920102 and grading 15122245729 evidence to inventory. config/frozen_archive_inventory.json pins seven original run/artifact IDs, ZIP digests, source commits, expiration and five essential payload hashes. Extended existing recovery utility via scripts/backup_frozen_archives.py, two tests and docs/FROZEN_RESEARCH_RECOVERY.md; optional authenticated gh CLI downloads exact ZIPs outside public checkout, verifies whole ZIP and critical members, rejects mismatches/overwrite, no unpickling or uploads. Existing member-only verification retained.
- Integrity workflow 45833447775 succeeded, artifact 15123566078, 70 tests passed; all seven original ZIP digests and five pinned payload hashes verified. Temporary runner downloads deleted, only checksum report published; data/model_runs/2026-11-26_frozen_archive_integrity.json committed. No permanent private backup created or confirmed: no authorized private storage destination provided. User given original download run links and recovery instructions. Current public Actions depend on original artifact IDs; after expiry authorized private restoration/execution configuration still needed. No source permissions or commercial use rights established. No new historical data, model fit, grades or predictive changes. Next: confirm private backup before Dec25; verify first expanded prospective slate and investigate advanced data licensing only with approved source rights. Official v0.2.0 remains unchanged.
