# NHL Lessons / Change Log

## v0.1.0 — 2026-09-29 — Initial build

### Rules established
- Separate probability ranking from price/value selection.
- Track Top 10 Probability and Playable Price cohorts independently.
- Train on 2021-22 through 2025-26 and append 2026-27 prospectively.
- Chronological validation only.
- Use role, PP usage, injuries and starting goalies as current-context inputs.

### Hypotheses to test prospectively
- Player role/PP changes will be especially important in October.
- Goalie-save accuracy should improve by modeling expected opponent shot volume separately from goalie save skill.
- Raw scorer/assist probabilities will likely require market-specific calibration because rare events are prone to overconfidence.
- Game-total errors should be checked for shared pace/empty-net correlation rather than assuming independent team goal counts forever.
