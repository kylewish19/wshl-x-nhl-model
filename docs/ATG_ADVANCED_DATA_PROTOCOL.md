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

## 2026-11-26 source rights and offline prototype
Reviewed provider pages on 2026-11-26:
- https://www.moneypuck.com/data.htm : noncommercial/ad-hoc journalist scope, attribution; contact for other purposes. Recent 2021-25 shot archive is advertised as 605,110 events; historical availability is not verified complete coverage for our chosen games.
- https://www.nhl.com/info/terms-of-service and https://www.nhl.com/news/nhl-edge-advanced-stats-section-brings-fans-closer-to-game : NHL EDGE tracking data exists; no confirmed bulk/commercial permission.
- https://puckapi.com/docs/timing-and-rights and https://puckapi.com/pricing : provider states model training, backtesting, commercial derived outputs permitted while account open, internal retained-data use after cancellation; raw redistribution prohibited and no league rights granted. Free, Starter $19/mo, Pro $49/mo advertised. No pregame confirmed starter feed; revised records replace older versions; strict before-scheduled-start filter required on any future historical prop study. Confirm full terms, training/retention rights, upstream rights, exact FanDuel coverage, costs and data fields before account activation or ingestion. Do not substitute non-FanDuel prices.
- https://onice.dev/data/ and https://onice.dev/terms/ : noncommercial CSVs, commercial API plan required; evaluate actual plan and dated game-level availability.
- https://developer.sportradar.com/ice-hockey/reference/nhl-overview : official-data commercial option; obtain written plan/rights/coverage.

Existing 18-game source probe (data/results/2026-11-25_atg_advanced_source_coverage.csv) has no missing shooter, geometry, strength or goalie presence and one missing shot-type event. Both PP reports returned 36 rows per sample game; explicit complete participant matching and units must still be verified. No new data downloaded. No provider subscribed or approved. A successful public endpoint response does not establish permitted use.

Added src/wshlx_nhl/advanced_shot_research.py: offline only, normalized synthetic/authorized data. Explicit defended ordinary unblocked attempts; caller must exclude blocked shots and shootouts and identify penalty shots/empty nets. Fit fixed logistic xG on strictly earlier dates per interval, using geometry, strength and shot type only. No test labels in fit; earliest warm-up unscored. Aggregate only independently reconciled complete games, exact PP participation matching, no missing PP treated as zero. A 0.20 xG danger threshold is a project proxy, not provider-defined high-danger metric; no promotion or threshold tuning. PP and shot-quality rolling features strictly lagged by player with valid-count indicators. No same-day features. Three synthetic tests; no real-data performance claim. Next: source-specific authorized normalized data adapter, independently reconcile counts and PP units, then chronological evaluation on common rows, before any live use. No actual xG model bundle trained on real data.
