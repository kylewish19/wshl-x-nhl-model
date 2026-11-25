import argparse
from pathlib import Path
import json
import joblib
import pandas as pd
from wshlx_nhl.team_market_shadow import build_team_features,benchmark

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--team-games",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    raw=pd.read_parquet(a.team_games)
    assert pd.to_datetime(raw.date).max()<pd.Timestamp("2026-11-25")
    assert raw.game_id.nunique()==6945
    z=build_team_features(raw)
    scores,preds,models=benchmark(z)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    scores.to_csv(out/"metrics.csv",index=False)
    preds.to_parquet(out/"predictions.parquet",index=False)
    joblib.dump(models,out/"models.joblib")
    meta={"status":"HISTORICAL_DIAGNOSTIC_ONLY","games":len(z),"train_games":int(z.season.isin(["20222023","20232024","20242025"]).sum()),"test_games":z[z.season.isin(["20252026","20262027"])].groupby("season").size().to_dict(),"last_date":str(z.date.max().date()),"limitations":["No archived prices, no lineup or starting goalie forecasts, zero context in reconstructed baseline","Shot counts derived from goalie shots faced, not guaranteed official team SOG","Previous holdout periods already observed in project; not promotion evidence","Final score includes OT/SO credit; direct classes avoid simulated final ties"]}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== TEAM RESEARCH MANIFEST ===")
    print(json.dumps(meta,indent=2))
    print("=== TEAM RESEARCH METRICS ===")
    print(scores.to_csv(index=False))
    print("=== END TEAM RESEARCH ===")
if __name__=="__main__":
    main()
