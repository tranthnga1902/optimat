"""Chỉ nạp module candidate trong child; không ghi/import bản rebar canonical."""
import os
import sys
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[5]
for key in ("DATABASE_URL", "OPTIMAT_TEST_DATABASE_URL", "OPENAI_API_KEY"):
    os.environ.pop(key, None)
os.environ["OPTIMAT_NO_DOTENV"] = "1"
os.environ["LLM_PROVIDER"] = "none"
sys.path.insert(0, str(ROOT / "src"))
import optimat.rough

path = Path(__file__).with_name("rebar.py")
spec = importlib.util.spec_from_file_location("optimat.rough.rebar", path)
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
optimat.rough.rebar = candidate
assert Path(candidate.__file__).resolve() == path.resolve()
import pytest

raise SystemExit(pytest.main(sys.argv[1:]))
