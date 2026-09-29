# WSHL_X NHL Model

Season-long NHL prediction and grading framework for:

- Moneyline
- Puck line / spread
- Game total goals O/U
- Anytime goal scorer
- Anytime assist
- Goalie saves O/U
- Player 1+ point
- Player 2+ points

## Official workflow

1. Build the slate from the games Kyle sends.
2. Refresh current rosters, injuries, expected lines/PP units, and projected/confirmed goalies.
3. Run models **without odds**.
4. Lock the **Top 10 Probability Card**: the 10 eligible picks with the highest calibrated hit probability.
5. Add FanDuel odds after the Top 10 is locked.
6. Run the independent **Playable Price Gate** using implied probability, model edge, and expected value.
7. Save both cards separately.
8. Next day, grade both cards and calculate W-L, hit rate, Brier score/calibration, and (for priced picks) ROI.
9. Append lessons to `logs/LESSONS.md`. Change code only when evidence supports a repeatable improvement; never rewrite history.

## Data window

Initial training window: regular seasons 2021-22 through 2025-26. The live 2026-27 season is appended game by game. Historical observations are recency-weighted, so recent seasons matter more without discarding useful older samples.

Primary data sources:

- NHL public web endpoints: schedule, rosters, boxscores, play-by-play and player game logs.
- MoneyPuck downloadable data for xG, shot quality and richer skater/goalie/team features. Credit MoneyPuck.com when its data is used.

## Modeling design

This project deliberately does **not** use one generic model for everything.

- `game_goals_home` and `game_goals_away`: gradient-boosted Poisson regressors estimate expected team goals. Monte Carlo simulation derives ML, puck line and game-total probabilities.
- `player_goals`, `player_assists`, `player_points`: gradient-boosted Poisson regressors estimate expected event counts. Negative-binomial probability layers handle overdispersion and produce P(1+), P(2+), etc.
- `goalie_saves`: gradient-boosted count model estimates saves; a negative-binomial layer converts the estimate into O/U probabilities.
- Optional isotonic calibration maps raw probabilities to better out-of-sample probabilities on validation data.

All validation is chronological. Random train/test splits are prohibited because they leak future hockey context into the past.

## Selection rules

### Top 10 Probability Card

- Odds are invisible to this stage.
- Rank all eligible candidate picks by calibrated probability.
- Lock exactly 10 when at least 10 eligible markets exist.
- A pick remains in this cohort even if the later price is awful.
- Track W-L/hit rate and probability quality separately from betting ROI.

### Playable Price Card

- Created only after odds arrive.
- Model probabilities never change because of odds.
- Default gate: positive expected value plus a market-specific minimum edge over implied probability.
- Track W-L, hit rate, units/ROI and closing-line value when available.

## Important slate rules

- Goalie-save props are not official until the expected starter is sufficiently confirmed.
- If a starting goalie is uncertain, game markets may be run as goalie scenarios; the uncertainty must be recorded.
- Injured/out players are excluded. Questionable players require an availability flag.
- Current line/PP role matters heavily for player props, especially early in the season.
- No same-day result information may enter prediction features.

## Quick start

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
pytest -q
```

Train from prepared feature tables:

```bash
python scripts/train_models.py --data-dir data/processed --model-dir models
```

Create a probability card from a slate candidate CSV:

```bash
python scripts/make_cards.py \
  --candidates data/manual/candidates.csv \
  --top10-out data/picks/top10.csv
```

After odds are added to the candidate file:

```bash
python scripts/make_cards.py \
  --candidates data/manual/candidates_with_odds.csv \
  --top10-out data/picks/top10.csv \
  --playable-out data/picks/playable.csv
```

Grade a locked card:

```bash
python scripts/grade_card.py \
  --picks data/picks/top10.csv \
  --results data/results/results.csv \
  --out data/results/top10_graded.csv
```

## Versioning

- `v0.1.x`: plumbing/bug fixes only.
- `v0.x.0`: justified model/feature change after grading evidence.
- Every change gets an entry in `logs/LESSONS.md` with the problem, evidence, change, and expected effect.
