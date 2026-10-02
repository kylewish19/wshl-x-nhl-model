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

## 2026-09-29 — Opening-night grading

### Results
- Top 10 Probability Card: 7-3 (70.0%). Model probabilities summed to 7.600 expected wins; Brier score 0.2080.
- Playable Price Card: 7-10 (41.2%), -0.9502 units at 1u flat staking, -5.59% ROI. Model probabilities summed to 8.911 expected wins; Brier score 0.2586.

### Market notes
- Top-10 point/assist props: 4-2 (McDavid 1+ point W; Draisaitl 1+ point W; McDavid 1+ assist W; Eichel 1+ point W; Pastrnak 1+ point L; Suzuki 1+ point L).
- Top-10 puck-line picks: 2-0 (Boston +1.5; Toronto +1.5).
- Top-10 goalie saves: 1-1 (Hart O20.5 W; Jarry O20.5 L).
- Playable goalie-save picks: 2-4. Hart over and Bobrovsky under won; Jarry over, Bussi over, Lankinen under and Shesterkin over lost.
- Playable moneylines: 2-1 (Vancouver W, Boston W, Chicago L).
- Playable spreads: 1-1 (Vancouver +1.5 W, Chicago +1.5 L).
- Rookie projection fallback: Anton Frondell 1+ assist and 1+ point both lost (0-2). Keep this cohort explicitly tagged and separate while sample size grows.

### Lessons / actions
- Do not alter the core Top-10 model after one slate; 7-3 is a healthy start and the calibration sample is far too small for structural conclusions.
- Watch goalie-save calibration closely. The playable save cohort started 2-4, with large misses on Jarry (17 vs O20.5), Lankinen (32 vs U27.5), and Shesterkin (20 vs O23.5). Prioritize opponent shot-volume / game-script diagnostics during the next several slates.
- The opening-day price gate was more aggressive than the pure probability card. Track whether longshot EV and lower-probability value candidates remain overconfident before changing thresholds.
- Do not promote rookie-fallback probabilities to the same trust level as veteran transition-model probabilities until we have a meaningful prospective sample.
- No post-result code changes are made from this slate alone. Continue collecting evidence and change code only when a repeatable error pattern appears.

## 2026-09-30 — Slate 2 grading

### Results
- Top 10 Probability Card: 6-4 (60.0%). Model probabilities summed to 6.8778 expected wins; Brier score 0.2135.
- Official Playable Price Card: 6-4 (60.0%), +1.2905 units at 1u flat staking, +12.90% ROI; Brier score 0.1824.
- Cumulative Top 10: 13-7 (65.0%) through two slates.
- Cumulative Playable Price: 13-14 (48.15%), +0.3403u, +1.26% ROI through 27 plays.

### Market notes
- Top-10 puck lines improved to 4-0 cumulatively after NYI +1.5 and PIT +1.5 both won on Slate 2. Keep sample-size caution.
- Top-10 skater point props went 3-3 on Slate 2: MacKinnon, Necas and Panarin won; Nylander, Matthews and Martone lost.
- MacKinnon 1+ assist lost despite a two-goal night (2 G, 0 A), a useful reminder that point and assist markets should remain separately calibrated.
- Playable goalie saves went 1-0 on Slate 2 with Blackwood O23.5 (27 saves), improving the cumulative playable saves cohort to 3-4.
- Blueger anytime goal at +1100 has now qualified twice and lost twice. Continue tracking low-probability/high-EV longshots as a separate calibration band before changing the gate.
- Rookie/projection fallback now has another miss with Porter Martone 1+ point; combined early fallback examples remain weak. Continue tagging and consider a stricter gate if this persists over a larger sample.
- Playable spreads went 2-0, PIT ML won, NYI ML lost, and LAK-COL U6.5 lost badly in an 8-4 game.

### Lessons / actions
- No structural v0.1.0 code change yet. Two slates are still too small, and the playable card rebounded from -5.59% ROI on Slate 1 to +12.90% on Slate 2, leaving the cumulative price card slightly positive.
- Preserve the current Top-10 ranking process; 13-7 (65%) is an acceptable early baseline but not enough to claim calibration is solved.
- Keep three watchlists: goalie-save volume, rookie/fallback props, and low-probability/high-EV longshots.
- If rookie/fallback or longshot EV cohorts continue underperforming over several more slates, test a higher minimum edge/EV gate for those cohorts rather than changing the veteran model globally.
- Continue tracking puck-line performance separately; 4-0 is promising but far too small for a weight increase.
