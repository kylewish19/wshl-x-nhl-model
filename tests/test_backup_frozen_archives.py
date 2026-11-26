import sys,hashlib
from pathlib import Path
from zipfile import ZipFile
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from backup_frozen_archives import backup,digest,verify_archive,ROOT

def test_exact_zip_and_member(tmp_path):
    p=tmp_path/"test.zip"
    with ZipFile(p,"w") as z:z.writestr("nested/file.bin",b"original")
    e=dict(key="test",artifact_id=1,name="test",zip_digest=digest(p),
           members={"file.bin":hashlib.sha256(b"original").hexdigest()})
    assert verify_archive(p,e)["verified_members"][0]["bytes"]==8
    assert backup(tmp_path,{"archives":[e]})["status"]=="EXACT_ARCHIVE_BYTES_VERIFIED"
    with pytest.raises(ValueError,match="ZIP digest mismatch"):
        verify_archive(p,{**e,"zip_digest":"sha256:"+"0"*64})
    with pytest.raises(ValueError,match="Checksum mismatch"):
        verify_archive(p,{**e,"members":{"file.bin":"0"*64}})

def test_no_public_destination_or_unknown_key(tmp_path):
    with pytest.raises(ValueError,match="outside public repository"):
        backup(ROOT/"backup",{"archives":[]},download=True)
    with pytest.raises(ValueError,match="Unknown archive key"):
        backup(tmp_path,{"archives":[]},keys=["missing"])
