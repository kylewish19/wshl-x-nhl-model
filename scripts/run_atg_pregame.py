"""Score the frozen ATG challengers on the official candidate universe.

Live mode must run before the first scheduled NHL game on the target date.
Replay mode is explicitly retrospective, never an official record.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from audit_atg_archive import audit_counts
from build_goalie_features import BASE, get_json
from train_atg_game_shadow import parse_game
from wshlx_nhl.atg_pregame import predict, price_comparison, MODELS

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def schedule(day):
    payload=get_json(f"{BASE}/score/{day}")
    if "games" not in payload:
        raise ValueError(f"Missing schedule for {day}")
    return [g for g in payload["games"] if int(g["gameType"])==2]

def live_cutoff(target, games):
    now=pd.Timestamp.now(tz="UTC")
    if datetime.now(ZoneInfo("America/New_York")).date().isoformat()!=target:
        raise ValueError("Live target must be today's Eastern date")
    slate=schedule(target)
    if not slate:
        raise ValueError("No scheduled games")
    names={g["awayTeam"]["abbrev"]+"@"+g["homeTeam"]["abbrev"] for g in slate}
    if not set(games).issubset(names):
        raise ValueError("Candidate matchup not in NHL schedule")
    first=min(pd.Timestamp(g["startTimeUTC"]) for g in slate)
    if now>=first or any(g["gameState"] not in ("FUT","PRE") for g in slate):
        raise ValueError("Slate already started or schedule state unverified")
    return first

def extend_history(raw,target):
    # Extend only the dated archive, never today's games. All prior scheduled
    # regular-season games must be final; fail rather than silently skip.
    start=pd.to_datetime(raw.date).max().normalize()+pd.Timedelta(days=1)
    jobs={}
    for day in pd.date_range(start,pd.Timestamp(target)-pd.Timedelta(days=1)):
        for g in schedule(day.date().isoformat()):
            if g["gameState"] not in ("OFF","FINAL"):
                # Postponed games are not completed history, but ambiguous
                # schedule states require review.
                if g.get("gameScheduleState")=="PPD":
                    continue
                raise ValueError(f"Nonfinal prior scheduled game {g['id']}")
            jobs[int(g["id"])]=str(g["season"])
    if jobs:
        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            rows=list(ex.map(lambda item:parse_game(*item),jobs.items()))
        extra=pd.DataFrame([row for game in rows for row in game])
        if extra.game_id.nunique()!=len(jobs):
            raise ValueError("Incomplete incremental history")
        raw=pd.concat([raw,extra],ignore_index=True)
    return raw

def matched_board(candidates,history,target):
    d=candidates[candidates.market.eq("anytime_goal")].copy()
    if not d.date.astype(str).eq(target).all():
        raise ValueError("Candidate date mismatch")
    d["player_id"]=pd.to_numeric(d.player_id,errors="coerce")
    d["official_probability"]=pd.to_numeric(d.model_probability,errors="coerce")
    active=pd.to_numeric(d.active,errors="coerce").eq(1)
    valid_id=d.player_id.notna() & d.player_id.gt(0) & d.player_id.mod(1).eq(0)
    valid_p=d.official_probability.between(0,1)
    splits=d.game.str.split("@",expand=True)
    if splits.shape[1]!=2 or splits.isna().any().any():
        raise ValueError("Malformed matchup")
    d["opponent"]=np.where(d.team.eq(splits[0]),splits[1],splits[0])
    d["is_home"]=d.team.eq(splits[1]).astype(int)
    matchup=d.team.eq(splits[0])|d.team.eq(splits[1])
    identity=d.team.eq(d.resolved_team)&d.team.eq(d.listed_team)
    # No live-roster guesses: use the frozen official identity; position from
    # known history, or explicitly verified position on the submitted board.
    positions=history.sort_values(["date","game_id"]).drop_duplicates("player_id",keep="last").set_index("player_id").position
    historical_pos=d.player_id.map(positions)
    verified=d["position"] if "position" in d else pd.Series(None,index=d.index,dtype=object)
    d["position"]=verified.where(verified.isin(["F","D"]),historical_pos)
    reasons=np.select([~active,~valid_id,~identity,~matchup,~valid_p,~d.position.isin(["F","D"])],
        ["INACTIVE","UNRESOLVED_ID","TEAM_MISMATCH","INVALID_MATCHUP","INVALID_OFFICIAL_P","UNKNOWN_POSITION"],default="")
    d["exclusion_reason"]=reasons
    good=d[d.exclusion_reason.eq("")].copy()
    if good.empty: raise ValueError("No matched eligible players")
    good["player_id"]=good.player_id.astype("int64")
    if good.player_id.duplicated().any():
        raise ValueError("Duplicate player on submitted slate")
    return good,d[~d.exclusion_reason.eq("")].copy()

def main():
    ap=argparse.ArgumentParser()
    for name in ["history","bundle","candidates","target-date","out-dir"]:
        ap.add_argument("--"+name,required=True)
    ap.add_argument("--replay",action="store_true")
    args=ap.parse_args()
    target=args.target_date
    out=Path(args.out_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Refuse overwrite of existing lock")
    out.mkdir(parents=True,exist_ok=True)
    candidates=pd.read_csv(args.candidates)
    first=None if args.replay else live_cutoff(target,candidates.game.unique())
    raw=pd.read_parquet(args.history)
    if not args.replay:
        if pd.Timestamp(target)<pd.Timestamp("2026-11-25"):
            raise ValueError("Before prospective benchmark cutoff")
        raw=extend_history(raw,target)
    raw=raw[pd.to_datetime(raw.date)<pd.Timestamp(target)].copy()
    repaired,audit=audit_counts(raw,out/"audit")
    good,excluded=matched_board(candidates,repaired,target)
    bundle=joblib.load(args.bundle)
    f=predict(repaired,good,target,bundle)
    keys=["date","game","player_id","player_name","team","opponent","position","official_probability"]
    probs=pd.concat([good[keys],f.drop(columns=["is_home"])],axis=1)
    if not probs[MODELS].apply(lambda x:x.between(0,1)).all().all():
        raise ValueError("Invalid probability output")
    probs.to_csv(out/"probabilities.csv",index=False)
    excluded.to_csv(out/"excluded.csv",index=False)
    # Only after the probability file is written, apply identical price gates.
    prices=good[["date","game","player_id","odds_american"]]
    p=price_comparison(probs,prices)
    p.to_csv(out/"matched_prices.csv",index=False)
    for name in MODELS:
        q=p[p[name+"_qualifies"]].sort_values(name+"_ev",ascending=False)
        q.to_csv(out/(name+"_paper_card.csv"),index=False)
    now=pd.Timestamp.now(tz="UTC")
    if first is not None and now>=first:
        raise ValueError("Missed pregame cutoff; no clean lock")
    manifest={"target_date":target,"status":"RETROSPECTIVE_SMOKE_ONLY" if args.replay else "PREGAME_PENDING_ARTIFACT_VERIFICATION",
        "created_at_utc":now.isoformat(),"first_puck_utc":str(first) if first is not None else None,
        "history_last_date":str(pd.to_datetime(raw.date).max().date()),"history_rows":len(raw),
        "matched_rows":len(good),"excluded_rows":len(excluded),
        "exclusion_counts":excluded.exclusion_reason.value_counts().to_dict(),
        "candidate_file_sha256":digest(args.candidates),"archive_sha256":digest(args.history),
        "bundle_sha256":digest(args.bundle),"probability_sha256":digest(out/"probabilities.csv"),
        "prices_sha256":digest(out/"matched_prices.csv"),
        "paper_card_counts":{m:int(p[m+"_qualifies"].sum()) for m in MODELS},
        "price_gate":{"edge":.05,"ev":.05},"official_model_changed":False,
        "limits":"Matched subset only; historical position fallback; actual participation not guaranteed; verify external artifact timestamp before clean classification."}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print("=== LOCK MANIFEST ===")
    print(json.dumps(manifest,indent=2))
    print("=== MATCHED ROWS ===")
    print(p[["game","player_name","official_probability","shot_probability","boosting_calibrated","odds_american"]].head(30).to_csv(index=False))

if __name__=="__main__":
    main()
