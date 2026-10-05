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

## 2026-10-02 — Slate 3 grading

### Results
- Top 10 Probability Card: 7-3 (70.0%). Model probabilities summed to 7.1457 expected wins; Brier score 0.2017.
- Official Playable Price Card: 6-2 (75.0%), +4.4427 units at 1u flat staking, +55.53% ROI; Brier score 0.2068.
- Cumulative Top 10: 20-10 (66.67%) through three tracked slates.
- Cumulative Playable Price: 19-16 (54.29%), +4.7830u, +13.67% ROI through 35 tracked plays.

### Market notes
- Top-10 puck-line picks went 4-0 on Slate 3 (BOS +1.5, NYR +1.5, WSH +1.5, ANA +1.5), moving the tracked Top-10 puck-line cohort to 8-0.
- Top-10 1+ point props went 3-3: Eichel, Pastrnak and Kyle Connor won; Robertson, Rantanen and Scheifele lost.
- Dallas was shut out 4-0, creating correlated misses on Robertson and Rantanen. Continue tracking same-team correlation inside the Top 10 even though probability ranking remains pure.
- Playable goalie saves fell to 3-5 cumulatively after Oettinger O21.5 lost with 20 saves. Goalie workload remains a priority watchlist.
- Low-probability/high-EV anytime-goal plays are now 0-3 across Blueger twice and Boone Jenner once. Keep this band separately calibrated before changing the full playable gate.
- The broader Playable Price Card performed very well on Slate 3 and is now +4.7830u cumulatively, so there is no evidence for globally tightening the value gate at this point.
- Pastrnak's markets were internally consistent this slate: 2+ points and 1+ assist both won on two assists.

### Lessons / actions
- No structural predictive-code change from game results yet. Three slates remain a small prospective sample, and both official cohorts are currently positive/healthy enough to avoid reactive overfitting.
- Continue the current v0.1.0 probability model.
- Maintain separate watchlists for goalie saves, rookie/fallback props, and model probabilities below 20% that qualify on large price edges.
- Add same-team / same-game concentration diagnostics to grading reports so correlated misses can be distinguished from independent model errors. This is a reporting/diagnostic enhancement, not a change to which Top-10 bets are selected.
- Do not increase puck-line weights despite the 8-0 start; retain pure probability ranking until a much larger sample exists.

## 2026-10-03 — Late-lock grading (excluded from clean prospective cumulative record)

### Results
- Top 10 Probability Card: 6-4 (60.0%). Model probabilities summed to 7.6161 expected wins; Brier score 0.2563.
- Playable Price Card: 12-21 (36.36%), +6.4177 units at 1u flat staking, +19.45% ROI; Brier score 0.2836.
- This slate remains tagged LATE_LOCK because the final model run occurred after some scheduled puck drops. Only pregame screenshots were used; no live scores, in-game odds, live stats, or outcomes were used to generate the cards.
- Clean prospective cumulative totals remain unchanged at Top 10 20-10 (66.67%) and Playable Price 19-16, +4.7830u (+13.67% ROI).

### Market notes
- Top-10 puck lines went 4-2: OTT +1.5, NYI +1.5, LAK +1.5 and PIT +1.5 won; CGY +1.5 and CBJ +1.5 lost. The clean tracked Top-10 puck-line streak remains separate because this slate is late-lock.
- Top-10 1+ point props went 2-2: MacKinnon and Kucherov won; Jack Hughes and Pastrnak lost.
- Playable moneylines went 2-5 and playable spreads went 3-5. Game-side value was the weak area of the late-lock card.
- Playable anytime goals went 1-2, but Kiefer Sherwood +700 produced +7u and made the market profitable despite the losing record.
- Playable 2+ point props went 1-3, with Victor Eklund +800 producing +8u.
- Assists went 3-3; 1+ point props went 2-2; SEA-EDM Over 6.5 lost.
- Limited-history/fallback props were highly correlated by player: Victor Eklund went 3-0 across 1+ point, 2+ points and assist, while Porter Martone went 0-4 across goal/point/assist markets. Do not treat seven correlated bets as seven independent calibration observations.

### Lessons / actions
- No predictive-code change from this slate. The card was late-lock and therefore is lower-quality evidence for prospective model evaluation even though the inputs were frozen pregame.
- Add/retain a process rule: any slate not fully locked before the first puck drop is graded in a separate LATE_LOCK cohort and excluded from the clean prospective season record.
- Positive ROI (+6.42u) came from a few large plus-money hits while the card was only 12-21 and had a weak 0.2836 Brier score. Do not interpret the profit as evidence that probability calibration improved.
- Continue monitoring same-player concentration. Eklund's three correlated wins and Martone's four correlated losses show why card-level W-L can overstate the effective sample size.
- Continue the v0.1.0 model unchanged. Do not tighten or loosen the longshot gate from one high-variance slate.

## 2026-10-04 — Slate 4 grading

### Results
- Top 10 Probability Card: **7-3 (70.0%)**. Model probabilities summed to **6.7306 expected wins**; Brier score **0.2244**.
- Official Playable Price Card: **5-5 (50.0%)**, **-0.8231u** at 1u flat staking, **-8.23% ROI**; Brier score **0.1994**.
- Clean cumulative Top 10: **27-13 (67.50%)**, expected wins **28.3544**, Brier **0.2119** through 40 picks.
- Clean cumulative Playable Price: **24-21 (53.33%)**, **+3.9599u**, **+8.80% ROI**, Brier **0.2193** through 45 plays.
- The goalie-save board was analyzed later, but no goalie save was added to the official locked Playable Price Card before puck drop; therefore the official Oct. 4 playable cohort remains the original 10 plays.
- Ladder Challenge 2026-10-A Day 1 won: Vancouver +1.5 covered in a 3-2 loss to Vegas.

### Market notes
- Top-10 puck lines went **2-2**: Anaheim +1.5 and Vancouver +1.5 won; Utah +1.5 and Calgary +1.5 lost. The clean Top-10 puck-line cohort is now **10-2**.
- Top-10 1+ point props went **4-1**: Eichel, Stone, Keller and Matthew Tkachuk won; Reinhart lost.
- Top-10 CGY-SEA Over 5.5 won easily in Seattle's 6-1 victory.
- Playable moneylines went **1-3**: Anaheim won; Vancouver, Utah and Calgary lost.
- Playable spreads went **2-1** and playable totals went **2-0**. Game-side losses were concentrated in moneylines rather than the broader team-market model.
- Tristan Luneau anytime goal +950 lost, moving the clean low-probability/high-EV anytime-goal watchlist to **0-4** across Blueger twice, Boone Jenner and Luneau. Luneau was also a limited-history fallback.
- Oct. 4 produced several useful correlated clusters: Anaheim ML/+1.5 both won; Utah ML/+1.5 both lost; Calgary ML/+1.5 both lost while the game over won. Treat these as clustered evidence rather than fully independent observations.

### Lessons / actions
- **No structural predictive-code change. v0.1.0 remains active.** The Top 10 has now produced 27 wins in 40 clean prospective picks and the playable card remains profitable overall.
- Do not increase puck-line weighting despite the 10-2 clean start. The two losses on Oct. 4 are a reminder that the earlier 8-0 streak was not enough evidence to alter pure probability ranking.
- Keep monitoring moneyline pricing separately. Oct. 4 moneylines were 1-3, but the clean moneyline sample remains too small and mixed to justify a market-specific code or gate change.
- Escalate the low-probability/high-EV anytime-goal cohort for review, but do not change the gate yet. A 0-4 record is poor, yet these are low-base-rate events and the expected number of wins across such a small sample is still below one; more independent observations are needed before tightening the threshold.
- Limited-history fallback remains a caution flag. Continue tagging it explicitly and avoid treating its probability estimates as equally mature evidence when making ladder/tie-break decisions.
- Goalie-save model remains on watch. No official Oct. 4 goalie save entered the clean record, so the clean goalie-save cohort remains **3-5** through Oct. 2.

## 2026-10-05 — v0.2 goalie-save shadow development started

### Why this experiment is justified
- The official clean goalie-save playable cohort is only 3-5, so it is still too small to replace v0.1.0 from results alone.
- However, opponent shot volume / workload has been the same identified weakness since opening night, so it is reasonable to begin testing a structural alternative now rather than waiting to write code later.
- This is a **shadow experiment only**. Official daily cards continue to use v0.1.0 until the replacement earns promotion prospectively.

### Shadow model design
- Added `src/wshlx_nhl/goalie_shadow.py` with a two-stage architecture:
  1. predict expected shots faced from opponent shot generation, team defensive environment, rest/workload and penalty/xG context;
  2. predict goalie save percentage from recent save skill, GSAx, rebound proxy and workload context;
  3. combine expected shots × expected save percentage into expected saves;
  4. fit a negative-binomial dispersion layer on chronological validation saves for O/U probabilities.
- Added `config/goalie_shadow_v0.2.yaml`, `scripts/train_goalie_shadow.py`, `tests/test_goalie_shadow.py`, and `data/results/goalie_shadow_v0.2.csv`.
- Historical validation remains chronological and recency-weighted. No random train/test split is permitted.

### Promotion rule
- Keep v0.1.0 official while v0.2 records shadow predictions on confirmed starters.
- Do not promote from historical backtest alone.
- Minimum prospective review point: **20 clean confirmed-start goalie props**. Prefer more if calibration is noisy.
- v0.2 must improve save-count MAE and probability calibration/Brier versus v0.1.0 without creating an obvious new directional bias.
- If it fails, revise or discard the shadow rather than forcing a version change.
