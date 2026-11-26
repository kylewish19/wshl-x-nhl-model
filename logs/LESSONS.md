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

## 2026-11-12 — grading completed 2026-11-25
- Clean Top 10 **5-5**, expected wins 7.01765, Brier 0.27318.
- Official Playable **5-12, -8.29604u, -48.80% ROI**, Brier 0.22903. ATG 0-5 (-5u), goalies 2-3 (-1.13068u), ML 1-2 (-1.12281u), spread 2-1 (-0.04255u), total 0-1 (-1u). All settled. MacKinnon played and exited injured, not a DNP.
- Playable shadow v0.3 **0-2, -2u**, Brier 0.32366; both plays STL@UTA. Consensus ATG shadow PASS. Current-season ATG top eight 4-4, winners Kyle Connor, Caufield, Tage Thompson, Hagel. This is a rank diagnostic, not executable price card.
- Goalie recorded picks v0.1 9-8, v0.2 10-7, v0.3 12-5; expected saves MAE 3.3981 / 3.5682 / 3.4034; over-event Brier 0.25396 / 0.25925 / 0.24636. Saved picks sometimes favor price rather than maximum probability; keep these distinct. Kuemper identity unresolved only in v0.3: keep locked fallback and flag; common 16 known-ID rows yield 9-7 / 9-7 / 11-5. Do not retroactively alter probabilities. Review identity resolver before next live run. Need compare maximum-probability directions and same price gates across versions.
- Official v0.2 goalie playable since promotion 5-4, +0.28391u. Two slates not enough to reverse promotion. Continue v0.1 and v0.3 research.
- Current clean cumulative Top 10 63-46; Official Playable 50-88, -41.8203u; Playable shadow 1-5, -4.1667u (six settled, not enough for promotion).
- Full clean market diagnostics saved: ATG 2-22 +1 void (-19.65u), goalie 19-24 (-7.3240u), ML 7-10 (-0.7879u), spread 10-8 (-2.2542u), totals 6-3 (+2.1442u). Prioritize ATG role/TOI/shot-volume calibration and matched goalie workload audits. Keep official control unchanged; recommend paper testing given substantial observed losses.
- Sources: https://www.nhl.com/news/st-louis-blues-utah-mammoth-game-recap-november-12-2026 ; https://www.nhl.com/news/nathan-mackinnon-cale-makar-exit-game-for-colorado-avalanche ; https://daily.hockey/starting-goalies/2026-11-12 ; https://www.agatetypes.com/hockey/november-12-2026 .
- Nov 13–24 skipped for betting; no retroactive official picks. Refresh completed historical games and current context for next slate. No predictive code change in this grading.

## 2026-11-25 — ATG game-level research and goalie identity audit
- Official NHL v0.2.0 remains active; no formula, card thresholds, or historical locks changed.
- Goalie identity: both goalie runners now prefer unique normalized historical full-name matches strictly before target date; ambiguous or initial-only identities are not guessed. Added regression tests. The original identity tests passed CI. New optional `--identity-board` in v0.3 validates the official board's date/game/name/team/line/player ID and rejects unresolved/mismatched rows. **Use this argument on the next new live workflow** (not retroactively on archived runs). Final CI for this additional guard was pending at checkpoint. This reduces API-dependent inconsistency but does not guarantee resolution if historical names are abbreviated and roster data unavailable.
- Added SHADOW_ONLY ATG game-level research: `src/wshlx_nhl/atg_game_shadow.py`, `scripts/train_atg_game_shadow.py`, `tests/test_atg_game_shadow.py`, `.github/workflows/atg-game-shadow.yml`.
- Compare fixed shrunk goal-rate baseline, shrunk shot-volume/finishing baseline, raw histogram gradient boosting, and logistic-calibrated boosting. Chronological split: 2021-22 warmup, 2022-23/2023-24 train, 2024-25 calibration, 2025-26 and 2026-27 through Nov 24 held out separately. No same-game realized shot, goal, or TOI features; no odds. Unit tests for current/future outcome invariance, probability bounds and duplicate rows passed.
- Historical ATG experiment is conditional on actual participation, not a prospective betting backtest. Missing xG, PP TOI, projected line/goalie and archived FanDuel odds. Baselines are not identical to the original official v0.1. No promotion or ROI claims before appropriate matched comparisons and prospective tracking.
- Refresh workflow run 45713367700 and ATG benchmark run 45713698148 were still running at checkpoint; benchmark test step succeeded, dataset/model results not yet verified. Check completion, coverage and metrics next. No new official picks generated. Full CI for later identity guard run 45713763159 pending.
- Next: verify data cutoff and completeness (including missing game counts), inspect benchmark calibration/Brier/log loss by season and experience/role band, compare with frozen official ATG on future supplied slates; investigate xG/PP TOI availability and prospective lineup inputs before adding them. Preserve all official and shadow tracking.

## 2026-11-25 — refresh verified, goalie matched audit, first ATG benchmark
- Resume refresh run 45713367700 succeeded: 6945 completed games, 13890 goalie starts and team-game rows, 385 current-season games through Nov 24, 32 teams, 78 current-season goalies, 732 current-roster skaters. Live skater aggregate not historical-cutoff certified. Metadata saved in data/model_runs/2026-11-25_resume_refresh.json.
- CI run 45713763159 passed all 23 tests including goalie matched identity guard.
- Nov 11–12 common resolved goalie sample 27 rows (Kuemper v0.3 unknown excluded). v0.1/v0.2/v0.3 odds-blind W-L 15-12/14-13/16-11; price-selected directions 17-10/15-12/19-8; MAE 4.38886/4.68378/4.48307; Brier .238868/.255206/.241564. Identical 4% edge and 5% EV gate on locked forecasts: 8-2 +4.93434u / 5-4 +0.28391u / 3-2 +0.65185u. Two slates only; not enough to reverse prior goalie promotion. Preserve earlier results. Detailed audit in data/results/goalie_matched_postpromotion_2026-11-12.csv and corresponding detail file.
- ATG initial run 45713698148 fetched 6945 games but stopped at invalid counts. Archive audit run 45714769216 succeeded using immutable first-run input. 249950 player-game rows, 23 goals>shots discrepancies (0.0092%); no missing/negative/PP>goals. Under predeclared research sensitivity policy, shots=goals lower-bound proxy only on those rows in lagged histories, exclude them from fitting/calibration/testing, original raw archive preserved. Not verified corrections. Audit and artifact contain rows and heldout predictions.
- First held-out ATG benchmark: train 94423, calibration 47221, test 47221 (2025-26) and 13857 (2026-27 to Nov 24). Brier 2025-26 / 2026-27: goal baseline .1219985/.1235268; shot/finish .1206734/.1220343; raw boosting .1216648/.1235569; calibrated boosting .1204703/.1221938. Shot model improves over goal baseline both seasons, calibrated boosting narrowly better in 2025-26 but not 2026-27. No clear dominance of complex model. Limited-history (<10 prior dataset GP) actual 9.59%/11.03%; goal baseline 14.08%/13.75%; shot 12.97%/12.15%; calibrated boost 11.10%/10.69%. Promising calibration but not proof of profit or superiority over official v0.1. Metrics and bands committed in data/model_runs/2026-11-25_atg_game_shadow_metrics.json and data/results/2026-11-25_atg_game_shadow_bands.csv.
- Decision: retain shot-volume baseline and calibrated boosting as separate research comparators. Do not select a new official ATG or tune on these now-observed holdout seasons. Next build strictly pregame future-board scoring, match original official predictions on identical eligible players, freeze both challengers and log prospective probabilities and FanDuel prices independently. Add role/PP TOI/xG only with dated source and new untouched test window. No official model change, no retroactive picks.

## 2026-11-25 — ATG pregame integration checkpoint
- Added src/wshlx_nhl/atg_pregame.py and scripts/run_atg_pregame.py. Both new ATG challengers score strictly prior player and team history using benchmark-consistent rolling features; use frozen calibrated model bundle from archive audit run 45714769216 and immutable history from run 45713698148, extending only completed regular-season games before target when needed.
- Match against full official ATG candidate CSV using date/game/player ID, listed/resolved teams, and active status. Unknown position, unresolved IDs, inactive and mismatched-team rows audited and excluded from the matched comparison only; original official universe untouched. Historical positions used unless verified position provided; actual participation remains unverified.
- Save odds-free probabilities before matched FanDuel pricing; compare official, shot/finish and calibrated boosting using identical 5pp edge and 5% expected ROI gate. All shadow cards paper only; official v0.2.0 unchanged.
- Live runner verifies Eastern date, NHL schedule matchup and all scheduled games FUT/PRE before first puck, checks time again after scoring, refuses overwrite of nonempty output directory and hashes input, model and output files. Manifest status remains PREGAME_PENDING_ARTIFACT_VERIFICATION until external artifact timestamp is verified. Replay always RETROSPECTIVE_SMOKE_ONLY; no retrospective official selections.
- Added tests/test_atg_pregame.py for training/pregame feature parity, odds invariance, future-date rejection, matching and price gates. Added .github/workflows/atg-pregame-shadow.yml; first archived full Nov 12 board integration test run 45715282170 initiated; final CI and replay outcome not yet verified. Historical artifact expires under GitHub retention policy; pin/recover frozen history and model before expiration. No new prospective predictions or results in this step.
- Next: inspect replay results and fix integration defects if any; save manifest/coverage and set up matched postgame grader before live use. Keep both challengers shadow-only; do not claim historical profit or change official model.

## 2026-11-25 — ATG integration and matched grading verified
- Pregame integration run 45715282170 succeeded; 30 tests passed. Archived Nov 12 full board: 343 candidates, 337 matched, 5 unresolved identities and 1 inactive excluded. Prior data cutoff Nov 11. Equal price gate qualified official 5, shot-based 2, calibrated boost 3. Manifest preserved in data/model_runs/2026-11-25_atg_pregame_smoke_manifest.json.
- Added src/wshlx_nhl/atg_grading.py, scripts/grade_atg_pregame.py, tests/test_atg_grading.py and .github/workflows/atg-shadow-grading.yml. Grader checks source workflow success/path, artifact metadata and timestamp, frozen probability and price hashes, matched player IDs, complete final games, and goal outcomes; DNP paper void. No refitting or postgame re-selection. Live dispatch by source run ID; replay permanently separate.
- Grading run 45715871716 succeeded through grading/artifact upload; 33 tests passed. Ten games, 337 matched, 332 settled, 5 DNP void. Official/shot/boost replay Top 10 4-6/6-4/6-4, Brier .126633/.122669/.124092, log loss .411120/.400432/.401642, AUC .695205/.719078/.710759. Equal price paper records 0-5 (-5u), 0-2 (-2u), 1-2 (+3.5u). RETROSPECTIVE_SMOKE_ONLY; no clean prospective or official season records changed; do not use this previously observed period as independent promotion evidence. Summary and manifest persisted in REPLAY_ONLY result and grading smoke manifest files.
- Frozen research provenance saved in config/atg_frozen_research_2026-11-25.json (hashes, source runs, dependency versions and artifact expiry). Original history artifact expires Dec 25 2026; trained model artifact expires Feb 23 2027. Repo is public, so did not publish binaries to main without explicit authorization. Download/save original artifacts privately before expiry. Refetching historical data may yield changed data; hashes must be checked. Long-term binary preservation still open.
- Next: prospective use with a full official candidate CSV and clean pregame verified upload; run matched grader after final games. Keep official v0.2.0 and both ATG challengers unchanged. Investigate PP TOI, xG and projected lines with dated sources and fresh holdout; improve goalie and team models through separate experiments. No new official picks.

## 2026-11-25 — advanced ATG source feasibility and team identity coverage
- Reviewed MoneyPuck data terms (https://moneypuck.com/data.htm): free noncommercial/ad-hoc journalist use with credit; no ingestion performed. NHL website terms (https://www.nhl.com/info/terms-of-service) also limit use and prohibit unauthorized automated collection. API-specific permission and intended commercial-use rights are not established; no new full-scale advanced-stat collection or redistribution authorized. Continue developing offline code with synthetic or appropriately licensed/authorized inputs; obtain applicable permission/source terms before bulk collection and commercial deployment. Earlier historical research artifacts are not a commercial license.
- Added scripts/probe_atg_advanced_sources.py, tests/test_atg_advanced_sources.py, .github/workflows/atg-advanced-source-audit.yml and docs/ATG_ADVANCED_DATA_PROTOCOL.md. Source audit run 45716267696 succeeded, 36 tests passed. First/middle/last archived game from each of six seasons: 18 games, 1,568 unblocked attempts including 111 goal events; 0 missing/unmatched shooter IDs, geometry, strength or opposing-goalie state; one missing shot type. NHL game-level timeonice and powerplay reports each returned 648 rows; observed ppTimeOnIce, evTimeOnIce, shTimeOnIce, ppShots and ppIndividualSatFor fields, including actual zeros. Sample feasibility only; not full coverage or verified all-row PP joins. Persisted source coverage CSV and example schemas JSON under data/results and data/model_runs. No xG fit yet.
- Fixed missing CAR and SEA in scripts/assemble_core_slate.py TEAM_NAMES map and added test requiring all 32 active teams; CI run 45716355962 pending at checkpoint. Identity mapping correction only; no predictive formula changed and no historical lock rewritten.
- Next: develop offline shot-level xG cross-fitting and PP usage feature ingestion with synthetic/authorized inputs, verify full coverage only once source rights resolved; retain frozen ATG challengers and focus also on existing-data goalie/team model diagnostics. No new official picks, no model promotion, official v0.2.0 unchanged.

## 2026-11-25 — direct final-score team-market research
- Existing official game_markets.simulate_game resolves simulated ties only for ML; spread and total calculations use unadjusted independent Poisson scores. This is a structural limitation, not evidence by itself of an advantage for any challenger. Official formulas and historical locks untouched.
- Added src/wshlx_nhl/team_market_shadow.py, scripts/benchmark_team_market_shadow.py, tests/test_team_market_shadow.py and .github/workflows/team-market-shadow.yml. Direct multinomial final-margin classes (away 2+, away 1, home 1, home 2+) and total classes (<=5, 6, >=7), regularized logistic classifiers with prior/current goal averages, lagged 5/20-game goals/shots and rest. Chronological feature tests passed; baseline is analytic infinite-simulation equivalent of official v0.1 team model with zero context. No new data downloads, reused archived refresh artifact.
- Benchmark run 45716648252 completed scoring, 40 tests passed. 6,945 games; 3,936 train (2022-23 through 2024-25), 1,312 2025-26 and 385 2026-27 diagnostic games through Nov 24. Direct model lost all five Brier comparisons in 2025-26; won two of five in 2026-27 (home ML .238001 vs .241238; away -1.5 .196028 vs .198435). Baseline won remaining eight of ten season-market comparisons. Direct model overpredicted home -1.5 (35.26% vs actual 30.11%; 34.70% vs actual 29.35%), underpredicted over 5.5 (52.27% vs 57.32%; 51.25% vs 59.48%). No promotion, no prospective challenger deployment justified by this benchmark. Metrics and manifest archived.
- Limitations: shots derived from goalie shots faced, not exact team SOG; no verified pregame goalie/lineup context, no archived odds; previously observed seasons are development diagnostics only. Do not tune to these results then claim independent validation.
- Next team research: isolate final-score tie treatment from rate-model changes, assess score distribution and era calibration on earlier training/calibration windows, freeze before genuinely new prospective slates; consider goalie quality only with dated pregame identities. Next goalie research: audit shots-faced workload prediction and short-start effects using existing archived data. Advanced xG/PP full collection still blocked by unresolved permissions; frozen ATG shadows ready. Official NHL v0.2.0 unchanged; no new picks or season record changes.

## 2026-11-25 — isolated team tie treatment and goalie workload audit
- Added team_tie_shadow.py, benchmark_team_tie_shadow.py, regression tests and team-tie-shadow workflow. Run 45717100136 succeeded, 42 tests passed. Analytic comparison on existing 6,945-game archive: unchanged baseline, resolve tied simulated score with one credited goal, preserve expected final total by solving regulation scale, and mean-preserving version with factor 0.993493 fitted on 2024-25 only. With fixed rates, tie resolution leaves ML, +/-1.5, and O5.5 unchanged; O6.5 gains probability of simulated 3-3. 2025-26/2026-27 baseline O6.5 Brier .250934/.253872; tie-only .248502/.250762; mean-preserving .249211/.251875; calibrated .249591/.252342. Actual O6.5 frequencies 46.875%/49.091%; baseline 41.946%/43.477%; tie-only 46.885%/48.348%. Mean reductions hurt O5.5 on both evaluation seasons. Tie-only promising diagnostic for totals, not promoted; regulation labels unavailable, expected means currently based on final scores (risk of double-counting), previously observed seasons not independent promotion evidence. Metrics and manifest saved.
- Added scripts/audit_goalie_workload.py and goalie-workload-audit workflow. Run 45717165583 succeeded through scoring/upload, 42 tests passed. Reconstructed official v0.2 trained from pre-July 2026 archive (13,120 input rows, internal chronological split); 770 actual 2026-27 starts through Nov 24 evaluated. Overall shots MAE 5.0602, saves MAE 5.0997, expected minus actual shots +0.4599, saves +0.6819. 38 starts under 50 min (4.94%) had actual shots 13.76 vs predicted 27.60, saves MAE 14.9084; 89 starts 50–<58 min saves MAE 4.3989; 643 starts >=58 min saves MAE 4.6171. Realized duration only diagnostic, never pregame feature; short starts not necessarily pulls. Actual total team shots minus starter shots averaged 12.32 in short cohort vs zero in >=58 min cohort. All 770 rows reported rest >=2 days: verify source goalie IDs/date order and rest feature distribution before using fatigue as a discriminator; no evidence for short-rest effects from this sample. Metrics and manifest persisted. Historical diagnostics conditional on actual starters, not frozen daily predictions or betting backtest.
- Next: investigate rest-feature coverage and archived starter identity integrity; test a pregame-only short-start mixture with fixed earlier-season training/calibration and common test rows, not actual minutes as input. Develop totals shadow integration only after evaluating regulation assumptions and freezing prospective protocol. Preserve existing official and shadow cards. No new picks, no promotion, official v0.2.0 unchanged.

## 2026-11-25 — goalie rest integrity and shortened-start mixture benchmark
- Added src/wshlx_nhl/goalie_short_shadow.py, scripts/benchmark_goalie_short_shadow.py, tests/test_goalie_short_shadow.py and .github/workflows/goalie-short-shadow.yml. Run 45717517239 succeeded through scoring/artifact upload, 44 tests passed. Reused existing archive only.
- Independently rebuilt days between starts and previous seven-day start counts by stable goalie ID/date. All 13,890 rows matched archived rest and seven-day counts exactly; all had explicit starter flag. Rest <=1 day by season: 66, 46, 16, 28, 35, 0 (2021-22 through current 2026-27). Thus the current zero is present in source history, not explained by a rest calculation bug. Not externally verified; no inference about relief appearances, true fatigue or league schedule. Do not fabricate back-to-back records.
- Short-start (TOI <3000s) risk model trained on 5,248 starts 2022-23/2023-24, calibration 2,624 starts 2024-25, fixed risk 4.8018%; 2025-26 and 2026-27 diagnostic sets 2,624 and 770. Lagged short-start rate, recent goalie/team stats, home, rest and prior starts only; realized duration is label only. Learned risk modestly beat constant risk on Brier (.048325 vs .048469; .046509 vs .046917) and log loss, AUC .57394/.62892. No independent prospective evidence.
- Compared matched simple Poisson regression means with calibrated NB single distribution, constant short/full mixture and learned mixture on synthetic half-goal save lines 20.5/24.5/28.5. Single distribution won all 3 Brier comparisons in 2025-26; current season constant mixture narrowly won 20.5 (.203108 vs single .203823), single won 24.5 (.239797), learned mixture marginally won 28.5 (.176965 vs single .176999). Single distribution had best saves MAE in both seasons (5.40925/5.07566 vs learned 5.41797/5.08048). No compelling overall mixture improvement. This is not a direct comparison to official v0.2, no actual FanDuel lines or prices, actual-starter conditional and previously examined evaluation windows.
- Decision: retain existing goalie v0.2 official and v0.1/v0.3 comparators. Do not promote or deploy short-start mixture; keep risk finding for future research. No historical record changes. Archive rest/risk/counts/metrics and manifest. Next: build a prospective paper-only totals tie-treatment comparator (only fixed 5.5/6.5 scope) and prepare one integrated workflow for existing ATG and goalie comparators on next user-submitted slate. Verify archived data source completeness before relying on unusual rest patterns; advanced-stat rights and artifact preservation remain unresolved.

## 2026-11-25 — unified daily shadow comparison
- Added src/wshlx_nhl/daily_shadow.py, scripts/run_daily_shadow.py, tests/test_daily_shadow.py and .github/workflows/daily-shadows.yml. New runner consumes successful frozen official core workflow artifact (date, game, model board, team means, goalie v0.1/v0.2/v0.3 files), checks source workflow metadata, frozen ATG model/history hashes, date and first-puck cutoff. Live result remains PREGAME_PENDING_ARTIFACT_VERIFICATION until independent output upload timestamp is checked. Archived replay is RETROSPECTIVE_SMOKE_ONLY; never counted toward prospective records.
- Totals shadow fixed to 5.5/6.5: official locked probabilities vs analytic Poisson control vs tie-only adjustment; 6.5 over gets probability of 3-3 tie, 5.5 unchanged. Uses exact archived team means, no estimated future score inputs; edge>=3pp, EV>=5%. Goalie comparison: matched resolved player IDs, game, team, half-line and prices across v0.1/v0.2/v0.3, excludes mismatches from research only; choose higher-EV side, edge>=4pp, EV>=5%. Nested frozen ATG paper boards use original 5pp/5% gates. No model/official threshold change.
- Unified workflow run 45718113354 initiated with Nov 12 archived board; final smoke result and CI not verified at time of initial entry. Existing original daily cards and earlier shadows remain separate. No live slate generated. Next verify run and persist manifest; implement unified postgame grading for totals/goalies, plus wrapper to verify parent artifact timestamp for nested ATG, and maintain separate prospective cumulative log. Live use requires a successful official pregame artifact in time before first puck; not a replacement for official core run. Long-term frozen artifact retention still unresolved.

## 2026-11-25 — unified daily comparison and grading verified
- Unified comparison run 45718113354 succeeded (46 tests). Archived Nov 12 slate: 10 total pairs, 16 matched goalie lines (1 identity mismatch excluded), 337 ATG candidates. Manifest saved data/model_runs/2026-11-25_unified_shadow_smoke_manifest.json.
- Added src/wshlx_nhl/daily_shadow_grading.py, scripts/grade_daily_shadow.py, tests/test_daily_shadow_grading.py, .github/workflows/daily-shadow-grading.yml. Validates parent/nested artifact hash and pregame timestamp chain, reads completed game-level team, starter and skater outcomes, grades paper selections without recomputation. Totals and goalie calibration use one Over probability per line. Goalie requires explicit starter flag and nonstarter void; ATG DNP void. Cumulative Brier/log loss observation-weighted; duplicate date/market/model blocked. No automatic official changes.
- Grading replay run 45719012128 completed successfully (49 tests), 10 games, 0 prospective ledger rows. ATG official/shot/boost Brier .126633/.122669/.124092 and price records 0-5 (-5u), 0-2 (-2u), 1-2 (+3.5u). Goalies v0.1/v0.2/v0.3 Brier .249003/.260592/.246601, price 4-2 (+1.42716u), 2-3 (-1.13068u), 2-2 (-.14815u); agree with earlier matched Nov 12 audit. Totals official/analytic/tie-only Brier .257549/.258349/.246890, price 0-1 (-1u), 0-1 (-1u), 1-1 (+.12u). Replay results never independent promotion evidence; no official record edits.
- Initialized data/results/prospective_shadow_ledger.csv (header only), docs/DAILY_SHADOW_GRADING.md. Live grader defaults to existing canonical ledger, outputs updated ledger/cumulative artifacts; reviewed commit required to persist, no automatic write rights. Last default-ledger-path change after replay is pending its own CI verification. Live requires a successful pregame official core and unified artifact plus authorized complete finalized outcome files; no live slate tested yet. Existing artifact retention and advanced data permissions still unresolved.
- Next: verify current CI, address retention/provenance, then execute next fresh user-submitted slate and record clean prospective results. Do not keep tuning on the already examined evaluation seasons. Official v0.2.0 remains unchanged.

## 2026-11-25 — slate readiness and frozen research recovery
- Latest canonical ledger default-path CI run 45719086287 succeeded; 49 tests passed. Prior prospective ledger still header-only.
- Added scripts/preflight_slate.py, tests/test_preflight_slate.py, .github/workflows/slate-readiness.yml. Offline exact-date and game/team validation, complementary spreads, finite numeric context, integer American odds, full six core prices per matchup, duplicate player/line checks, explicit missing ATG/goalie game coverage and input SHA-256 hashes. Requires four nonempty boards; partial/late boards remain separate, not silently filled. Does not independently authenticate sportsbook, current schedule, player eligibility or timestamp. Workflow 45719463447 succeeded (52 tests) on archived Nov 12: 10 games, 60 core rows, 343 ATG rows, 17 goalie lines, no games without either player market. Verified original artifact availability and expiry metadata (not payload hashes in this workflow); manifest data/model_runs/2026-11-25_slate_readiness_smoke.json. No new picks.
- Added scripts/verify_research_backup.py, tests/test_research_backup.py, docs/FROZEN_RESEARCH_RECOVERY.md. Verifies original four binary payload hashes from private ZIP copies without extraction/unpickling. Actual private backup has NOT been created; no private destination supplied, public raw-data publication avoided. Original history 15067769899 and team/goalie 15069296241 expire Dec 25 2026, ATG bundle 15068418480 expires Feb 23 2027; download before expiry, verify and retain privately. Current workflows still reference original runs; recovery after expiry requires reconfiguring authorized artifact source. Backup tests pending CI at checkpoint.
- Next: use next fresh user-supplied FanDuel slate; complete dated official core run with independently checked schedule, pregame context and authorized current data, then unified research grading. Generic reusable official core runner has not been built; existing date-specific workflow is the basis. No official predictive or record changes. Advanced data rights unresolved, no further historical tuning justified absent fresh prospective evidence.


## 2026-11-26 — Nov25 clean grading and prospective diagnostics
- Verified all 14 finalized games, original core artifact 15073700466 and research artifact 15073920102 against pregame timestamps/hashes. Grading run 45828937854 succeeded; artifact 15122245729. Official Top10 5–5 (expected 6.9189, Brier .29616), Playable 10–10 (+17.78056u, ROI .88903), price shadow 3–1 (+1.56210u). All official selections settled; no voids. Cumulative clean Top10 68–51 (57.14%), Playable 60–98 (37.97%, -24.0397u), price shadow 4–6 (-2.6046u). Late-lock cohorts unchanged. Cumulative Brier uses previous rounded aggregate.
- Top10 nine puck lines went 4–5, Oettinger O21.5 won with 24 saves. Do not force diversity or change weights after one slate. Investigate persistent puck-line calibration and underestimation of multi-goal margins using existing chronological data rather than this slate alone. Official price ATG 2–4 (+17u) because Simashev +1500 and Knuble +600 scored; five limited-history qualifiers 2–3, do not infer fallback calibration from two high-paying hits. Excluding ATG, official price 8–6 (+0.78056u). Totals 3–0, goalie saves 4–4, spread 1–1, ML 0–1.
- First clean unified prospective ledger: totals official 3–0 (+2.5621u), analytic 2–0 (+1.6530u), tie-only 1–0 (+.8197u); matched 14 Brier .241212/.240640/.249376 respectively. Goalie v0.1 9–6 (+2.02834u), v0.2 4–4 (-.32502u), v0.3 4–1 (+2.72552u); 24 matched/settled, Brier .252743/.249866/.243781, saves MAE 3.7758/4.0476/3.8557. Unanimous goalie directions 7–4; unanimous and v0.3 price gate 4–1; all three price gates 3–0 (Oettinger, Tarasov, Merilainen). These groups were displayed pregame, but not official cards; preserve as separate prospective diagnostic, sample too small, two picks share VAN@DET game. No promotion. ATG matched 476, 473 settled, 3 void; official/shot/boost Brier .133812/.131314/.131625; top10 2–8/5–5/4–6; price 2–4 (+17u)/0–4 (-4u)/0–4 (-4u). Current-season blend full-board top10 5–5, consensus pass. Different matched/full populations noted. No new ATG model promotion; lower Brier and higher top10 accuracy do not imply profitability.
- Persisted three official graded CSVs, grading summary JSON, updated season summary and first nine prospective ledger rows. No predictive code or gate changes. Next: retain frozen models, grade future slates on identical cohorts, maintain agreement diagnostic separately; analyze persistent calibration and limited-history risk only with chronological evidence. Grading fetched finalized box scores for this one slate, not a full historical refresh or advanced-data acquisition. Private backup/advanced-data permissions remain unresolved.

## 2026-11-26 — selected +1.5 puck-line calibration audit
- Re-read all 12 clean official Top10 and Playable graded cards, excluded late locks and voids; every tracked puck-line pick in these cohorts was +1.5. Top10 28–22/50 (56.00%) vs mean 70.5419%, expected 35.27096 wins, Brier .269413; before Nov25 24–17/41 vs expected 29.01821. Sep–Oct 13–6 vs 13.65036 expected; November 15–16 vs 21.6206 expected. Probability bands .60–.65: 3/3; .65–.70: 10/19; .70–.75: 11/22; .75+: 4/6. Playable 11–9, mean 69.2716%, -2.71074u, ROI -13.5537%; cohorts overlap and must not be pooled.
- Existing archived zero-context analytic benchmark (2026-11-25_team_tie_shadow_metrics.csv baseline) implies multi-goal margin frequencies predicted vs observed: 2024–25 53.91% vs 61.74%, 2025–26 53.86% vs 56.78%, current season through Nov24 54.48% vs 58.44%. This supports a broad margin underestimation issue, but full-schedule baseline and selected actual card gaps are not interchangeable. The direct final-score class challenger did not consistently beat baseline Brier across spread directions and seasons; tie-only correction leaves ±1.5 unchanged. No further tuning on observed holdouts, no arbitrary 14.5pp haircut, no official changes. Keep matched prospective spread comparison as next implementation task, alongside consensus goalie tracking.
- Created scripts/audit_puckline_calibration.py (read-only, exact clean filename matching; script not independently executed yet) and data/results/2026-11-26_puckline_calibration_audit.json (computed directly from archived graded rows and existing benchmark metrics). No new games or advanced data gathered, no new predictive fit or picks.
