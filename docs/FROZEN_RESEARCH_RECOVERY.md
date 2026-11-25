# Frozen research recovery — 2026-11-25

Save the three original ZIPs to private storage you control before their expiry. This project has a public main branch; do not commit the raw datasets or joblib binaries there. Original artifacts are still hosted by GitHub; this procedure is not itself a completed private backup.

| Archive | Workflow run | Artifact ID | Expires UTC |
|---|---:|---:|---|
| atg-game-shadow-2026-11-25 | 45713698148 | 15067769899 | 2026-12-25 22:32:38 |
| atg-archive-audit-2026-11-25 | 45714769216 | 15068418480 | 2027-02-23 22:37:07 |
| nhl-resume-refresh-2026-11-24 | 45713367700 | 15069296241 | 2026-12-25 22:31:56 |

Download from the corresponding GitHub Actions run while signed in. Keep the ZIPs and source commit/configuration together. Verify original payloads with:

```sh
python scripts/verify_research_backup.py --history /private/atg-game-shadow-2026-11-25.zip --bundle /private/atg-archive-audit-2026-11-25.zip --team-goalie /private/nhl-resume-refresh-2026-11-24.zip
```

The script compares four original file SHA-256 checksums recorded in the frozen config and grading manifest. It does not unpickle models or extract arbitrary archive paths. A successful check confirms exact payload copies, not data completeness or data-use rights. Preserve the Python and dependency versions in the frozen configuration. Only load trusted model bundles.

Recovery after expiry: use the original verified bytes in an authorized private execution environment. The current unified GitHub workflows still reference the original artifact runs, so their artifact-source settings must be updated if the originals expire. Do not treat a newly fetched archive or retrained model as identical unless verified. No advanced bulk data collection or public redistribution is authorized by this procedure.
