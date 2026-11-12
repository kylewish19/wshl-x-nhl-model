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

## 2026-11-09 — Slate grading

### Results
- Top 10 Probability Card: **6-4 (60.0%)**. Expected wins **6.5416**; Brier score **0.2845**.
- Official Playable Price Card: **5-2 with 1 void (71.43% on settled bets)**, **+2.6586u**, **+37.98% ROI** at 1u flat staking on seven settled bets.
- Cole Knuble anytime goal +550 was **VOID** because he was scratched and did not play.
- v0.3 playable shadow: **1-1**, **-0.1667u**.
- Goalie v0.2 directional diagnostic: **4-2**. Notably, v0.2 had Joseph Woll Under 22.5 while official v0.1 had Woll Over 22.5; Woll finished with 18 saves, so the shadow direction was correct.
- Current-season ATG shadow: **2-6** across the eight locked candidates; Leon Draisaitl and Connor McDavid scored.

### Market notes
- Official goalie-save playable props went **4-2**: Levi Over, Askarov Over and Sorokin Over won; Woll Over and Merilainen Over lost.
- Islanders-Sharks Under 6.5 won with five total goals.
- Connor McDavid anytime goal +115 won.
- San Jose +1.5 won outright, while Vancouver +1.5 and Rangers +1.5 both missed by one goal relative to the +1.5 line.
- Edmonton moneyline won 3-1.

### Lessons / actions
- **No structural predictive-code change from this slate alone.** The official playable card performed well, but one slate is not enough evidence to loosen or tighten gates.
- Continue the goalie v0.2 shadow comparison. The 4-2 directional result and the correct Woll disagreement are useful evidence, but the prospective sample is still too small for promotion.
- Keep scratch/lineup validation as a mandatory pregame data-quality step. Knuble's void is not a model loss, but late scratch detection matters for executable cards.
- Do not overreact to the 2-6 current-season ATG shadow; the Brier score was relatively strong because most misses were low-probability events. Continue collecting prospective data before changing the ATG architecture.

## 2026-11-10 — LATE_LOCK slate grading

### Results
- This slate remains **LATE_LOCK / diagnostic only**. User-supplied FanDuel prices were pregame, but the final computational lock completed after the first puck drop. It does **not** change clean cumulative records.
- Top 10 Probability Card: **8-2 (80.0%)**. Expected wins **7.1492**; Brier score **0.1634**.
- Official Playable Price Card: **8-5 (61.54%)**, **+1.0451u**, **+8.04% ROI** at 1u flat staking; expected wins **7.3040**; Brier score **0.1414**.
- Playable Price shadow v0.3: **2-0**, **+1.8130u**, **+90.65% ROI**; calibrated expected wins **1.1906**. Bobrovsky Under 27.5 and NJD-WPG Under 6.5 both won.
- Official goalie v0.1 directional board: **8-5**, Brier **0.2131**.
- Goalie v0.2 directional shadow: **5-8**, Brier **0.2677**.
- Current-season ATG shadow top-eight diagnostic: **2-6**; Kirill Kaprizov and Kyle Connor scored.

### Market notes
- Top-10 +1.5 puck lines went **5-2**: Ottawa, Nashville, Montreal, Detroit and Winnipeg covered; Columbus and Toronto did not.
- Top-10 goalie unders went **3-0**: Bobrovsky U27.5 (22), Daws U26.5 (19), Fowler U25.5 (22).
- Official playable goalie saves went **5-0**: Bobrovsky U27.5, Daws U26.5, Fowler U25.5, Wallstedt O24.5 and Gibson O22.5.
- Official playable ATGs went **0-3**: William Wallinder +1600, Zack MacEwen +1200 and Nathan MacKinnon +115.
- The two limited-history fallback ATG longshots (Wallinder, MacEwen) both lost. v0.3 correctly quarantined all ATG selections on this slate.
- NJD-WPG Under 6.5 won exactly below the line with a 4-2 Winnipeg final.

### Lessons / actions
- **No predictive-model promotion or structural change from this slate.** Because it is LATE_LOCK, it is diagnostic evidence rather than clean prospective promotion evidence.
- The goalie v0.2 shadow should remain shadow-only. After a 4-2 Nov. 9 result, it went 5-8 here while official v0.1 went 8-5; the combined evidence is mixed and below the planned prospective review threshold.
- Continue testing playable v0.3. Its 2-0 result is encouraging and its ATG quarantine avoided three official losses, but the clean prospective v0.3 sample is still too small for promotion.
- Longshot / limited-history ATG remains a concern. Do not loosen the official ATG gate; continue prospective shadow collection before any architecture or gate change.
- **Lineup-validation process adjustment:** Hayden Hodgson had been excluded from the submitted ATG universe based on a projected-scratch read, but he ultimately played and scored. Going forward, do not hard-exclude an ATG player solely from an early projected lineup when official game-roster confirmation is not yet available; treat projected scratches as provisional and re-check as close to lock as possible.

## 2026-11-11 — Goalie-save model promotion
- Repeated clean prospective evidence now satisfies the pre-written Oct. 5 goalie promotion rule.
- On 33 matched clean prospective props, v0.2 beat v0.1 on directional record (**19-14 vs 15-18**), saves MAE (**4.963 vs 5.298**) and pick Brier (**0.244 vs 0.275**).
- **Promote goalie v0.2 to official effective 2026-11-11; overall model version becomes v0.2.0.**
- Keep the existing 4% goalie edge gate and 5% minimum EV. Do not rewrite historical official cards.
- A new v0.3 simulation experiment (current-season retraining + r20 baselines + shot/save Monte Carlo) failed to improve actionable performance. On clean date-safe backfill, v0.2 had better MAE/Brier; at the existing goalie edge gate v0.2 went **9-6, +1.7342u** while v0.3 went **6-9, -3.6844u**.
- **Do not promote v0.3.** Complexity is not an improvement by itself; keep it research-only.

## 2026-11-11 — Clean prospective slate grading

### Results
- Top 10 Probability Card: **6-4 (60.0%)**. Expected wins **6.5789**; Brier **0.2597**.
- Official Playable Price Card: **5-3 (62.5%)**, **+1.0354u**, **+12.94% ROI** at 1u flat staking. Expected wins **4.3668**; Brier **0.1855**.
- Playable Price shadow v0.3: **0 selections**. This is a valid PASS slate and does not change its cumulative W-L.
- Official goalie v0.2 playable subset: **3-1**, **+1.4146u**, **+35.36% ROI**.
- Top-10 goalie v0.2 selections: **2-1** (Vladar Under and Jarry Over won; Brossoit Over lost).
- Full goalie directional board: v0.1 **8-3**, official v0.2 **6-5**, goalie v0.3 research **8-3**.
- Current-season ATG shadow top-eight: **3-4 with 1 void** (Logan Cooley DNP).

### Market notes
- Nashville +1.5, San Jose +1.5, Edmonton ML and Philadelphia +1.5 won.
- Calgary +1.5, Buffalo +1.5 and Utah +1.5 lost.
- Official playable goalie results:
  - Dan Vladar U24.5: **WIN**, 21 saves.
  - Laurent Brossoit O22.5: **LOSS**, 18 saves.
  - Yaroslav Askarov O24.5: **WIN**, 33 saves.
  - Tristan Jarry O20.5: **WIN**, 30 saves.
- PIT-SJS U6.5 won with a 3-2 shootout final.
- Connor McDavid ATG lost; he recorded an assist but no goal.
- Tristan Luneau ATG +800 lost; Anaheim's goals were scored by Cutter Gauthier and Mikael Granlund.

### Goalie-model review
- **No reversal of the Nov. 11 goalie v0.2 promotion.** One slate favored v0.1 and research v0.3 on the full directional board, but the promoted v0.2 remains ahead on the accumulated clean prospective matched sample.
- Adding this slate to the 33-prop promotion sample gives:
  - v0.1: **23-21 (52.3%)**, approximate cumulative saves MAE **5.527**, Brier **0.262**.
  - v0.2: **25-19 (56.8%)**, approximate cumulative saves MAE **5.371**, Brier **0.245**.
- More importantly for betting, the **price-gated official v0.2 goalie card went 3-1**. Continue evaluating both full-board calibration and the actual executable subset separately.
- v0.3 research went 8-3 directionally on this slate, but its prior date-safe backfill was inferior to v0.2 at the price gate. Continue research only; do not promote from one strong day.

### ATG / playable shadow
- Playable Price shadow v0.3 passed the entire slate. Do not force action when its gates reject everything.
- The official ATG card went 0-2 (Luneau, McDavid). The longshot limited-history ATG concern remains active.
- Logan Cooley was a late DNP after appearing in earlier projected lineup information. Continue late lineup validation, and grade any DNP sportsbook market as VOID when applicable.

### Action
- **No predictive code change from this slate.**
- Keep NHL model **v0.2.0** and official goalie component **v0.2**.
- Continue collecting clean prospective goalie v0.1/v0.2/v0.3 comparisons and official price-gated goalie results.
- Continue Playable Price shadow v0.3 exactly as specified; a zero-play slate is informative, not a failure.

