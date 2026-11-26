"""Verify or privately download exact original frozen archives; never unpickle or upload.
Uses only Python standard library and authenticated gh CLI for optional download.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
from verify_research_backup import verify_member

ROOT=Path(__file__).resolve().parents[1]
INVENTORY=ROOT/"config/frozen_archive_inventory.json"

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return "sha256:"+h.hexdigest()

def verify_archive(path,entry):
    path=Path(path)
    actual=digest(path)
    if actual!=entry["zip_digest"]:raise ValueError("ZIP digest mismatch: "+entry["name"])
    members=[verify_member(path,n,h) for n,h in entry["members"].items()]
    return {"key":entry["key"],"artifact_id":entry["artifact_id"],"zip_digest":actual,
            "bytes":path.stat().st_size,"verified_members":members}

def backup(directory,inventory,download=False,keys=None):
    dest=Path(directory).expanduser().resolve()
    if dest==ROOT or dest.is_relative_to(ROOT):raise ValueError("Backup destination must be outside public repository")
    entries=[e for e in inventory["archives"] if keys is None or e["key"] in keys]
    if keys is not None and set(keys)!={e["key"] for e in entries}:raise ValueError("Unknown archive key")
    if download:dest.mkdir(parents=True,exist_ok=True)
    if not dest.is_dir():raise ValueError("Missing private destination")
    report=[]
    for e in entries:
        p=dest/(e["name"]+".zip")
        if not p.exists() and download:
            temp=p.with_suffix(".zip.partial")
            if temp.exists():raise ValueError("Existing partial download; review and remove manually")
            endpoint=f'repos/{inventory["repository"]}/actions/artifacts/{e["artifact_id"]}/zip'
            try:
                with temp.open("xb") as f:subprocess.run(["gh","api",endpoint],stdout=f,check=True)
                result=verify_archive(temp,e)
                if p.exists():raise ValueError("Refuse overwrite")
                temp.rename(p)
            except Exception:
                temp.unlink(missing_ok=True)
                raise
        else:result=verify_archive(p,e)
        report.append(result)
    return {"status":"EXACT_ARCHIVE_BYTES_VERIFIED","archives":report}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True)
    p.add_argument("--download",action="store_true",help="Download missing originals through authenticated gh")
    p.add_argument("--keys",nargs="+")
    a=p.parse_args()
    inventory=json.loads(INVENTORY.read_text())
    print(json.dumps(backup(a.directory,inventory,a.download,a.keys),indent=2))

if __name__=="__main__":main()
