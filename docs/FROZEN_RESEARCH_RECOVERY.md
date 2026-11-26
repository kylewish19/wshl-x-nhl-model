# Frozen NHL archive recovery — updated 2026-11-26

The public repository contains code, derived reports and provenance, not a permanent private copy of the raw historical archives or fitted bundles. The canonical inventory is config/frozen_archive_inventory.json. It pins the original run, artifact ID, source commit, ZIP SHA-256, expiry and critical payload SHA-256 values. All seven listed artifacts were confirmed available on 2026-11-26. Download before expiration and keep in private storage you control; permissions and data-use rights still apply.

| Archive | Run | Artifact ID | Expires UTC |
|---|---:|---:|---|
| nhl-resume-refresh-2026-11-24 | 45713367700 | 15069296241 | 2026-12-25 22:31:56 |
| atg-game-shadow-2026-11-25 | 45713698148 | 15067769899 | 2026-12-25 22:32:38 |
| atg-archive-audit-2026-11-25 | 45714769216 | 15068418480 | 2027-02-23 22:37:07 |
| team-market-shadow-2026-11-25 | 45716648252 | 15069647695 | 2027-02-23 22:50:52 |
| nhl-core-slate-2026-11-25 | 45723015990 | 15073700466 | 2027-02-23 23:39:18 |
| unified-daily-shadows-2026-11-25 | 45723215283 | 15073920102 | 2027-02-23 23:40:55 |
| nov25-frozen-grading | 45828937854 | 15122245729 | 2027-02-24 13:25:04 |

## Private backup
Save original ZIP downloads from their Actions runs while signed in, retaining the original artifact names with .zip extension. Prefer two independent private copies (e.g. encrypted local drive and permitted private backup). Do not put the archives inside the public checkout or share a public link. Do not modify/recompress ZIPs. If Python and authenticated GitHub CLI are installed, from the current checkout run:

```powershell
python scripts/backup_frozen_archives.py --directory "$HOME\Documents\WSHL_X_NHL_Private_Backup" --download
```

Without the CLI, download the original ZIPs manually, then run the same command without --download. The script checks complete ZIP digests, five critical member digests, refuses mismatching existing files and does not overwrite or upload data. The earlier verify_research_backup.py remains available for member-only checking of the original three archives. Verification of the live originals in an ephemeral Actions runner is not a permanent backup. A confirmed private copy requires a successful local verification report; do not claim the backup is complete without one.

## Recovery
Retain the inventory, repository history/source commits, frozen dependency configuration and verified archive ZIPs. Verify original ZIPs again before recovery; only unpack verified trusted archives into a private working directory and only load trusted joblib files. Use the original archive contents with the existing reusable runner --archive and unified research --history/--bundle/--team-history/--margin-bundle options, together with the original artifact metadata for historical grading. Reuse exact source and cutoff provenance. A restored ZIP or copied artifact is not a new pregame lock; retain the original artifact IDs and original upload timestamps. Public Actions workflows still reference original artifact runs; after expiry they require an authorized private execution/storage configuration rather than uploading raw archives publicly. No automatic private cloud recovery has been configured.

Archive hashes do not establish completeness or data-use rights. No advanced-data bulk collection, commercial licensing or redistribution is implied. Refreshing historical data can change hashes; a rebuilt archive or model must be versioned separately unless exact identity is demonstrated. Add each future clean slate's original core/research/grading artifacts to the private archive before expiry; this inventory covers the four foundational dependencies and Nov25 originals only.
