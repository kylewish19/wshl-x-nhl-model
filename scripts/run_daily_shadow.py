"""Unified shadow-only slate runner consuming a previously frozen core board."""
import argparse,json,subprocess,sys
from pathlib import Path
import pandas as pd
import joblib
from concurrent.futures import ThreadPoolExecutor
from assemble_core_slate import TEAM_NAMES
from build_goalie_features import parse_boxscore
from run_atg_pregame import schedule
from wshlx_nhl.margin_consensus_shadow import pregame_margin_features,spread_board,goalie_consensus
from run_atg_pregame import digest,live_cutoff
from wshlx_nhl.daily_shadow import totals_board,goalie_board

def source_file(root,name):
    hits=list(root.rglob(name))
    if len(hits)!=1:raise ValueError(f"Expected exactly one {name}, found {len(hits)}")
    return hits[0]

def margin_history(path,date):
    raw=pd.read_parquet(path)
    if digest(path)!="8a64b279789ed438ee42df1f9ee2f43936405b5113c3ba5c2422eef6498e6a16":
        raise ValueError("Original team archive hash mismatch")
    target=pd.Timestamp(date)
    last=pd.to_datetime(raw.date).max().normalize()
    jobs={}
    for day in pd.date_range(last+pd.Timedelta(days=1),target-pd.Timedelta(days=1)):
        for g in schedule(day.date().isoformat()):
            if g.get("gameScheduleState")=="PPD":continue
            if g["gameState"] not in ("OFF","FINAL"):raise ValueError("Nonfinal prior team game")
            jobs[int(g["id"])]=str(g["season"])
    def fetch(item):
        gid,season=item
        _,rows=parse_boxscore(gid,season)
        if len(rows)!=2:raise ValueError("Incomplete prior team boxscore")
        return rows
    if jobs:
        with ThreadPoolExecutor(max_workers=8) as ex:
            rows=[r for game in ex.map(fetch,jobs.items()) for r in game]
        raw=pd.concat([raw,pd.DataFrame(rows)],ignore_index=True)
    raw=raw[pd.to_datetime(raw.date)<target].copy()
    if raw.duplicated(["game_id","team"]).any():raise ValueError("Duplicate history")
    return raw

def main():
    p=argparse.ArgumentParser()
    for k in ["target-date","core-dir","source-metadata","history","bundle","out"]:p.add_argument("--"+k,required=True)
    p.add_argument("--replay",action="store_true")
    p.add_argument("--team-history",required=True)
    p.add_argument("--margin-bundle",required=True)
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
    history=margin_history(a.team_history,date)
    features=pregame_margin_features(history,c.game.unique(),date)
    margin=joblib.load(a.margin_bundle)["margin_class"]
    spreads=spread_board(c,json.loads(files["team"].read_text())["team_goal_means"],features,margin,TEAM_NAMES)
    consensus=goalie_consensus(g)
    spreads.to_csv(out/"spread_comparison.csv",index=False)
    consensus.to_csv(out/"goalie_consensus.csv",index=False)
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
              "spread_pairs":int(len(spreads)/6),"spread_qualifying":spreads.groupby("model").qualifies.sum().astype(int).to_dict(),
              "goalie_consensus_counts":{k:int(consensus[k].sum()) for k in ["unanimous_direction","unanimous_v03_gate","unanimous_all_gates"]},
              "margin_history_sha256":digest(a.team_history),"margin_bundle_sha256":digest(a.margin_bundle),"margin_history_last_date":str(pd.to_datetime(history.date).max().date()),
              "official_records_changed":False,"note":"No new official picks; totals 5.5/6.5 only; analytic control isolates tie effect from Monte Carlo noise; goalie half-lines matched only; ATG nested lock. Live requires independent final artifact timestamp."}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print("=== UNIFIED SHADOW MANIFEST ===");print(json.dumps(manifest,indent=2));print("=== END UNIFIED SHADOW ===")
if __name__=="__main__":main()
