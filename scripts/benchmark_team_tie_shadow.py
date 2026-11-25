import argparse,json
from pathlib import Path
import pandas as pd
from wshlx_nhl.team_market_shadow import build_team_features
from wshlx_nhl.team_tie_shadow import benchmark

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--team-games",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    raw=pd.read_parquet(a.team_games)
    assert raw.game_id.nunique()==6945 and pd.to_datetime(raw.date).max()<pd.Timestamp("2026-11-25")
    z=build_team_features(raw)
    metrics,preds,factor=benchmark(z)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    metrics.to_csv(out/"metrics.csv",index=False)
    preds.to_parquet(out/"predictions.parquet",index=False)
    meta={"status":"HISTORICAL_DIAGNOSTIC_ONLY","games":len(z),"calibration_season":"2024-25","factor":factor,
          "limitations":["No regulation score labels in archive; tie resolution is mathematical assumption, not validated OT frequency","No odds or pregame goalie context","Already viewed evaluation seasons; not independent promotion evidence"]}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== TIE MANIFEST ===")
    print(json.dumps(meta,indent=2))
    print("=== TIE METRICS ===")
    print(metrics.to_csv(index=False))
    print("=== END TIE ===")
if __name__=="__main__":
    main()
