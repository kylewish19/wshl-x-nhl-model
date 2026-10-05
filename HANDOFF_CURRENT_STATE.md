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
- **v0.1.0 remains active. No structural predictive change through Oct. 4.**
- Training seasons: **2021-22 through 2025-26** plus current 2026-27 context prospectively.
- Skater season-transition sample: **2,594 rows**, chronological latest validation **640 rows**.
- Selected Ridge transition models: goal/game alpha 10 (validation MAE ~0.0574), assist/game alpha 0.3 (~0.0761), point/game alpha 0.3 (~0.1125).
- Team/game markets use the current team-goal Poisson hybrid plus opening-season strength context.
- Player goal/assist/point thresholds are generated from count-rate models with probability transforms.
- Goalie-save model remains a watchlist because workload/shot-volume calibration has been weak early.
- Known limitations: opening-season role changes, rookie/limited-history fallback, independent team-goal structure, lineup/goalie uncertainty, raw implied-probability edge rather than full no-vig price normalization.

## Player-name normalization fixes already in repo
`src/wshlx_nhl/player_aliases.py` includes:
- Mitchell Marner -> Mitch Marner
- Alexis Lafreniere -> Alexis Lafrenière
- Joe Veleno -> Joseph Veleno
- Michael Brandsegg-Nygard -> Michael Brandsegg-Nygård
- Maxim Tsyplakov -> Maksim Tsyplakov
- Frederick Gaudreau -> Freddy Gaudreau

These are data/identity fixes, not predictive-model changes.

## Clean prospective grading through 2026-10-04
### Daily results
- **2026-09-29:** Top 10 7-3, Brier 0.2080. Playable 7-10, -0.9502u, -5.59% ROI, Brier 0.2586.
- **2026-09-30:** Top 10 6-4, Brier 0.2135. Playable 6-4, +1.2905u, +12.90% ROI, Brier 0.1824.
- **2026-10-01:** skipped intentionally; no retroactive picks.
- **2026-10-02:** Top 10 7-3, Brier 0.2017. Playable 6-2, +4.4427u, +55.53% ROI, Brier 0.2068.
- **2026-10-04:** Top 10 **7-3**, expected wins **6.7306**, Brier **0.2244**. Playable **5-5**, **-0.8231u**, **-8.23% ROI**, Brier **0.1994**.

### CLEAN CUMULATIVE through Oct. 4
- **Top 10: 27-13 (67.50%)**, expected wins **28.3544**, Brier **0.2119**.
- **Playable Price: 24-21 (53.33%)**, expected wins **23.8740**, **+3.9599u**, **+8.80% ROI**, Brier **0.2193**.

## Oct. 3 — LATE LOCK (separate from clean record)
Oct. 3 remains excluded from clean cumulative totals.
- Late-lock Top 10: **6-4**, expected wins **7.6161**, Brier **0.2563**.
- Late-lock Playable: **12-21**, **+6.4177u**, **+19.45% ROI**, Brier **0.2836**.
- Profit was driven by a few plus-money hits, especially Kiefer Sherwood ATG +700 and Victor Eklund 2+ points +800; do not interpret the profit as improved calibration.

## Oct. 4 grading details
Official Top 10 went **7-3**:
- Wins: Jack Eichel 1+ point, Anaheim +1.5, Mark Stone 1+ point, Clayton Keller 1+ point, Matthew Tkachuk 1+ point, Vancouver +1.5, CGY-SEA Over 5.5.
- Losses: Utah +1.5, Calgary +1.5, Sam Reinhart 1+ point.
- Clean Top-10 puck-line cohort is now **10-2** after going 2-2 on Oct. 4.
- Top-10 1+ point props went **4-1** on Oct. 4.

Official Playable Price went **5-5, -0.8231u**:
- Wins: Vancouver +1.5, CGY-SEA Over 5.5, Anaheim ML, UTA-NYR Over 5.5, Anaheim +1.5.
- Losses: Tristan Luneau ATG +950, Vancouver ML, Utah ML, Calgary ML, Utah +1.5.
- Moneylines were 1-3; spreads 2-1; totals 2-0.
- The later goalie-save board was analyzed, but no goalie save was added to the official locked Playable Price Card before puck drop, so Oct. 4's official playable cohort remains the original 10.

## Current watchlists / lessons
- **Goalie saves:** clean official playable cohort remains **3-5 through Oct. 2** because no Oct. 4 goalie save became official. Continue monitoring expected opponent shot volume, workload and game script.
- **Rookie / limited-history fallback:** still volatile/weak. Tristan Luneau ATG +950 lost on Oct. 4. Keep tagged separately and do not give equal trust to established transition-model players.
- **Low-probability/high-EV anytime goals:** clean cohort is now **0-4** across Teddy Blueger twice, Boone Jenner and Tristan Luneau. Escalate for review, but do not change the gate yet; the sample is still small and low-base-rate.
- **Top-10 puck lines:** clean cohort is **10-2**. Promising, but do not increase weighting or change pure probability ranking yet.
- **Moneylines:** Oct. 4 playable ML went 1-3, but cumulative evidence is still too mixed/small for a market-specific code change.
- **Correlation:** same-team and same-game concentration can create clustered wins/losses. Keep reporting diagnostics; do not distort the pure-probability Top 10.
- **No structural predictive-model update yet; v0.1.0 remains active.**

## 10-Day NHL Ladder Challenge
Separate workflow documented in `LADDER_CHALLENGE.md`; it does not alter Top 10 or Playable Price tracking.
- Challenge ID: **2026-10-A**
- Day 1 (Oct. 4): **Vancouver Canucks +1.5 -108**, model probability 62.89%, model fair odds ~-169.
- Result: **WIN** (Vancouver lost 3-2, so +1.5 covered).
- Challenge advances to **Day 2** on the next eligible slate.

## Repo files updated for Oct. 4 grading
- `data/results/2026-10-04_top10_graded.csv`
- `data/results/2026-10-04_playable_graded.csv`
- `data/results/2026-10-04_summary.csv`
- `data/results/season_summary.csv`
- `data/results/ladder_summary.csv`
- `logs/LESSONS.md`

## Next task
For the next supplied NHL slate, continue with v0.1.0 and the same clean workflow: refresh current context, run probabilities odds-blind, lock exactly 10 Top-Probability picks, apply FanDuel prices to the full universe for the Playable Price Card, and separately select Ladder Challenge Day 2 from the strongest model-supported ticket priced between -120 and +100.
