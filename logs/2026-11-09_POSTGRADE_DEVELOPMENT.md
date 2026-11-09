# NHL Post-Grade Development — 2026-11-09

## Active-market clean diagnostics through Nov. 8
- Anytime goal: **1-15**, 6.25%, **-13.80u, -86.25% ROI**
- Goalie saves: **11-18**, 37.93%, **-8.2832u, -28.56% ROI**
- Moneyline: **6-8**, 42.86%, **+0.3349u, +2.39% ROI**
- Spread: **7-7**, 50.00%, **-2.7325u, -19.52% ROI**
- Total: **4-2**, 66.67%, **+1.2109u, +20.18% ROI**

These are selected Official Playable observations, not the full model universe, so they are used for reliability/risk diagnostics rather than direct predictive retraining.

## Decisions
1. Official v0.1 remains unchanged.
2. Official Playable remains the historical control for now.
3. Playable v0.3 keeps the full ATG quarantine.
4. No goalie v0.2 promotion.
5. Current-season skater shadow remains shadow-only.
6. Add a dedicated ATG consensus research track instead of reopening ATGs in v0.3.

## ATG consensus shadow v0.1
New code:
- `src/wshlx_nhl/atg_consensus_shadow.py`
- `scripts/build_atg_consensus_shadow.py`
- `config/atg_consensus_shadow_v0.1.yaml`
- `tests/test_atg_consensus_shadow.py`

Rules:
- Exclude limited-history and rookie fallback projections.
- Require at least 8 current-season games when GP is available.
- Use **min(official v0.1 probability, current-season shadow probability)** as the consensus probability.
- Require consensus probability >= 30%.
- Require model disagreement <= 12 percentage points.
- Require edge vs FanDuel >= 5%.
- Require expected ROI >= 5%.
- Shadow-only; no effect on Official Top 10 or Official Playable.
- Promotion review no earlier than 25 clean prospective decisions, with positive ROI and better Brier/calibration than official ATG.

## Rationale
The Official Playable ATG cohort is now 1-15 and the Nov. 8 four fallback ATGs all lost. A blanket ATG reopen would be unsupported. The consensus shadow gives the project a path to rehabilitate the market using agreement between the old scorer model and current-season form without contaminating the official record.
