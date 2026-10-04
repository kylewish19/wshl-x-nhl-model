# NHL MODEL — CURRENT STATE

Version: **v0.1.0**
Season: **2026-27**
Repository: **kylewish19/wshl-x-nhl-model**
Branch: `main`

## Core workflow / locked rules
- Use only the games the user supplies for the daily slate.
- Refresh current rosters, injuries, projected lines/PP roles, rest/back-to-back context, and starting goalies before the final model run.
- First stage is **odds-blind**: sportsbook thresholds/markets define the candidate universe, but prices cannot influence probabilities or Top 10 ranking.
- Produce exactly **10 highest model-probability eligible bets** across the full available slate: the **Top 10 Probability Card**. No forced game/market diversity.
- Lock the Top 10 before applying FanDuel prices.
- Then apply the **Playable Price Gate** to the full eligible candidate universe, not only the Top 10. The playable card is uncapped.
- Default playable gates: minimum EV 5%; edge thresholds ML/spread/total 3%, anytime goal 5%, assist 4%, goalie saves 4%, 1+ point 4%, 2+ point 5%.
- Grade Top 10 and Playable Price separately after each slate. Track W-L, hit rate and Brier/calibration; Playable also tracks 1u flat profit/ROI.
- Structural model/code changes happen only when repeated prospective evidence justifies them, except implementation/data bugs and normalization fixes which may be corrected pre-lock. Never rewrite historical locked picks.
- Same-player / same-team correlations are diagnostic issues; pure Top 10 ranking remains based on marginal probability unless a future documented rule changes it.
- Goalie-save props are official only when the expected starter is sufficiently confirmed.
- If a slate is finalized after puck drop, it must be tagged **LATE_LOCK** and kept out of the clean prospective cumulative record.
- Skipped dates stay skipped; never create retroactive official cards.

## Modeling state
- v0.1.0 opening-season bootstrap is still active; no structural predictive change yet.
- Training seasons: **2021-22 through 2025-26**.
- Skater season-transition sample: **2,594 rows**, chronological latest validation **640 rows**.
- Selected Ridge transition models: goal/game alpha 10 (validation MAE ~0.0574), assist/game alpha 0.3 (~0.0761), point/game alpha 0.3 (~0.1125).
- Team/game markets use the current team-goal Poisson hybrid plus opening-season strength context.
- Player goal/assist/point thresholds are generated from count-rate models with probability transforms.
- Goalie-save model is separate and remains a watchlist because workload/shot-volume calibration has been weak early.
- Known limitations: opening-season role changes, rookie/limited-history fallback, independent team-goal structure, current lineup/goalie uncertainty, raw implied-probability edge rather than full no-vig price normalization.

## Player-name normalization fixes already in repo
`src/wshlx_nhl/player_aliases.py` includes:
- Mitchell Marner -> Mitch Marner
- Alexis Lafreniere -> Alexis Lafrenière
- Joe Veleno -> Joseph Veleno
- Michael Brandsegg-Nygard -> Michael Brandsegg-Nygård
- Maxim Tsyplakov -> Maksim Tsyplakov
- Frederick Gaudreau -> Freddy Gaudreau

These are data/identity fixes, not predictive-model changes.

## Clean prospective grading through 2026-10-02
### 2026-09-29
- Top 10: **7-3**, Brier **0.2080**, expected wins **7.6003**.
- Playable: **7-10**, **-0.9502u**, **-5.59% ROI**, Brier **0.2586**.

### 2026-09-30
- Top 10: **6-4**, Brier **0.2135**, expected wins **6.8778**.
- Playable: **6-4**, **+1.2905u**, **+12.90% ROI**, Brier **0.1824**.

### 2026-10-01
- **Skipped intentionally.** No retroactive picks.

### 2026-10-02
- Top 10: **7-3**, Brier **0.2017**, expected wins **7.1457**.
- Playable: **6-2**, **+4.4427u**, **+55.53% ROI**, Brier **0.2068**.

### CLEAN CUMULATIVE through Oct. 2
- **Top 10: 20-10 (66.67%)**, expected wins **21.6238**, Brier **0.2077**.
- **Playable Price: 19-16 (54.29%)**, **+4.7830u**, **+13.67% ROI**, Brier **0.2250**.

## Oct. 3 — LATE LOCK (separate from clean record)
The final run occurred after some puck drops, but it used only frozen pregame screenshots and no live data. It is graded separately and does **not** change clean cumulative totals.
- Late-lock Top 10: **6-4**, expected wins **7.6161**, Brier **0.2563**.
- Late-lock Playable: **12-21**, **+6.4177u**, **+19.45% ROI**, Brier **0.2836**.
- Profit was driven by a few plus-money hits (not improved calibration), especially Kiefer Sherwood ATG +700 and Victor Eklund 2+ points +800.
- Victor Eklund correlated fallback props went 3-0; Porter Martone correlated props went 0-4. Treat these as same-player clusters, not seven independent calibration observations.
- No structural code change from Oct. 3.

## Current watchlists / lessons
- **Goalie saves:** clean playable cohort had reached 3-5 through Oct. 2; continue monitoring expected opponent shot volume, workload and game script before changing model.
- **Rookie / limited-history fallback:** early record volatile/weak; keep tagged separately and do not give same trust as established transition-model players.
- **Low-probability/high-EV longshots:** early clean cohort had been 0-3 through Oct. 2, while Oct. 3 late-lock produced big longshot wins. Do not loosen/tighten globally from a small, high-variance sample.
- **Top-10 puck lines:** clean cohort was **8-0 through Oct. 2**; promising but too small to increase weighting.
- **Correlation:** same-team and same-player concentration can create clusters of wins/losses. Add/retain reporting diagnostics, but do not distort the pure-probability Top 10.
- No structural predictive-model update yet; **v0.1.0 remains active**.

## CURRENT SLATE — 2026-10-04
Original slate had 5 games:
1. WPG @ DET — 1:00 PM
2. UTA @ NYR — 6:00 PM
3. CGY @ SEA — 8:00 PM
4. FLA @ ANA — 8:00 PM
5. VGK @ VAN — 9:00 PM

WPG@DET was already underway before the complete later-board run, so it was **excluded entirely** rather than mixing post-puck-drop/incomplete candidates. The official clean prospective Oct. 4 card covers the remaining four games.

FanDuel odds files saved:
- `data/odds/2026-10-04_UTA-NYR_FanDuel.csv`
- `data/odds/2026-10-04_CGY-SEA_FanDuel.csv`
- `data/odds/2026-10-04_FLA-ANA_FanDuel.csv`
- `data/odds/2026-10-04_VGK-VAN_FanDuel.csv`

### Oct. 4 Official Top 10 Probability Card — LOCKED
File: `data/picks/2026-10-04_top10_probability.csv`
1. Utah Mammoth +1.5 — **75.09%**
2. Jack Eichel 1+ point — **74.38%**
3. Anaheim Ducks +1.5 — **73.84%**
4. Calgary Flames +1.5 — **70.06%**
5. Mark Stone 1+ point — **64.91%**
6. Clayton Keller 1+ point — **63.73%**
7. Matthew Tkachuk 1+ point — **63.36%**
8. Vancouver Canucks +1.5 — **62.89%**
9. CGY-SEA Over 5.5 — **62.51%**
10. Sam Reinhart 1+ point — **62.29%**

Top-10 expected wins = **6.7306**. This is an honest calibration expectation, not a target; the objective is still to get as many of the 10 correct as possible.

### Oct. 4 Official Playable Price Card — currently locked without goalie saves
File: `data/picks/2026-10-04_playable_price.csv`
1. Tristan Luneau anytime goal +950 — model 17.85%, limited-history fallback
2. Vancouver ML +230 — 39.51%
3. Vancouver +1.5 -108 — 62.89%
4. CGY-SEA Over 5.5 -120 — 62.51%
5. Anaheim ML +114 — 51.52%
6. UTA-NYR Over 5.5 -120 — 58.93%
7. Utah ML +105 — 52.37%
8. Calgary ML +130 — 46.62%
9. Anaheim +1.5 -225 — 73.84%
10. Utah +1.5 -245 — 75.09%

Run metadata: `data/model_runs/2026-10-04_v0.1.0.json`
- Top 10 was locked before included games started.
- Odds were not used in probability ranking.
- Goalie-save props were **not included yet** because the user asked to run before sending them.
- User plans to send goalie-save odds later. Treat those as a **goalie supplement**: they may create additional Playable Price bets, but they must **not replace or rewrite the already locked Top 10**.
- Curtis Douglas was excluded as scratched.
- Current lineup/rest checks were performed before lock.

## Exact next task in a new chat
Continue from the Oct. 4 locked state. The user may next send **goalie-save FanDuel odds** for the four remaining games. Verify starters/eligibility, run the goalie-save model, and add any qualifying goalie-save bets to an Oct. 4 supplemental/expanded Playable Price card without altering the locked Top 10. After the games finish, grade Oct. 4 Top 10 and Playable cohorts, update cumulative clean records, log lessons, and make code changes only if repeated evidence supports them.
