# NHL Lessons / Change Log

## v0.1.0 — 2026-09-29 — Initial build

### Rules established
- Separate probability ranking from price/value selection.
- Track Top 10 Probability and Playable Price cohorts independently.
- Train on 2021-22 through 2025-26 and append 2026-27 prospectively.
- Chronological validation only.
- Use role, PP usage, injuries and starting goalies as current-context inputs.

### Opening-day pre-lock QA
- The first dry run exposed a full-team-name vs abbreviation mapping error in game-market candidate resolution.
- Example failure mode: a selection like "Vancouver Canucks +1.5" was not recognized as VAN, so it could be evaluated as the home side.
- The dry run was discarded before any official card was locked.
- Added canonical team-name mapping in `src/wshlx_nhl/team_aliases.py`.
- Re-ran the full slate after the fix, then locked the Top 10 before applying sportsbook prices.
- This is an implementation fix, not a post-result model adjustment, so the version remains v0.1.0.

### Hypotheses to test prospectively
- Player role/PP changes will be especially important in October.
- Goalie-save accuracy should improve by modeling expected opponent shot volume separately from goalie save skill.
- Raw scorer/assist probabilities will likely require market-specific calibration because rare events are prone to overconfidence.
- Game-total errors should be checked for shared pace/empty-net correlation rather than assuming independent team goal counts forever.
