"""Grade the immutable unified research artifact using a dated outcome archive."""
import argparse,json
from pathlib import Path
import pandas as pd
from run_atg_pregame import digest
from grade_atg_pregame import load_lock
from wshlx_nhl.atg_grading import grade_matched
from wshlx_nhl.daily_shadow_grading import grade_totals,grade_goalies,cumulative
from wshlx_nhl.margin_consensus_shadow import grade_spreads,grade_consensus

def verify(root,artifact,replay):
    m=json.loads((root/"manifest.json").read_text())
    if artifact.get("expired") or artifact["name"]!="unified-daily-shadows-"+m["date"]:
        raise ValueError("Invalid unified artifact")
    for name,sha in m["output_hashes"].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path)!=sha:raise ValueError("Frozen hash mismatch")
    nested=json.loads((root/"atg/manifest.json").read_text())
    if nested["target_date"]!=m["date"] or nested["status"]!=m["status"]:raise ValueError("Nested lock mismatch")
    if replay:
        if m["status"]!="RETROSPECTIVE_SMOKE_ONLY":raise ValueError("Not replay")
        cohort="RETROSPECTIVE_SMOKE_ONLY"
    else:
        if m["status"]!="PREGAME_PENDING_ARTIFACT_VERIFICATION":raise ValueError("Not a prospective lock")
        stamps=[pd.Timestamp(x) for x in [m["core_artifact_created_at"],nested["created_at_utc"],m["created_at_utc"],artifact["created_at"],m["first_puck_utc"]]]
        if any(x.tzinfo is None for x in stamps) or not stamps[0]<=stamps[1]<=stamps[2]<=stamps[3]<stamps[4]:
            raise ValueError("Invalid pregame timestamp chain")
        if pd.Timestamp(nested["first_puck_utc"])!=stamps[4]:raise ValueError("Nested cutoff mismatch")
        cohort="CLEAN_SHADOW_PREGAME"
    # The nested lock is hash-bound to the parent; validate its own hashes using
    # the independently verified parent upload timestamp, not a fabricated time.
    _,p,status=load_lock(root/"atg",{**artifact,"name":"atg-pregame-shadow-output"},replay)
    if status!=cohort:raise ValueError("Nested cohort mismatch")
    return m,p,cohort

def outcomes(team,goalie,skater,date,games):
    def day(x):
        return x[pd.to_datetime(x.date).dt.strftime("%Y-%m-%d").eq(date)].copy()
    t=day(team);g=day(goalie);s=day(skater)
    if t.duplicated(["game_id","team"]).any():raise ValueError("Duplicate final team")
    a=t[t.is_home.eq(0)];h=t[t.is_home.eq(1)]
    p=a.merge(h,on="game_id",suffixes=("_a","_h"),validate="one_to_one")
    p["game"]=p.team_a+"@"+p.team_h
    p=p[p.game.isin(games)].copy()
    if set(p.game)!=set(games) or p.game.duplicated().any():raise ValueError("Missing final games")
    if not (p.team_a.eq(p.opponent_h)&p.team_h.eq(p.opponent_a)&p.goals_for_a.eq(p.goals_against_h)&p.goals_for_h.eq(p.goals_against_a)&p.goals_for_a.ne(p.goals_for_h)).all():
        raise ValueError("Invalid final scores")
    finals=p[["game_id","game"]].assign(date=date,total_goals=p.goals_for_a+p.goals_for_h,home_margin=p.goals_for_h-p.goals_for_a)
    g=g.merge(finals[["game_id","game"]],on="game_id",validate="many_to_one")
    s=s.merge(finals[["game_id","game"]],on="game_id",validate="many_to_one")
    if not g.groupby("game_id").size().reindex(p.game_id).eq(2).all() or not g.starter_flag.eq(True).all():
        raise ValueError("Unverified starting goalie outcomes")
    if not s.groupby(["game_id","team"]).size().ge(10).all() or not s.groupby("game_id").team.nunique().reindex(p.game_id).eq(2).all():
        raise ValueError("Incomplete skater outcomes")
    if s.duplicated(["game_id","player_id"]).any() or g.duplicated(["game_id","goalie_id"]).any():raise ValueError("Duplicate identity")
    if g.saves.isna().any() or g.saves.lt(0).any() or g.saves.gt(g.shots_against).any():raise ValueError("Invalid save outcomes")
    for frame in (g,s):
        if not all(team in game.split("@") for team,game in zip(frame.team,frame.game)):raise ValueError("Outcome team mismatch")
        frame["date"]=date
    g["goalie_id"]=g.goalie_id.astype(str)
    return finals,g,s

def main():
    ap=argparse.ArgumentParser()
    for k in ["lock-dir","artifact-metadata","team-games","goalie-features","skater-games","out"]:ap.add_argument("--"+k,required=True)
    ap.add_argument("--ledger");ap.add_argument("--replay",action="store_true")
    a=ap.parse_args();root=Path(a.lock_dir);out=Path(a.out)
    if out.exists() and any(out.iterdir()):raise ValueError("Refuse overwrite")
    artifact=json.loads(Path(a.artifact_metadata).read_text())
    m,p,cohort=verify(root,artifact,a.replay)
    t=pd.read_csv(root/"totals_comparison.csv");g=pd.read_csv(root/"goalie_comparison.csv",dtype={"goalie_id":str})
    if len(t)!=6*m["totals_pairs"] or len(g)!=3*m["matched_goalie_rows"]:raise ValueError("Manifest coverage mismatch")
    if not t.date.eq(m["date"]).all() or not g.date.eq(m["date"]).all():raise ValueError("Board date mismatch")
    games=set(t.game)|set(g.game)|set(p.game)
    finals,starts,skaters=outcomes(pd.read_parquet(a.team_games),pd.read_parquet(a.goalie_features),pd.read_parquet(a.skater_games),m["date"],games)
    td,ts=grade_totals(t,finals);gd,gs=grade_goalies(g,starts,finals)
    ad,ats=grade_matched(p,skaters,list(zip(finals.date,finals.game)))
    ats.insert(0,"market","anytime_goal")
    extras=[]
    if "spread_pairs" in m:
        b=pd.read_csv(root/"spread_comparison.csv")
        if len(b)!=6*m["spread_pairs"] or not b.date.eq(m["date"]).all():raise ValueError("Spread lock coverage")
        sd,ss=grade_spreads(b,finals)
        extras.append(("spreads_graded",sd))
    else:ss=ts.iloc[:0].copy()
    if "goalie_consensus_counts" in m:
        b=pd.read_csv(root/"goalie_consensus.csv",dtype={"goalie_id":str})
        if not b.date.eq(m["date"]).all():raise ValueError("Consensus date mismatch")
        for k,v in m["goalie_consensus_counts"].items():
            if int(b[k].sum())!=v:raise ValueError("Consensus lock coverage")
        cd,cs=grade_consensus(b,starts,finals)
        cs.insert(0,"date",m["date"]);cs.insert(1,"cohort",cohort);cs.insert(2,"source_run_id",artifact["workflow_run"]["id"])
        extras.extend([("goalie_consensus_graded",cd),("goalie_consensus_summary",cs)])
        cp=Path("data/results/goalie_consensus_ledger.csv")
        cl=pd.read_csv(cp) if cp.exists() else cs.iloc[:0].copy()
        if not a.replay:cl=pd.concat([cl,cs],ignore_index=True)
        if cl.duplicated(["date","model"]).any():raise ValueError("Duplicate consensus ledger")
        extras.append(("goalie_consensus_ledger",cl))
    summary=pd.concat([ts,gs,ats,ss],ignore_index=True)
    summary.insert(0,"date",m["date"]);summary.insert(1,"cohort",cohort);summary.insert(2,"source_run_id",artifact["workflow_run"]["id"])
    ledger_path=a.ledger or ("data/results/prospective_shadow_ledger.csv" if not a.replay else None)
    ledger=pd.read_csv(ledger_path) if ledger_path else summary.iloc[:0].copy()
    # Replays never enter the prospective ledger.
    if not a.replay:ledger=pd.concat([ledger,summary],ignore_index=True)
    if not ledger.empty and not ledger.cohort.eq("CLEAN_SHADOW_PREGAME").all():raise ValueError("Nonprospective row in ledger")
    aggregate=cumulative(ledger)
    out.mkdir(parents=True,exist_ok=True)
    for name,frame in [("totals_graded",td),("goalies_graded",gd),("atg_graded",ad),("summary",summary),("prospective_ledger",ledger),("cumulative",aggregate)]+extras:
        frame.to_csv(out/(name+".csv"),index=False)
    meta={"date":m["date"],"cohort":cohort,"source_run_id":artifact["workflow_run"]["id"],"source_artifact_id":artifact["id"],"lock_hash":digest(root/"manifest.json"),"outcome_hashes":{k:digest(v) for k,v in [("team",a.team_games),("goalie",a.goalie_features),("skater",a.skater_games)]},"summary_sha256":digest(out/"summary.csv"),"games":len(finals),"ledger_rows":len(ledger),"official_records_changed":False}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== UNIFIED GRADE MANIFEST ===");print(json.dumps(meta,indent=2));print("=== UNIFIED GRADE SUMMARY ===");print(summary.to_csv(index=False));print("=== END UNIFIED GRADE ===")
    if "goalie_consensus_counts" in m:
        print("=== CONSENSUS SUMMARY ===");print(cs.to_csv(index=False));print("=== END CONSENSUS SUMMARY ===")
if __name__=="__main__":main()
