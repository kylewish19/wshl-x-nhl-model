# Unified daily shadow grading and ledger

Official NHL v0.2.0 cards and results are independent of this research.

## Pregame
Use the successful official core workflow artifact as input to Unified Daily NHL Shadows. The official artifact and the unified artifact must both be uploaded before first puck. A retrospective or late run is never eligible for clean grading.

## Postgame
Dispatch Unified NHL Shadow Grading with the unified source run ID, Eastern slate date, and authorized finalized game-level team, explicit starting-goalie and skater parquets. Input history must contain all matched games with exact player IDs and completed scores. Do not use a projected lineup or a partially completed game. Live source paths require separately reviewed provenance; the grader checks coverage and consistency, not whether an external provider is licensed or its scores independently correct.

For live grading always supply the current canonical ledger, data/results/prospective_shadow_ledger.csv, via the ledger input. The workflow produces an updated ledger and cumulative summary as artifacts; it does not have write permission and does not automatically commit results. Before committing the replacement, review the source run, timestamp chain, outcome provenance, hashes, and previous ledger rows, and confirm no concurrent updates were lost. Never replace an existing clean ledger with a fresh empty one.

Probability metrics: one Over probability per total or goalie line, one ATG probability per eligible settled player; DNP/nonstarter voids excluded. Paper selections use frozen flags and one unit per selection; ROI denominator is settled wagers. Goalie grade requires an explicit starting flag. Cumulative Brier/log loss are observation-weighted; do not average daily AUCs or report an independent sample size when lines or players share games.

Promotion requires genuinely prospective evidence; a successful replay is only an integration check. Current-season archive and frozen model artifact expiry remain unresolved. No full advanced data collection or redistribution without suitable rights.
