# NHL Model Resume Refresh — 2026-11-08

## Status
**COMPLETE.** This is a data/context refresh, not an official model-version change.

Official model remains **v0.1.0**.

## Refreshed current-season sample
As of the Nov. 8 snapshot:
- Completed 2026-27 regular-season games: **276**
- Team-game rows: **552**
- Teams represented: **32**
- Goalies with at least one 2026-27 start: **74**
- Current-roster skaters scored in the snapshot: **717**
- Current-season NHL skater stat rows returned: **727**

The snapshot used completed games available before the 2026-11-09 target cutoff. Games still in progress or not yet played on Nov. 8 were intentionally excluded and will be picked up automatically on the next refresh.

## What already updates with current-season data
### Team/game model
The team-goal hybrid already blends 2025-26 priors with 2026-27 results, so the month of missed games now materially updates:
- team scoring
- team goals allowed
- shots for/against
- last-5 and last-10 form
- rest/current context used on future slates

### Goalie pipeline
Current-season workload tables now include:
- starts
- saves per start
- shots faced per start
- save percentage
- last-five workload/save form
- recent-start count
- rest

Goalie v0.2 remains SHADOW_ONLY. Official goalie v0.1 remains the production comparison.

## Important skater audit
The established-skater official v0.1 path is still primarily anchored to the player's 2025-26 transition-model input. Current 2026-27 production had been affecting fallback/limited-history players much more than established veterans.

Therefore the restart adds:

**SKATER_CURRENT_SEASON_BLEND_SHADOW_V0_2**

It blends the frozen official v0.1 expected rate with actual 2026-27 production using an empirical-Bayes style prior:
- Goal prior weight: 12 games
- Assist prior weight: 10 games
- Point prior weight: 10 games

This shadow does **not** alter Official Top 10 or Official Playable picks yet. It will be tracked prospectively and can only be promoted after sufficient clean evidence.

## Examples of current-season movement
### Strong upward movement in 1+ point probability
- Kent Johnson: 24.6% official -> 52.9% shadow
- Berkly Catton: 23.0% -> 47.2%
- Devon Toews: 29.2% -> 50.1%
- Owen Power: 27.6% -> 48.5%
- Seth Jones: 41.3% -> 60.9%
- Jack Roslovic: 35.6% -> 55.1%
- Auston Matthews: 63.6% -> 73.4%
- Sebastian Aho: 60.8% -> 70.5%

### Strong downward movement
- Conor Garland: 38.1% -> 20.7%
- Alex Ovechkin: 51.4% -> 36.2%
- Oliver Ekman-Larsson: 29.8% -> 15.0%
- Timo Meier: 50.5% -> 36.0%
- Kyle Palmieri: 51.7% -> 37.7%
- Owen Tippett: 43.0% -> 29.3%
- Tom Wilson: 51.9% -> 38.9%

These are diagnostic shadow movements only, not retroactive official changes.

## Team-form snapshot
Notable season scoring rates:
- Edmonton: 4.17 GF/game
- Carolina: 4.11
- Colorado: 4.00
- Boston: 3.76
- Anaheim: 3.76
- Tampa Bay: 3.75

Notable defensive rates:
- Minnesota: 2.26 GA/game
- Boston: 2.35
- Carolina: 2.37
- Dallas: 2.41

Recent last-five scoring leaders in the snapshot:
- Anaheim: 5.4 GF/game
- Carolina: 5.0
- Montreal: 4.6
- Tampa Bay: 4.4
- New Jersey: 4.2
- Florida: 4.2

## Restart rules going forward
1. Keep official v0.1.0 frozen until prospective evidence justifies promotion/change.
2. Use refreshed current-season team and goalie data on every new slate.
3. Track the new current-season skater blend as a separate shadow.
4. Keep Playable Price v0.3 shadow and goalie v0.2 shadow separate from official results.
5. Refresh same-day injuries, scratches, projected lines, PP units, rest and goalie context for participating teams before every lock.
6. Never backfill skipped October dates as if picks had been made.
7. Preserve historical clean records; the refresh does not change past grading.

## Existing clean record remains
- Top 10: **41-28 (59.42%)**
- Official Playable: **32-64 (33.33%)**
- Official Playable P/L: **-32.8209 units**
- Official Playable ROI: **-34.19%**
- Playable v0.3 clean prospective: **0-1, -1.0u**

## Files / code added
- `scripts/build_resume_snapshot.py`
- `scripts/build_current_season_fast_snapshot.py`
- `config/skater_current_season_shadow_v0.2.yaml`
- `data/context/2026-11-08_resume_context.md`
- `.github/workflows/2026-11-08-resume-refresh.yml`
- `.github/workflows/2026-11-08-fast-refresh.yml`

Both Nov. 8 refresh workflows completed successfully.
