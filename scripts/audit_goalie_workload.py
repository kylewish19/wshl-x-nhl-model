"""Historical starter-workload diagnostic, not a new prediction model."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from wshlx_nhl.goalie_shadow import train_goalie_two_stage_shadow

def summarize(d):
    return {"rows":len(d),"mean_actual_shots":float(d.shots_against.mean()),
            "mean_expected_shots":float(d.expected_shots.mean()),
            "shot_bias":float((d.expected_shots-d.shots_against).mean()),
            "shot_mae":float((d.expected_shots-d.shots_against).abs().mean()),
            "saves_mae":float((d.expected_saves-d.saves).abs().mean()),
            "saves_bias":float((d.expected_saves-d.saves).mean()),
            "team_minus_starter_shots":float((d.team_total_shots-d.shots_against).mean())}

def main():
    ap=argparse.ArgumentParser()
    for k in ["features","team-games","out"]: ap.add_argument("--"+k,required=True)
    a=ap.parse_args()
    st=pd.read_parquet(a.features);t=pd.read_parquet(a.team_games)
    assert pd.to_datetime(st.date).max()<pd.Timestamp("2026-11-25")
    assert len(st)==13890 and len(t)==13890
    assert not st.duplicated(["game_id","team"]).any()
    assert not t.duplicated(["game_id","team"]).any()
    cfg=yaml.safe_load(Path("config/goalie_shadow_v0.2.yaml").read_text())
    w=cfg["workload"];s=cfg["save_rate"]
    train=st[pd.to_datetime(st.date)<pd.Timestamp("2026-07-01")]
    test=st[pd.to_datetime(st.date)>=pd.Timestamp("2026-07-01")].copy()
    model=train_goalie_two_stage_shadow(train,w["numeric"]+w["categorical"],w["categorical"],s["numeric"]+s["categorical"],s["categorical"])
    x,y,z=model.predict_components(test)
    test["expected_shots"]=x;test["expected_save_pct"]=y;test["expected_saves"]=z
    test=test.merge(t[["game_id","team","shots_against"]].rename(columns={"shots_against":"team_total_shots"}),on=["game_id","team"],validate="one_to_one")
    if len(test)!=770 or test.team_total_shots.lt(test.shots_against).any():
        raise ValueError("Starter/team coverage inconsistent")
    # Realized TOI is a diagnostic label only, never a predictor.
    cohorts={"all":test,"short_under_50m":test[test.toi_seconds<3000],
             "50_to_under_58m":test[test.toi_seconds.between(3000,3479)],
             "58m_plus":test[test.toi_seconds>=3480],
             "home":test[test.is_home==1],"away":test[test.is_home==0],
             "rest_0_1d":test[test.days_rest<=1],"rest_2plus":test[test.days_rest>=2]}
    metrics=pd.DataFrame([{"band":k,**summarize(v)} for k,v in cohorts.items() if len(v)])
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    metrics.to_csv(out/"metrics.csv",index=False)
    test[["date","game_id","team","goalie_id","toi_seconds","shots_against","saves","team_total_shots","expected_shots","expected_save_pct","expected_saves"]].to_parquet(out/"detail.parquet",index=False)
    meta={"status":"HISTORICAL_DIAGNOSTIC_ONLY","train_input_rows":len(train),"test_rows":len(test),
          "test_last_date":str(pd.to_datetime(test.date).max().date()),
          "limitations":["Conditional on actual starters; not archived FanDuel boards","Realized ice time groups are diagnostic only; short starts can include injury, pull or other reasons","Reconstructed official v0.2 components on archived features, not frozen daily forecasts"]}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== WORKLOAD MANIFEST ===")
    print(json.dumps(meta,indent=2))
    print("=== WORKLOAD METRICS ===")
    print(metrics.to_csv(index=False))
    print("=== END WORKLOAD ===")
if __name__=="__main__":main()
