import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# Danh mục thật còn trống số liệu của nhiều phương án tường: kiểm thử tối ưu dùng thêm số MẪU (data/sample/catalog).
if not os.environ.get("OPTIMAT_CATALOG_OVERLAY"):
    os.environ["OPTIMAT_CATALOG_OVERLAY"] = str(ROOT / "data/sample/catalog")


@pytest.fixture(scope="session")
def sample_dxf() -> str:
    path = ROOT / "data/sample/sample_floor.dxf"
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/make_sample_dxf.py")], check=True)
    return str(path)


@pytest.fixture(scope="session")
def sample_prices() -> str:
    path = ROOT / "data/sample/prices_sample.csv"
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/make_sample_data.py")], check=True)
    return str(path)
