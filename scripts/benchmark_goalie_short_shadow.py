import argparse,json
from pathlib import Path
import pandas as pd
from wshlx_nhl.goalie_short_shadow import prepare,benchmark

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--features",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();raw=pd.read_parquet(a.features)
    assert len(raw)==13890 and pd.to_datetime(raw.date).max()<pd.Timestamp("2026-11-25")
    d=prepare(raw)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rest=[]
    for season,x in d.groupby("season"):
        rest.append({"season":season,"starts":len(x),"unique_ids":x.goalie_id.nunique(),
            "explicit_starter_flags":int(x.starter_flag.sum()),"archive_rest_le1":int(x.days_rest.le(1).sum()),
            "rebuilt_rest_le1":int(x.rest_rebuilt.le(1).sum()),"rest_mismatches":int(x.days_rest.ne(x.rest_rebuilt).sum()),
            "starts7_mismatches":int(x.starts_last_7d.ne(x.starts7_rebuilt).sum()),
            "short_starts":int(x.short.sum()),"first_observed_starts":int(x.prior_starts.eq(0).sum())})
    audit=pd.DataFrame(rest);audit.to_csv(out/"rest_audit.csv",index=False)
    print("=== REST AUDIT ===");print(audit.to_csv(index=False));print("=== END REST ===",flush=True)
    metrics,risk,counts,meta=benchmark(d)
    for name,frame in [("metrics",metrics),("risk",risk),("counts",counts)]:
        frame.to_csv(out/(name+".csv"),index=False)
        print("=== "+name.upper()+" ===");print(frame.to_csv(index=False));print("=== END "+name.upper()+" ===")
    meta.update({"status":"HISTORICAL_DIAGNOSTIC_ONLY","limitations":["Same simpler Poisson regression architecture for single and mixture; not official v0.2 comparison","Actual starters only, fixed synthetic save lines, no odds","Rest measures days between starts, not relief appearances or full recovery","Archive may misidentify starters when explicit flag absent","Evaluation seasons previously observed"]})
    (out/"manifest.json").write_text(json.dumps(meta,indent=2))
    print("=== MANIFEST ===");print(json.dumps(meta,indent=2));print("=== END MANIFEST ===")
if __name__=="__main__":main()
