# Model Card — v0.1.0

## Purpose
Estimate pregame NHL market hit probabilities and evaluate them prospectively across the 2026-27 season.

## Markets
Moneyline, puck line, game total, anytime goal, anytime assist, goalie saves, player 1+ point and player 2+ points.

## Core modeling family
Scikit-learn histogram gradient boosting with Poisson loss for count means, negative-binomial distribution layers for threshold probabilities, and chronological probability calibration when enough validation data is available.

## Validation
Time-based holdout only. Report MAE/deviance for count estimates and Brier score/log loss/calibration error for event probabilities. Betting ROI is an evaluation metric for the priced card, not a training target.

## Known v0.1 limitations
- Early-season role changes can move faster than historical models; manual/current line and PP-role context is therefore required.
- Starting-goalie uncertainty materially changes game and save projections.
- Public injury/lineup data may be incomplete or change close to puck drop.
- Correlated picks can legitimately appear in the raw Top 10 because that card ranks pure marginal hit probability. Correlation management belongs to staking/parlay construction, not probability ranking.
