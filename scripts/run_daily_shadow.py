"""Unified shadow-only slate runner consuming a previously frozen core board."""
import argparse,json,subprocess,sys
from pathlib import Path
import pandas as pd
from run_atg_pregame import digest,live_cutoff
from wshlx_nhl.daily_shadow import totals_board,goalie_board

def source_file(root,name):
    hits=list(root.rglob(name))
    if len(hits)!=1:raise ValueError(f"Expected exactly one {name}, found {len(hits)}")
    return hits[0]

def main():
    p=argparse.ArgumentParser()
    for k in ["target-date","core-dir","source-metadata","history","bundle","out"]:p.add_argument("--"+k,required=True)
    p.add_argument("--replay",action="store_true")
    a=p.parse_args();date=a.target_date;root=Path(a.core_dir);out=Path(a.out)
    if out.exists() and any(out.iterdir()):raise ValueError("Refuse overwrite")
    out.mkdir(parents=True,exist_ok=True)
    meta=json.loads(Path(a.source_metadata).read_text())
    if meta["expired"] or meta["name"]!="nhl-core-slate-"+date:raise ValueError("Wrong core artifact")
    files={k:source_file(root,date+"_"+v) for k,v in {"candidates":"core_candidates.csv","team":"team_metrics.json","goalie":"goalie_predictions.csv","research":"goalie_v03_research.csv"}.items()}
    c=pd.read_csv(files["candidates"],dtype={"date":str})
    if not c.date.eq(date).all():raise ValueError("Core date mismatch")
    first=None if a.replay else live_cutoff(date,c.game.unique())
    if first is not None and pd.Timestamp(meta["created_at"])>=first:raise ValueError("Core artifact uploaded after cutoff")
    config=json.loads(Path("config/atg_frozen_research_2026-11-25.json").read_text())
    for key,path in [("history",a.history),("bundle",a.bundle)]:
        if digest(path)!=config[key]["sha256"]:raise ValueError("Frozen artifact hash mismatch: "+key)
    t=totals_board(c,json.loads(files["team"].read_text())["team_goal_means"])
    g,e=goalie_board(pd.read_csv(files["goalie"],dtype={"goalie_id":str}),pd.read_csv(files["research"],dtype={"goalie_id":str}))
    if not g.date.eq(date).all():raise ValueError("Goalie date mismatch")
    t.to_csv(out/"totals_comparison.csv",index=False)
    g.to_csv(out/"goalie_comparison.csv",index=False)
    e.to_csv(out/"goalie_excluded.csv",index=False)
    cmd=[sys.executable,"scripts/run_atg_pregame.py","--history",a.history,"--bundle",a.bundle,"--candidates",str(files["candidates"]),"--target-date",date,"--out-dir",str(out/"atg")]
    if a.replay:cmd.append("--replay")
    subprocess.run(cmd,check=True)
    now=pd.Timestamp.now(tz="UTC")
    if first is not None and now>=first:raise ValueError("Missed pregame deadline")
    manifest={"date":date,"status":"RETROSPECTIVE_SMOKE_ONLY" if a.replay else "PREGAME_PENDING_ARTIFACT_VERIFICATION","core_run_id":meta["workflow_run"]["id"],"core_artifact_id":meta["id"],"core_artifact_created_at":meta["created_at"],"created_at_utc":now.isoformat(),"first_puck_utc":str(first) if first is not None else None,
              "source_hashes":{k:digest(v) for k,v in files.items()},"output_hashes":{str(p.relative_to(out)):digest(p) for p in out.rglob("*") if p.is_file()},
              "totals_pairs":int(len(t)/6),"matched_goalie_rows":int(len(g)/3),"excluded_goalie_rows":len(e),
              "totals_qualifying":t.groupby("model").qualifies.sum().astype(int).to_dict(),"goalie_qualifying":g.groupby("model").qualifies.sum().astype(int).to_dict(),
              "official_records_changed":False,"note":"No new official picks; totals 5.5/6.5 only; analytic control isolates tie effect from Monte Carlo noise; goalie half-lines matched only; ATG nested lock. Live requires independent final artifact timestamp."}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print("=== UNIFIED SHADOW MANIFEST ===");print(json.dumps(manifest,indent=2));print("=== END UNIFIED SHADOW ===")
if __name__=="__main__":main()
