"""data/rules/nguong_nhan_dien.csv: mọi ngưỡng mã nguồn dùng đều có trong file, kèm định nghĩa và nguồn."""
import csv
import re
from pathlib import Path

import pytest

from optimat import config

ROOT = Path(__file__).resolve().parents[1]


def test_every_threshold_defined_with_source():
    rows = list(csv.DictReader(open(config.THRESHOLDS_PATH, encoding="utf-8-sig", newline="")))
    codes = [r["ma"] for r in rows]
    assert len(codes) == len(set(codes))
    for r in rows:
        float(r["gia_tri"])
        assert r["dinh_nghia"].strip() and r["nguon"].strip() and r["don_vi"].strip(), r["ma"]
    used = {m for f in (ROOT / "src").rglob("*.py") for m in re.findall(r'threshold\("(\w+)"\)', f.read_text(encoding="utf-8"))}
    assert used and used <= set(codes), used - set(codes)


def test_missing_threshold_raises():
    with pytest.raises(KeyError, match="NG99"):
        config.threshold("NG99")
