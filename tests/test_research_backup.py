import sys,hashlib
from pathlib import Path
from zipfile import ZipFile
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from verify_research_backup import verify_member

def test_verify_exact_payload_and_reject_changed(tmp_path):
    p=tmp_path/"archive.zip"
    with ZipFile(p,"w") as z:z.writestr("nested/data.parquet",b"original")
    h=hashlib.sha256(b"original").hexdigest()
    assert verify_member(p,"data.parquet",h)["bytes"]==8
    with pytest.raises(ValueError,match="Checksum mismatch"):
        verify_member(p,"data.parquet","0"*64)

def test_duplicate_basename_rejected(tmp_path):
    p=tmp_path/"archive.zip"
    with ZipFile(p,"w") as z:
        z.writestr("a/data",b"a")
        z.writestr("b/data",b"b")
    with pytest.raises(ValueError,match="Expected one"):
        verify_member(p,"data","0"*64)
