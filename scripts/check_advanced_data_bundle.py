"""Validate a local advanced-data bundle; no downloads or publication."""
import argparse,json
from pathlib import Path
from wshlx_nhl.advanced_data_contract import load_bundle,reconcile,build_research

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",required=True)
    p.add_argument("--authorized-research",action="store_true")
    p.add_argument("--cutoffs",nargs="+")
    a=p.parse_args()
    m,data=load_bundle(a.bundle,a.authorized_research)
    if a.cutoffs:report,_=build_research(data,a.cutoffs)
    else:report=reconcile(data)
    print(json.dumps({"scope":m["scope"],"report":report,"official_records_changed":False,"note":"Local validation only; authorization declarations are not independent legal verification."},indent=2))
if __name__=="__main__":main()
