"""Verify incremental pregame history using existing official and research code.
No odds, picks, model changes or raw-data publication.
"""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd
from run_daily_core import history,check,find,digest
from run_atg_pregame import extend_history,schedule,live_cutoff
from build_resume_snapshot import build_skater_snapshot,team_form_summary,goalie_workload_summary

def main():
    p=argparse.ArgumentParser()
    for k in ("date","archive","skater-archive","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args();target=pd.Timestamp(a.date);root=Path(a.out);root.mkdir(exist_ok=False)
    work=root/"private_work";work.mkdir()
    slate=schedule(a.date)
    games=[g["awayTeam"]["abbrev"]+"@"+g["homeTeam"]["abbrev"] for g in slate]
    first=live_cutoff(a.date,games)
    day_counts={}
    expected={}
    for day in pd.date_range("2026-11-25",target-pd.Timedelta(days=1)):
        ds=day.date().isoformat();prior=schedule(ds)
        accepted=[g for g in prior if g.get("gameScheduleState")!="PPD"]
        check(all(g["gameState"] in ("OFF","FINAL") for g in accepted),"Nonfinal historical game")
        day_counts[ds]=len(accepted)
        for g in accepted:
            gid=int(g["id"]);check(gid not in expected,"Duplicate prior game")
            expected[gid]=(ds,{g["awayTeam"]["abbrev"],g["homeTeam"]["abbrev"]})
    tp,gp,hmeta=history(a.archive,a.date,work,False)
    t,g=pd.read_parquet(tp),pd.read_parquet(gp)
    raw_path=find(a.skater_archive,"skater_games.parquet")
    check(digest(raw_path)=="5a782b58ddd7922c7820de4dc20262b348f2547a891e431441dddf5d6734ff2b","Skater archive digest mismatch")
    raw=pd.read_parquet(raw_path)
    check(len(raw)==249950 and pd.to_datetime(raw.date).max()==pd.Timestamp("2026-11-24") and raw.game_id.nunique()==6945,"Original skater archive mismatch")
    extra=extend_history(raw,a.date)
    extra["date"]=pd.to_datetime(extra.date)
    check(extra.date.lt(target).all() and not extra.duplicated(["game_id","player_id"]).any(),"Skater history duplicate or cutoff violation")
    check(set(t.game_id)==set(g.game_id)==set(extra.game_id),"Historical game coverage mismatch")
    for gid,(day,teams) in expected.items():
        for table in (t,g,extra):
            x=table[table.game_id.eq(gid)]
            check(len(x)>0 and set(x.team)==teams and pd.to_datetime(x.date).dt.strftime("%Y-%m-%d").eq(day).all(),"Incremental identity/date/team mismatch")
        x=extra[extra.game_id.eq(gid)]
        check(x.groupby("team").size().min()>=10 and x.toi_seconds.gt(0).all(),"Incomplete skater participation")
    check(hmeta["additional_games"]==len(expected),"Incremental game count mismatch")
    check(len(extra)>=len(raw),"Historical skater rows lost")
    snapshot,meta=build_skater_snapshot()
    check(not snapshot.duplicated(["player_id","team"]).any(),"Duplicate snapshot identity")
    check(snapshot.official_goal_prob.between(0,1).all(),"Invalid skater probability")
    check(pd.Timestamp.now(tz="UTC")<first,"Today's slate began during preparation")
    form=team_form_summary(t,a.date);load=goalie_workload_summary(g,a.date)
    # Raw historical tables and live snapshot remain ephemeral runner files.
    extra.to_parquet(work/"skater.parquet",index=False)
    snapshot.to_csv(work/"snapshot.csv",index=False)
    report={"target_date":a.date,"status":"HISTORY_READINESS_ONLY_NO_PICKS","original_archive_cutoff":"2026-11-24","history_last_date":str(pd.to_datetime(t.date).max().date()),"additional_games_by_date":day_counts,"additional_games":len(expected),"historical_games":t.game_id.nunique(),"team_rows":len(t),"goalie_starter_rows":len(g),"skater_rows":len(extra),"additional_skater_rows":len(extra)-len(raw),"current_season_completed_games":int(t[t.season.astype(str).eq("20262027")].game_id.nunique()),"team_form_count":len(form),"current_goalies_with_starts":len(load),"skater_snapshot_metrics":meta,"first_puck_utc":first.isoformat(),"slate_games":games,"slate_count":len(games),"all_prior_games_final":True,"no_target_date_results":True,"prepared_history_hashes":{**hmeta["prepared_hashes"],"skater":digest(work/"skater.parquet")},"snapshot_sha256":digest(work/"snapshot.csv"),"official_model_changed":False,"raw_data_retention":"Ephemeral runner only; original frozen archives retained, next live runner rebuilds incremental history. No raw upload."}
    (root/"readiness.json").write_text(json.dumps(report,indent=2,default=str))
    print("READINESS "+json.dumps(report,default=str),flush=True)
if __name__=="__main__":main()
