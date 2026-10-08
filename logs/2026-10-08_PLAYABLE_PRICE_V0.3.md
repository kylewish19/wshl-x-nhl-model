# 2026-10-08 — Playable Price shadow v0.3

## Why a new shadow is justified

The official probability engine remains v0.1.0 and the Top 10 is not being changed. Through the clean Oct. 6 slate, the Top 10 is 37-22 on settled bets (62.71%), while the Official Playable Price cohort is 31-61 (33.70%), -30.5785 units and -33.24% ROI. Oct. 6 itself was Top 10 7-3 versus Playable 6-14.

The first Playable selection shadow v0.2 helped on Oct. 6 by removing four official plays; all four excluded bets lost. That improved the counterfactual night from -9.4475u to -5.4475u, but the remaining filtered card was still poor. One prospective slate is not promotion evidence; it is enough to justify testing a stronger challenger.

## v0.3 design

Playable Price shadow v0.3 keeps raw v0.1.0 probabilities intact and remains shadow-only. It adds a reliability/selection layer after the probability stage:

1. Build a market-specific one-sided reliability factor from clean settled Official Playable rows strictly before the target slate.
2. The reliability factor may shrink a raw probability when a market has underperformed its own forecasts; it can never increase the probability because the graded Playable sample is selected rather than a full calibration universe.
3. Quarantine all limited-history/rookie fallback projections.
4. Temporarily quarantine all anytime-goal wagers while that market is rebuilt/calibrated.
5. Require market-specific absolute probability floors.
6. Apply the same official edge and 5% EV thresholds, but to the reliability-adjusted probability.
7. Allow only one executable shadow wager per substantially correlated player/team/goalie cluster. Within a cluster, prefer the highest calibrated hit probability, with calibrated EV as the tie-break.

## Initial v0.3 floors

- Moneyline: no absolute probability floor; plus-money underdogs can remain eligible.
- Spread: 55%
- Total: 55%
- Anytime goal: quarantined
- Anytime assist: 50%
- Goalie saves: 58%
- 1+ point: 55%
- 2+ points: 45%

These are shadow rules, not official changes. They will be judged prospectively rather than optimized to rewrite prior cards.

## Promotion rule

The Official Playable Price card remains the control. Do not promote v0.3 until it has at least 20 new clean independent decisions (preferably 20-30+), better prospective calibration/Brier and flat-stake ROI, and no material damage to stronger markets. Same-player correlated bets count as one diagnostic cluster when judging independence.

Goalie v0.2 also remains a separate shadow and is not promoted by this change.
