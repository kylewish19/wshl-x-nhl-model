"""Verify private copies of original GitHub artifact ZIPs without extracting them."""
import argparse,hashlib,json
from pathlib import Path,PurePosixPath
from zipfile import ZipFile

def verify_member(archive,basename,expected):
    with ZipFile(archive) as z:
        names=[i for i in z.infolist() if not i.is_dir() and PurePosixPath(i.filename).name==basename]
        if len(names)!=1:raise ValueError(f"Expected one {basename} in {archive}")
        h=hashlib.sha256()
        with z.open(names[0]) as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
        actual=h.hexdigest()
        if actual!=expected:raise ValueError(f"Checksum mismatch: {basename}")
        return {"file":basename,"sha256":actual,"bytes":names[0].file_size}

def main():
    p=argparse.ArgumentParser()
    for k in ["history","bundle","team-goalie"]:p.add_argument("--"+k,required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/"config/atg_frozen_research_2026-11-25.json").read_text())
    grade=json.loads((root/"data/model_runs/2026-11-25_unified_shadow_grading_manifest.json").read_text())
    rows=[verify_member(a.history,"skater_games.parquet",config["history"]["sha256"]),
          verify_member(a.bundle,"atg_game_shadow.joblib",config["bundle"]["sha256"]),
          verify_member(a.team_goalie,"2026-11-24_team_games.parquet",grade["outcome_hashes"]["team"]),
          verify_member(a.team_goalie,"2026-11-24_goalie_features.parquet",grade["outcome_hashes"]["goalie"])]
    print(json.dumps({"status":"EXACT_PAYLOAD_HASHES_VERIFIED","files":rows},indent=2))
if __name__=="__main__":main()
