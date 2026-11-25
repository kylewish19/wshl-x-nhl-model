# Advanced ATG data research protocol — 2026-11-25

Status: RESEARCH ONLY. Official NHL v0.2.0 and both frozen ATG challengers remain unchanged.

## Sources and permitted scope
- NHL GameCenter play-by-play: https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play. Probe historical shot coordinates, event owner, shooter, strength, goalie presence and shot type.
- NHL Stats REST: https://api.nhle.com/stats/rest/en/skater/timeonice and /powerplay. Probe game-level reports and check whether actual PP ice time is provided, including zero-usage skaters. A report with PP participants only cannot imply missing=zero until verified.
- MoneyPuck: https://moneypuck.com/data.htm. Published free-use terms are noncommercial and ad-hoc journalist use, with attribution. Do not ingest or redistribute for a potentially commercial WSHL_X product without appropriate permission. NHL data use terms also require review before any commercial deployment or redistribution.

## Source audit
Deterministically sample first, middle, last archived game in each of six seasons (18 games). Inspect schema and report missing IDs, geometry, strength and goalie state; validate matches to frozen skater archive. Do not interpret successful HTTP response as complete data. This is a feasibility sample, not full historical coverage.

## Candidate independent xG model
If the audit supports full collection and permitted use:
1. Build one row per unblocked attempt (goal, shot-on-goal, missed-shot). Omit shootouts; exclude blocked attempts because block coordinates are not shot-release coordinates. Explicitly handle penalty shots and empty nets; do not conflate them with ordinary defended-net shots. Retain missing-event counts by season.
2. Orient shot coordinates using recorded defending side and event owner. Derive shot distance and angle; use pre-release context such as shot type, strength and elapsed time. No on-target flag, final goal outcome, saves, or post-shot information as inputs.
3. Chronological fitting and calibration: use only earlier seasons to generate xG for later seasons. Cross-fit xG estimates for any downstream ATG training row; don't compute training xG with an event model trained on that row's goal label. Report calibration/Brier/log loss at event level.
4. Aggregate player-game xG, high-danger/unblocked attempts and power-play usage; join by game and player ID and shift by one game. Same-day game outcomes and realized PP TOI cannot enter pregame features.
5. Compare against unchanged shot/finish and calibrated boosting baselines on common eligible rows. Previously viewed 2025-26 and 2026-27 through Nov 24 are development diagnostics, not untouched final validation. Freeze experimental configuration before new prospective dates. No official promotion until matched prospective evidence supports it.

## Lineup context
Projected lines, PP units and starter announcements require timestamped pregame records. Do not infer historical projected lineups from postgame actual shifts. Use lagged actual usage as a distinct feature, not as a confirmed next-game assignment.

## Stop conditions
Unexplained identity or shot geometry errors, insufficient season coverage, missing timestamps, or unavailable rights block deployment. Report missingness and keep existing official and shadow forecasts separate.
