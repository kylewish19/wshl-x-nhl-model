"""Grade archived ATG research locks, without re-running predictions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from run_atg_pregame import digest, schedule
from train_atg_game_shadow import parse_game
from wshlx_nhl.atg_grading import grade_matched, KEYS
from wshlx_nhl.atg_pregame import MODELS
from wshlx_nhl.atg_basis_grading import classify_basis

def lock_status(manifest, artifact, replay):
    if artifact.get("expired") or artifact.get("workflow_run",{}).get("id") is None:
        raise ValueError("Invalid source artifact metadata")
    if artifact.get("name")!="atg-pregame-shadow-output":
        raise ValueError("Wrong source artifact")
    if replay:
        if manifest["status"]!="RETROSPECTIVE_SMOKE_ONLY":
            raise ValueError("Expected retrospective manifest")
        return "RETROSPECTIVE_SMOKE_ONLY"
    if manifest["status"]!="PREGAME_PENDING_ARTIFACT_VERIFICATION":
        raise ValueError("Expected pregame manifest")
    locked=pd.Timestamp(manifest["created_at_utc"])
    uploaded=pd.Timestamp(artifact["created_at"])
    first=pd.Timestamp(manifest["first_puck_utc"])
    if any(x.tzinfo is None for x in (locked,uploaded,first)):
        raise ValueError("Missing timezone")
    if not locked<=uploaded<first:
        raise ValueError("Artifact not independently timestamped before puck drop")
    if pd.Timestamp(manifest["history_last_date"])>=pd.Timestamp(manifest["target_date"]):
        raise ValueError("History cutoff violation")
    return "CLEAN_SHADOW_PREGAME"

def load_lock(root,artifact,replay):
    m=json.loads((root/"manifest.json").read_text())
    status=lock_status(m,artifact,replay)
    for file,key in [("probabilities.csv","probability_sha256"),("matched_prices.csv","prices_sha256")]:
        if digest(root/file)!=m[key]:
            raise ValueError("Frozen file hash mismatch: "+file)
    p=pd.read_csv(root/"matched_prices.csv",dtype={"date":str})
    q=pd.read_csv(root/"probabilities.csv",dtype={"date":str})
    if len(p)!=m["matched_rows"] or not p.date.eq(m["target_date"]).all():
        raise ValueError("Manifest coverage mismatch")
    pd.testing.assert_frame_equal(p[KEYS+MODELS],q[KEYS+MODELS],check_dtype=False)
    if "basis_counts" in m:
        pd.testing.assert_frame_equal(p[KEYS+["model_basis"]],q[KEYS+["model_basis"]],check_dtype=False)
        if classify_basis(p.model_basis).value_counts().to_dict()!=m["basis_counts"]:raise ValueError("Frozen basis coverage mismatch")
    for model in MODELS:
        if int(p[model+"_qualifies"].sum())!=m["paper_card_counts"][model]:
            raise ValueError("Manifest card count mismatch")
    return m,p,status

def get_outcomes(target,matchups):
    games={g["awayTeam"]["abbrev"]+"@"+g["homeTeam"]["abbrev"]:g for g in schedule(target)}
    rows=[]; completed=[]
    for matchup in sorted(matchups):
        g=games.get(matchup)
        if not g or g["gameState"] not in ("OFF","FINAL"):
            raise ValueError("Missing/nonfinal matchup: "+matchup)
        raw=parse_game(int(g["id"]),str(g["season"]))
        for r in raw:
            if r["date"]!=target or r["team"] not in matchup.split("@"):
                raise ValueError("Boxscore date/team mismatch")
            rows.append({"date":target,"game":matchup,"player_id":r["player_id"],"team":r["team"],"goals":r["goals"]})
        completed.append((target,matchup))
    return pd.DataFrame(rows),completed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lock-dir",required=True)
    ap.add_argument("--artifact-metadata",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--replay",action="store_true")
    a=ap.parse_args()
    root=Path(a.lock_dir);out=Path(a.out_dir)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Refuse overwrite of grading")
    artifact=json.loads(Path(a.artifact_metadata).read_text())
    m,p,status=load_lock(root,artifact,a.replay)
    o,completed=get_outcomes(m["target_date"],p.game.unique())
    detail,summary=grade_matched(p,o,completed)
    out.mkdir(parents=True,exist_ok=True)
    detail.to_csv(out/"graded.csv",index=False)
    summary.insert(0,"date",m["target_date"])
    summary.insert(1,"cohort",status)
    summary.to_csv(out/"summary.csv",index=False)
    meta={"target_date":m["target_date"],"cohort":status,"source_run_id":artifact["workflow_run"]["id"],
          "artifact_id":artifact["id"],"source_artifact_created_at":artifact["created_at"],
          "manifest_sha256":digest(root/"manifest.json"),"summary_sha256":digest(out/"summary.csv"),
          "games_graded":len(completed),"official_records_changed":False,
          "note":"DNP is paper void; no grading of excluded identities. Replay excluded from prospective records."}
    (out/"grading_manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== GRADING MANIFEST ===")
    print(json.dumps(meta,indent=2))
    print("=== MATCHED GRADING SUMMARY ===")
    print(summary.to_csv(index=False))

if __name__=="__main__":
    main()
