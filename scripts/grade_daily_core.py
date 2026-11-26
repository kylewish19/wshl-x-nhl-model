"""Grade immutable official NHL locks and prepare review-only ledger updates.
No scoring model imports, no predictions regenerated, no repository writes.
"""
import argparse,json,hashlib,subprocess,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from assemble_core_slate import TEAM_NAMES
from build_goalie_features import parse_boxscore
from train_atg_game_shadow import parse_game
from run_atg_pregame import schedule
from grade_daily_shadow import outcomes,verify

CARDS={"top10":"TOP10_PROBABILITY","playable":"PLAYABLE_PRICE","playable_shadow_v0.3":"PLAYABLE_PRICE_SHADOW_V0_3"}
KEYS=["date","game","market","selection","line"]
def require(condition,message):
    if not condition:raise ValueError(message)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def find(root,name):
    hits=list(Path(root).rglob(name))
    require(len(hits)==1,"Missing or ambiguous frozen file "+name)
    return hits[0]
def read(root,date,name):return pd.read_csv(find(root,date+"_"+name+".csv"))
def verify_core(root,date,meta):
    require(not meta.get("expired") and meta["name"]=="nhl-core-slate-"+date,"Invalid core artifact")
    m=json.loads(find(root,date+"_lock_manifest.json").read_text())
    require(m["date"]==date and m["version"]=="v0.2.0" and m["status"]=="PREGAME_PENDING_ARTIFACT_VERIFICATION","Not a clean official lock")
    times=[pd.Timestamp(x) for x in (m["created_utc"],meta["created_at"],m["first_puck_utc"])]
    require(all(x.tzinfo is not None for x in times) and times[0]<=times[1]<times[2],"Invalid official upload cutoff")
    require(pd.Timestamp(m["history_cutoff"])<pd.Timestamp(date),"Invalid history cutoff")
    for name,h in m["hashes"].items():require(digest(find(root,name))==h,"Frozen core hash mismatch "+name)
    required=[date+"_"+n+".csv" for n in ["core_candidates","goalie_predictions",*CARDS,"atg_current_shadow","atg_consensus_shadow"]]
    require(set(required)<=set(m["hashes"]),"Missing required frozen hashes")
    return m

def fetch_outcomes(date,games):
    scheduled=schedule(date)
    by={g["awayTeam"]["abbrev"]+"@"+g["homeTeam"]["abbrev"]:g for g in scheduled}
    require(len(by)==len(scheduled) and games<=set(by),"Missing or duplicate scheduled game")
    require(all(by[g]["gameState"] in ("OFF","FINAL") for g in games),"All locked games must be final")
    def fetch(game):
        g=by[game];gid=int(g["id"]);season=str(g["season"])
        goalies,teams=parse_boxscore(gid,season);skaters=parse_game(gid,season)
        for rows in (goalies,teams,skaters):
            require(bool(rows) and all(str(x["date"])==date and int(x["game_id"])==gid for x in rows),"Wrong outcome date or game ID")
        require(len(goalies)==len(teams)==2 and all(x["starter_flag"] for x in goalies),"Unverified goalie starts")
        require({x["team"] for x in teams}==set(game.split("@"))=={x["team"] for x in goalies},"Outcome matchup mismatch")
        return teams,goalies,skaters
    with ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(fetch,sorted(games)))
    return tuple(pd.DataFrame([row for game in results for row in game[i]]) for i in range(3))

def settle(r,finals,starts,skaters,goalie_ids):
    game=r.game;a,h=game.split("@");f=finals.loc[game];x=int((f.total_goals-f.home_margin)/2);y=int((f.total_goals+f.home_margin)/2)
    m=r.market
    if m=="anytime_goal":
        require(pd.notna(r.player_id) and int(r.player_id)==r.player_id,"Unresolved ATG identity")
        q=skaters[(skaters.game==game)&(skaters.player_id==int(r.player_id))]
        if q.empty:return "VOID","DNP",""
        require(len(q)==1 and q.iloc[0].team==r.team,"ATG outcome team mismatch")
        v=int(q.iloc[0].goals)
        require(v>=0,"Invalid goal outcome")
        return ("WIN" if v else "LOSS"),f"{v} goals",""
    if m=="goalie_saves":
        gid=goalie_ids[(game,r.goalie_name,r.team)]
        require(str(gid).isdigit(),"Unresolved goalie identity")
        q=starts[(starts.game==game)&(starts.goalie_id==str(gid))]
        if q.empty:return "VOID","Nonstarter",""
        require(len(q)==1 and q.iloc[0].team==r.team,"Goalie outcome team mismatch")
        v=int(q.iloc[0].saves);actual=f"{v} saves"
        require(r.selection in (r.goalie_name+" Over",r.goalie_name+" Under"),"Invalid goalie side")
        delta=v-r.line
        if delta==0:return "PUSH",actual,""
        win=(delta>0)==r.selection.endswith(" Over")
    elif m=="total":
        require(r.selection in ("Over","Under"),"Invalid total side")
        actual=f"{a} {x}-{y} {h}";delta=x+y-r.line
        if delta==0:return "PUSH",actual,""
        win=(delta>0)==(r.selection=="Over")
    elif m in ("moneyline","spread"):
        require(r.selection in (TEAM_NAMES[a],TEAM_NAMES[h]),"Invalid team selection")
        actual=f"{a} {x}-{y} {h}";delta=(x-y if r.selection==TEAM_NAMES[a] else y-x)+(r.line if m=="spread" else 0)
        if delta==0:return "PUSH",actual,""
        win=delta>0
    else:raise ValueError("Inactive market in card: "+m)
    return ("WIN" if win else "LOSS"),actual,""

def grade_card(card,settler,pcol):
    d=card.copy()
    require(not d.duplicated(KEYS).any(),"Duplicate frozen selection")
    require(d[pcol].between(0,1).all() and d.odds_american.abs().ge(100).all(),"Invalid frozen probability or price")
    rows=[settler(r) for r in d.itertuples()]
    d[["result","actual","notes"]]=pd.DataFrame(rows,index=d.index,columns=["result","actual","notes"])
    d["profit_units"]=np.where(d.result.eq("WIN"),np.where(d.odds_american>0,d.odds_american/100,100/-d.odds_american),np.where(d.result.eq("LOSS"),-1.,0.))
    s=d[d.result.isin(["WIN","LOSS"])];n=len(s);w=int(s.result.eq("WIN").sum());net=float(s.profit_units.sum())
    return d,dict(wins=w,losses=n-w,voids=int(d.result.eq("VOID").sum()),pushes=int(d.result.eq("PUSH").sum()),hit_rate=w/n if n else None,expected_wins=float(s[pcol].sum()),brier=float(((s[pcol]-s.result.eq("WIN").astype(int))**2).mean()) if n else None,profit_units=net,roi=net/n if n else None)

def season_update(prior,date,stats):
    require(not prior.duplicated(["date","cohort"]).any(),"Duplicate season row")
    require(not prior.date.eq(date).any(),"Date already graded")
    daily=prior[prior.date.ne("CUMULATIVE")].copy();cumulative=prior[prior.date.eq("CUMULATIVE")].copy()
    rows=[]
    for name,cohort in CARDS.items():
        s=stats[name];rows.append(dict(date=date,cohort=cohort,wins=s["wins"],losses=s["losses"],hit_rate=s["hit_rate"],expected_wins=s["expected_wins"],brier=s["brier"],profit_units=None if name=="top10" else s["profit_units"],roi=None if name=="top10" else s["roi"]))
        old=cumulative[cumulative.cohort.eq(cohort)]
        require(len(old)==1,"Missing cumulative cohort")
        old=old.iloc[0];oldn=int(old.wins+old.losses);n=s["wins"]+s["losses"];total=oldn+n;w=int(old.wins)+s["wins"];l=total-w
        net=None if name=="top10" else float(old.profit_units)+s["profit_units"]
        brier=((float(old.brier)*oldn if oldn else 0)+(s["brier"]*n if n else 0))/total if total else None
        vals=dict(wins=w,losses=l,hit_rate=w/total if total else None,expected_wins=float(old.expected_wins)+s["expected_wins"],brier=brier,profit_units=net,roi=net/total if total and net is not None else None)
        for k,v in vals.items():cumulative.loc[cumulative.cohort.eq(cohort),k]=v
    return pd.concat([daily,pd.DataFrame(rows),cumulative],ignore_index=True)

def main():
    ap=argparse.ArgumentParser()
    for k in ("date","core-dir","core-metadata","out"):ap.add_argument("--"+k,required=True)
    ap.add_argument("--research-dir");ap.add_argument("--research-metadata")
    ap.add_argument("--review",action="store_true")
    a=ap.parse_args();date=a.date;root=Path(a.core_dir);out=Path(a.out)
    require(not out.exists() or not any(out.iterdir()),"Refuse overwrite")
    prior=pd.read_csv("data/results/season_summary.csv")
    require(prior.date.eq(date).any()==a.review,"Use review only for already graded dates")
    if a.review:require(date=="2026-11-25","Only original Nov25 verification supported")
    cm=json.loads(Path(a.core_metadata).read_text());m=verify_core(root,date,cm)
    c=read(root,date,"core_candidates");g=read(root,date,"goalie_predictions")
    require(c.date.eq(date).all() and not c.duplicated(KEYS).any(),"Invalid frozen candidate board")
    games=set(c.game);team,goalie,skater=fetch_outcomes(date,games)
    f,starts,skaters=outcomes(team,goalie,skater,date,games)
    require(not g.duplicated(["game","goalie_name","team"]).any(),"Duplicate frozen goalie identity")
    ids={(x.game,x.goalie_name,x.team):str(int(x.goalie_id)) for x in g.itertuples() if pd.notna(x.goalie_id)}
    settler=lambda r:settle(r,f.set_index("game"),starts,skaters,ids)
    out.mkdir(parents=True,exist_ok=True);official=out/"official";official.mkdir()
    private=out/"private_outcomes";private.mkdir()
    for n,d in zip(("teams","goalies","skaters"),(team,goalie,skater)):d.to_parquet(private/(n+".parquet"),index=False)
    stats={}
    for name in CARDS:
        card=read(root,date,name)
        pcol="calibrated_probability" if name.endswith("v0.3") else "model_probability"
        require(card.date.eq(date).all(),"Wrong card date")
        if name=="top10":require(len(card)==min(10,int(c.active.eq(1).sum())),"Wrong Top10 coverage")
        cols=KEYS+["odds_american","model_probability"]
        z=card[cols].merge(c[cols+["active"]],on=KEYS,how="left",suffixes=("","_source"),validate="one_to_one")
        require(z.active.eq(1).all() and z.odds_american.eq(z.odds_american_source).all() and np.allclose(z.model_probability,z.model_probability_source,rtol=0,atol=1e-12),"Card differs from frozen candidate")
        d,s=grade_card(card,settler,pcol);stats[name]=s
        cols=KEYS+["odds_american","model_probability"]+([pcol] if pcol!="model_probability" else [])+["result"]+([] if name=="top10" else ["profit_units"])+["actual","notes"]
        d=d[cols];d.to_csv(official/(date+"_"+name+"_graded.csv"),index=False)
        if a.review:
            old=pd.read_csv("data/results/"+date+"_"+name+"_graded.csv")
            pd.testing.assert_frame_equal(d.fillna(""),old.fillna(""),check_dtype=False,rtol=1e-10,atol=1e-10)
        print("CARD "+name+" "+json.dumps(s))
    blend=read(root,date,"atg_current_shadow");blend=blend[blend.active.eq(1)&blend.shadow_probability.notna()].sort_values("shadow_probability",ascending=False).head(10)
    b,bs=grade_card(blend,settler,"shadow_probability")
    consensus=read(root,date,"atg_consensus_shadow")
    q,qs=grade_card(consensus,settler,"consensus_probability")
    b.to_csv(official/"atg_blend_top10_graded.csv",index=False);q.to_csv(official/"atg_consensus_graded.csv",index=False)
    if a.review:
        old=json.loads(Path("data/results/"+date+"_grading_summary.json").read_text())["official"]
        for name,s in stats.items():
            for k,v in old[name].items():require(np.isclose(s[k],v,rtol=1e-10,atol=1e-10),"Replay metric mismatch")
    else:
        season_update(prior,date,stats).to_csv(official/"proposed_season_summary.csv",index=False,float_format="%.4f")
    f.to_csv(official/"final_scores.csv",index=False)
    research_status="NOT_SUPPLIED"
    if a.research_dir:
        rm=json.loads(Path(a.research_metadata).read_text());rroot=Path(a.research_dir)
        r,_,_=verify(rroot,rm,False)
        require(r["date"]==date and r["core_run_id"]==cm["workflow_run"]["id"] and r["core_artifact_id"]==cm["id"],"Research refers to a different core lock")
        require(pd.Timestamp(r["first_puck_utc"])==pd.Timestamp(m["first_puck_utc"]),"Research cutoff mismatch")
        for k,n in {"candidates":"core_candidates.csv","team":"team_metrics.json","goalie":"goalie_predictions.csv","research":"goalie_v03_research.csv"}.items():
            require(digest(find(root,date+"_"+n))==r["source_hashes"][k],"Research source hash mismatch "+k)
        ledger=Path("data/results/prospective_shadow_ledger.csv")
        if a.review:
            prior_shadow=pd.read_csv(ledger);ledger=private/"prior_shadow.csv"
            prior_shadow[prior_shadow.date.ne(date)].to_csv(ledger,index=False)
        cmd=[sys.executable,"scripts/grade_daily_shadow.py","--lock-dir",str(rroot),"--artifact-metadata",a.research_metadata,"--team-games",str(private/"teams.parquet"),"--goalie-features",str(private/"goalies.parquet"),"--skater-games",str(private/"skaters.parquet"),"--ledger",str(ledger),"--out",str(out/"research")]
        subprocess.run(cmd,check=True)
        if a.review:
            actual=pd.read_csv(out/"research/summary.csv");old=prior_shadow[prior_shadow.date.eq(date)]
            k=["market","model"];cols=[x for x in actual if x in old]
            pd.testing.assert_frame_equal(actual[cols].sort_values(k).reset_index(drop=True),old[cols].sort_values(k).reset_index(drop=True),check_dtype=False,rtol=1e-9,atol=1e-10)
            # No proposed ledger from a duplicate review may be promoted.
            for p in (out/"research").glob("*ledger.csv"):p.unlink()
        research_status="VERIFIED_FROZEN_REVIEW" if a.review else "PROPOSED_LEDGER_REVIEW"
    meta=dict(date=date,status="FROZEN_SOURCE_REVIEW_ONLY" if a.review else "PENDING_LEDGER_REVIEW",source_core_run=cm["workflow_run"]["id"],source_core_artifact=cm["id"],core_lock_hash=digest(find(root,date+"_lock_manifest.json")),games=len(games),official=stats,blend_top10=bs,atg_consensus=qs,research_status=research_status,canonical_records_changed=False,prior_season_sha256=digest("data/results/season_summary.csv"),outcome_hashes={p.name:digest(p) for p in private.glob("*.parquet")},output_hashes={str(p.relative_to(out)):digest(p) for p in out.rglob("*") if p.is_file() and private not in p.parents})
    (out/"manifest.json").write_text(json.dumps(meta,indent=2,allow_nan=False))
    print("=== REUSABLE GRADING ===");print(json.dumps(meta,indent=2,allow_nan=False));print("=== END REUSABLE GRADING ===")
if __name__=="__main__":main()
