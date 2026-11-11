# Goalie Save Model Promotion — 2026-11-11

## Decision
Promote **goalie v0.2** from shadow to the official goalie-save component. Overall NHL model version becomes **v0.2.0**. Historical locked cards remain unchanged.

## Pre-written promotion criteria
The Oct. 5 rule required:
- at least 20 clean matched FanDuel-listed goalie props;
- better expected-save MAE than v0.1;
- better probability calibration/Brier than v0.1;
- no obvious new directional bias.

## Clean prospective evidence
Matched clean shadow slates used for the promotion decision: Oct. 6, Oct. 9, Nov. 8 and Nov. 9.

| Version | Props | W-L | Hit rate | Saves MAE | Pick Brier |
|---|---:|---:|---:|---:|---:|
| v0.1 | 33 | 15-18 | 45.5% | 5.298 | 0.275 |
| v0.2 | 33 | 19-14 | 57.6% | 4.963 | 0.244 |

v0.2 clears every pre-written criterion.

## v0.3 research experiment
v0.3 added:
- training through the current 2026-27 season;
- 20-game/start rolling shot and save baselines;
- Monte Carlo shots-faced -> save-rate -> saves simulation.

Date-safe diagnostic across seven normalized FanDuel boards:
- all 72 rows: v0.1 35-37, v0.2 36-36, v0.3 37-35;
- clean 40 rows: v0.1 17-23, v0.2 20-20, v0.3 20-20;
- clean MAE: v0.1 5.794, v0.2 5.358, v0.3 5.538;
- clean Brier: v0.1 0.293, v0.2 0.248, v0.3 0.260.

With the existing goalie playable gate (edge >= 4%, EV > 0 in the diagnostic):
- v0.2: 9-6, +1.7342u;
- v0.3: 6-9, -3.6844u.

Conclusion: v0.3 adds complexity without actionable improvement and remains research-only.

## Production behavior from next slate
- scripts/assemble_core_slate.py uses v0.2 goalie probabilities as model_probability.
- v0.1 remains in output for diagnostic comparison.
- The goalie price gate is unchanged.
- Never backfill v0.2 into old official cards.
