"""Reusable official v0.2.0 runner. Replay is never a clean lock."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from preflight_slate import validate
from run_atg_pregame import live_cutoff, schedule
from build_goalie_features import parse_boxscore, add_goalie_features
from run_skater_transition_board import norm_name
import run_goalie_board as goalie
import run_goalie_v03_board as goalie3

ARCHIVE_DATE="2026-11-24"
HASHES={"team":"8a64b279789ed438ee42df1f9ee2f43936405b5113c3ba5c2422eef6498e6a16",
        "goalie":"b660defbe324f39cfc17868636ab95bcfbe962157f7d28deee2e1684b2e54a6c"}
KEY=["date","game","market","selection","line"]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def find(root,name):
    hits=list(Path(root).rglob(name))
    if len(hits)!=1:raise ValueError(f"Expected exactly one {name}, found {len(hits)}")
    return hits[0]
def check(flag,msg):
    if not flag:raise ValueError(msg)

def inputs(date,root):
    root=Path(root)
    return {"team":root/"inputs"/f"{date}_team_board.csv",
            "core":root/"odds"/f"{date}_core_FanDuel.csv",
            "atg":root/"inputs"/f"{date}_atg_board.csv",
            "goalie":root/"odds"/f"{date}_goalie_saves_FanDuel.csv",
            "review":root/"context"/f"{date}_core_review.json"}

def validate_review(date,review,atg):
    check(review.get("date")==date and review.get("reviewed") is True and bool(review.get("source_note")),"Reviewed date-specific context required")
    scratches=review.get("scratches",[])
    check(isinstance(scratches,list) and len(set(scratches))==len(scratches) and all(isinstance(s,str) and s in set(atg.player_name) for s in scratches),"Invalid scratch list")
    corrections=review.get("corrections",[])
    keys=set(zip(atg.game,atg.player_name))
    mapping={}
    for c in corrections:
        k=(c["game"],c["player_name"])
        check(k in keys and k not in mapping,"Invalid or duplicate correction key")
        check(set(c)<= {"game","player_name","team","snapshot_name","player_id","position"},"Unsupported correction field")
        if "team" in c:check(c["team"] in k[0].split("@"),"Correction outside matchup")
        if "player_id" in c:check(isinstance(c["player_id"],int) and c["player_id"]>0,"Invalid corrected player ID")
        mapping[k]=c
    return mapping,scratches

def resolve_atg(board,snapshot,corrections):
    s=snapshot.copy();s["key"]=s.player_name.map(norm_name)
    rows=[]
    for r in board.to_dict("records"):
        c=corrections.get((r["game"],r["player_name"]),{})
        name=r["player_name"];team=c.get("team",r["team"])
        hits=s[s.team.eq(team)]
        if "player_id" in c:
            hits=hits[hits.player_id.eq(c["player_id"])]
        else:
            hits=hits[hits.key.eq(norm_name(c.get("snapshot_name",name)))]
            if hits.empty and "snapshot_name" in c:
                hits=s[s.team.eq(team)&s.key.eq(norm_name(name))]
        if "position" in c:hits=hits[hits.position.eq(c["position"])]
        row={**r,"listed_team":r["team"],"resolved_team":team,"team":team}
        if len(hits)!=1:
            row.update(player_id=None,expected_count=None,model_probability=None,model_basis="unresolved_identity")
        else:
            p=hits.iloc[0]
            check(np.isfinite(p.official_goal_prob) and 0<=p.official_goal_prob<=1,"Invalid snapshot probability")
            row.update(player_id=int(p.player_id),expected_count=float(p.official_goal_mu),model_probability=float(p.official_goal_prob),model_basis=p.official_goal_basis)
        rows.append(row)
    out=pd.DataFrame(rows)
    check(not out[out.player_id.notna()].duplicated(["game","player_id"]).any(),"Duplicate resolved player")
    return out

def history(archive,date,work,replay):
    paths={k:find(archive,f"{ARCHIVE_DATE}_{'team_games' if k=='team' else 'goalie_features'}.parquet") for k in HASHES}
    for k,p in paths.items():check(digest(p)==HASHES[k],"Archive hash mismatch "+k)
    t,g=(pd.read_parquet(paths[k]) for k in ("team","goalie"))
    target=pd.Timestamp(date);last=pd.Timestamp(ARCHIVE_DATE)
    for d in (t,g):
        d["date"]=pd.to_datetime(d.date)
        check(d.date.max()==last and len(d)==13890 and not d.duplicated(["game_id","team"]).any(),"Archive coverage mismatch")
    check(target>last,"Runner starts after original archive cutoff")
    jobs={}
    if not replay:
        for day in pd.date_range(last+pd.Timedelta(days=1),target-pd.Timedelta(days=1)):
            for m in schedule(day.date().isoformat()):
                if m.get("gameScheduleState")=="PPD":continue
                check(m["gameState"] in ("OFF","FINAL"),"Prior scheduled game not final")
                gid=int(m["id"]);check(gid not in jobs,"Duplicate scheduled game")
                jobs[gid]=(str(m["season"]),day,m["awayTeam"]["abbrev"],m["homeTeam"]["abbrev"])
    else:check(date=="2026-11-25","Only verified Nov25 replay supported")
    def fetch(item):
        gid,(season,day,a,h)=item
        gs,ts=parse_boxscore(gid,season)
        for rows in (gs,ts):
            check(len(rows)==2 and {x["team"] for x in rows}=={a,h},"Incomplete incremental boxscore")
            check(all(int(x["game_id"])==gid and pd.Timestamp(x["date"])==day for x in rows),"Wrong incremental identity/date")
        check(all(x["starter_flag"] for x in gs),"Unverified incremental starter")
        check(ts[0]["goals_for"]!=ts[1]["goals_for"],"Unresolved final score")
        return gs,ts
    if jobs:
        with ThreadPoolExecutor(max_workers=8) as ex:res=list(ex.map(fetch,jobs.items()))
        extra_t=pd.DataFrame([x for _,ts in res for x in ts]);extra_g=pd.DataFrame([x for gs,_ in res for x in gs])
        for x in (extra_t,extra_g):x["date"]=pd.to_datetime(x.date)
        t=pd.concat([t,extra_t],ignore_index=True)
        # Compute lagged features for newly appended rows only; keep frozen old features byte-values.
        base=list(extra_g.columns)
        raw=pd.concat([g[base],extra_g],ignore_index=True)
        new=add_goalie_features(raw,t)
        g=pd.concat([g,new[new.game_id.isin(jobs)]],ignore_index=True)
    for d in (t,g):
        check(d.date.lt(target).all() and not d.duplicated(["game_id","team"]).any(),"Invalid pregame history")
    check(set(zip(t.game_id,t.team))==set(zip(g.game_id,g.team)),"History team/goalie mismatch")
    check(t.game_id.nunique()==6945+len(jobs),"History game count mismatch")
    tp=work/"team.parquet";gp=work/"goalie.parquet"
    t.to_parquet(tp,index=False);g.to_parquet(gp,index=False)
    return tp,gp,{"archive_date":ARCHIVE_DATE,"archive_hashes":HASHES,"additional_games":len(jobs),"games":int(t.game_id.nunique()),"last_date":str(t.date.max().date()),"prepared_hashes":{"team":digest(tp),"goalie":digest(gp)}}

def run_script(name,**kwargs):
    args=[sys.executable,"scripts/"+name+".py"]
    for k,v in kwargs.items():
        args.append("--"+k.replace("_","-"))
        if v is not True:args.append(str(v))
    subprocess.run(args,check=True)

def call_main(module,kwargs):
    old=sys.argv
    try:
        sys.argv=[module.__name__+".py"]
        for k,v in kwargs.items():sys.argv.extend(["--"+k.replace("_","-"),str(v)])
        module.main()
    finally:sys.argv=old

def parity(out,original,date):
    reports={}
    for kind in ("core_candidates","top10","playable","playable_shadow_v0.3"):
        a=pd.read_csv(out/f"{date}_{kind}.csv");b=pd.read_csv(find(original,f"{date}_{kind}.csv"))
        cols=KEY+["model_probability","odds_american","active"]
        if "rank" in b:cols+=["rank"]
        if kind=="playable_shadow_v0.3":cols+=["calibrated_probability"]
        pd.testing.assert_frame_equal(a[cols].reset_index(drop=True),b[cols].reset_index(drop=True),check_dtype=False,rtol=1e-9,atol=1e-10)
        reports[kind]=len(a)
    return reports

def main():
    ap=argparse.ArgumentParser()
    for k in ("date","archive","out"):ap.add_argument("--"+k,required=True)
    ap.add_argument("--data-root",default="data")
    ap.add_argument("--replay-core")
    a=ap.parse_args();date=a.date;out=Path(a.out);replay=bool(a.replay_core)
    check(pd.Timestamp(date).date().isoformat()==date,"Invalid date")
    check(not out.exists() or not any(out.iterdir()),"Refuse overwrite")
    out.mkdir(parents=True,exist_ok=True);work=out/"private_work";work.mkdir()
    paths=inputs(date,a.data_root);frames={k:pd.read_csv(paths[k]) for k in ("team","core","atg","goalie")}
    pre=validate(date,**frames)
    review=json.loads(paths["review"].read_text());corrections,scratches=validate_review(date,review,frames["atg"])
    first=None if replay else live_cutoff(date,frames["team"].game)
    def cutoff():
        if first is not None:check(pd.Timestamp.now(tz="UTC")<first,"Pregame cutoff exceeded")
    def op(n):return out/f"{date}_{n}"
    pre["input_hashes"]={k:digest(p) for k,p in paths.items()};op("preflight.json").write_text(json.dumps(pre,indent=2))
    tp,gp,hmeta=history(a.archive,date,work,replay);cutoff()
    if replay:
        snap=find(a.archive,"skater_snapshot_2026-11-24.csv")
        meta=json.loads(find(a.archive,"resume_refresh_summary.json").read_text())
        check(meta["data_cutoff_target_date"]==date,"Replay snapshot cutoff mismatch")
        s=pd.read_csv(snap)
        # Replay uses the exact original resolved goalie identities, no current-roster lookup.
        ids=pd.read_csv(find(a.replay_core,date+"_goalie_predictions.csv"),dtype={"goalie_id":str})
        idmap={(x.team,goalie._name_key(x.goalie_name)):x.goalie_id for x in ids.itertuples()}
        goalie.resolve_goalie=lambda starts,name,team:idmap.get((team,goalie._name_key(name)))
    else:
        from build_resume_snapshot import build_skater_snapshot
        s,meta=build_skater_snapshot()
        cutoff()
    snap=work/"snapshot.csv";s.to_csv(snap,index=False)
    check(not s.duplicated(["player_id","team"]).any(),"Duplicate snapshot identity")
    run_script("run_team_goal_board",team_games=tp,board=paths["team"],target_date=date,predictions=op("team_predictions.csv"),metrics=op("team_metrics.json"))
    cutoff()
    gargs=dict(features=gp,team_games=tp,odds=paths["goalie"],target_date=date,predictions=op("goalie_predictions.csv"),metrics=op("goalie_metrics.json"))
    call_main(goalie,{**gargs,"shadow_model":work/"goalie02.joblib","official_model":work/"goalie01.joblib"})
    g=pd.read_csv(gargs["predictions"],dtype={"goalie_id":str})
    check(len(g)==len(frames["goalie"]) and g.goalie_id.str.fullmatch(r"\d+").fillna(False).all(),"Unresolved goalie identity; review before lock")
    cutoff()
    # Official artifacts are locked independently; research failure is explicit, never a substitute.
    atg=resolve_atg(frames["atg"],s,corrections)
    atg.to_csv(op("atg_predictions.csv"),index=False)
    invalid=atg.model_probability.isna()
    atg[invalid].to_csv(op("identity_excluded.csv"),index=False)
    op("atg_metrics.json").write_text(json.dumps({"snapshot_hash":digest(snap),"snapshot_metadata":meta,"scored":int((~invalid).sum()),"unresolved":atg.loc[invalid,"player_name"].tolist(),"scratches":scratches,"corrections":review["corrections"]},indent=2,default=str))
    check((~invalid).any(),"No resolved ATG players")
    run_script("assemble_core_slate",team_pred=op("team_predictions.csv"),core_odds=paths["core"],atg_pred=op("atg_predictions.csv"),goalie_pred=op("goalie_predictions.csv"),skater_snapshot=snap,date=date,exclude_atg=",".join(scratches),explicit_scratches_only=True,out=op("core_candidates.csv"),shadow_atg_out=op("atg_current_shadow.csv"))
    c=pd.read_csv(op("core_candidates.csv"));c=c[c.model_probability.notna()].copy()
    check(len(c)==len(frames["core"])+len(atg)-int(invalid.sum())+2*len(g),"Candidate coverage mismatch")
    check(c.model_probability.between(0,1).all() and c.odds_american.abs().ge(100).all() and not c.duplicated(KEY).any(),"Invalid candidate board")
    c.to_csv(op("core_candidates.csv"),index=False)
    # Consensus is a research output; exclude scratches and unresolved players.
    active=atg[~invalid & ~atg.player_name.isin(scratches)]
    active.to_csv(work/"active_atg.csv",index=False)
    run_script("build_atg_consensus_shadow",official_atg=work/"active_atg.csv",skater_snapshot=snap,output=op("atg_consensus_shadow.csv"))
    run_script("make_cards",candidates=op("core_candidates.csv"),top10_out=op("top10.csv"),playable_out=op("playable.csv"),shadow_v03_out=op("playable_shadow_v0.3.csv"),shadow_target_date=date)
    cutoff()
    research_error=None
    try:
        call_main(goalie3,{**gargs,"predictions":op("goalie_v03_research.csv"),"metrics":op("goalie_v03_research_metrics.json"),"identity_board":op("goalie_predictions.csv"),"model":work/"goalie03.joblib"})
    except Exception as e:
        research_error=str(e)
        for n in ("goalie_v03_research.csv","goalie_v03_research_metrics.json"):op(n).unlink(missing_ok=True)
    cutoff()
    report=parity(out,a.replay_core,date) if replay else None
    manifest={"date":date,"version":"v0.2.0","status":"RETROSPECTIVE_SMOKE_ONLY" if replay else "PREGAME_PENDING_ARTIFACT_VERIFICATION","created_utc":pd.Timestamp.now(tz="UTC").isoformat(),"first_puck_utc":str(first) if first is not None else None,"history_cutoff":hmeta["last_date"],"history":hmeta,"source_run":45713367700,"input_hashes":pre["input_hashes"],"hashes":{p.name:digest(p) for p in out.glob(date+"_*.csv")},"research_error":research_error,"replay_parity":report}
    op("lock_manifest.json").write_text(json.dumps(manifest,indent=2))
    for kind in ("top10","playable","playable_shadow_v0.3"):
        print("=== "+kind.upper()+" ===");print(op(kind+".csv").read_text(),end="")
    print("=== REUSABLE CORE MANIFEST ===");print(json.dumps(manifest,indent=2));print("=== END REUSABLE CORE ===")
if __name__=="__main__":main()
