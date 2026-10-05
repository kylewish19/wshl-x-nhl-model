# NHL 10-Day Ladder Challenge

This is a separate betting/selection challenge built from the NHL model outputs. It does not replace or alter the official Top 10 Probability Card or Official Playable Price Card.

## Goal
Lock exactly one ladder ticket per challenge day with final FanDuel odds between **-120 and +100**.

The ticket may be:
- one straight bet in the target odds window, or
- a parlay with any number of model-supported legs whose combined price lands in the target window.

## Selection objective
The ladder is **probability-first**. The primary objective is to maximize the model-estimated probability that the entire ticket wins, subject to the final price being between -120 and +100.

This is different from the Official Playable Price Card, which is edge/EV-gated. A ladder leg may come from the broader eligible model candidate universe even if it does not clear the Official Playable Price gate, because the ladder optimizes ticket survival probability rather than expected value.

## Daily process
1. Run and freeze the day's model probabilities first.
2. Keep all normal eligibility rules: active players only and no scratched/injured players. For goalie saves, a goalie/line shown on a FanDuel screenshot supplied by the user is eligible immediately; no separate starter confirmation is required.
3. If a listed goalie ultimately does not start and FanDuel voids the wager, grade that ladder leg/ticket according to the sportsbook settlement (normally VOID), not as a model loss.
4. Apply current FanDuel prices only after probabilities are frozen.
5. Evaluate all straight bets priced from -120 through +100.
6. Evaluate parlays built from the strongest eligible model probabilities until the combined FanDuel price falls in the -120 through +100 range.
7. Estimate full-ticket hit probability.
   - For clearly independent cross-game legs, use the product of calibrated leg probabilities.
   - Do not blindly multiply same-game/same-player/same-team correlated legs. Use a modeled joint estimate/simulation when available; otherwise avoid that combination for the ladder.
8. Choose the eligible ticket with the highest modeled full-ticket probability.
9. Tie-breakers: fewer legs, lower correlation/uncertainty, stronger data quality (veteran/established model over limited-history fallback), then better model edge/EV.
10. Lock one ticket before the relevant games start. Never retroactively change a locked ladder ticket.

## Tracking
Track the ladder separately from all official model cohorts:
- challenge_id
- day_number (1-10)
- date
- ticket type (STRAIGHT/PARLAY)
- legs
- final FanDuel odds
- model-estimated ticket probability
- model fair odds if calculated
- result (WIN/LOSS/VOID/PENDING)
- stake and payout when supplied by the user
- notes on correlation, sportsbook listing/settlement status, and data-quality flags

A ladder loss ends that challenge run. A new 10-day run may begin afterward without rewriting the failed run.

## Model/version rule
The ladder uses the same active NHL predictive model version as the daily slate. Creating or changing ladder-selection rules does **not** by itself change the predictive model version.
