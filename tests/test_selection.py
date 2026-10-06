import pandas as pd
from wshlx_nhl.selection import top_probability_card, playable_price_card


def base_df():
    return pd.DataFrame([
        {"market":"moneyline","selection":"A","model_probability":0.70,"odds_american":-120,"active":1,"starter_confirmed":1},
        {"market":"point_1plus","selection":"B","model_probability":0.65,"odds_american":110,"active":1,"starter_confirmed":1},
        {"market":"goalie_saves","selection":"C","model_probability":0.80,"odds_american":-110,"active":1,"starter_confirmed":0},
        {"market":"goalie_saves","selection":"D","model_probability":0.90,"odds_american":None,"active":1,"starter_confirmed":0},
    ])


def test_top_includes_fanduel_listed_goalie_without_confirmation():
    out = top_probability_card(base_df(), 10)
    assert "C" in set(out.selection)
    assert "D" not in set(out.selection)


def test_playable_gate():
    out = playable_price_card(base_df(), min_expected_roi=0.0)
    assert len(out) >= 1
