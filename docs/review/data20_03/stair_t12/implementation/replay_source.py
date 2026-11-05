"""Replay nguồn scoped, không tuyên bố đã parse đủ CAD/KT hoặc dùng oracle thể tích."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ["OPTIMAT_NO_DOTENV"]="1"
os.environ.pop("DATABASE_URL",None)
os.environ.pop("OPTIMAT_TEST_DATABASE_URL",None)
sys.path.insert(0,str(Path.cwd()/"src"))
from optimat.catalog.repository import Catalog
from optimat.rough.stairs import Stair,StairFlight,StairLanding
from optimat.rough.takeoff import RoughRequest,PlanInput,compute_rough


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--from-floor",required=True)
    p.add_argument("--to-floor",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    payload=json.loads(a.source.read_text(encoding="utf-8-sig"))
    measurements=payload["concrete"]
    where=f"Nguồn scoped07, chưa duyệt: {payload['source_file']}; SHA {payload['sha256']}; {payload['sheet']}/p{payload['pdf_page']}; {payload['group']}"
    t=measurements.get("inclined_waist_perpendicular_thickness_m")
    top=measurements.get("upper_floor_landing_thickness_m")
    count=measurements.get("flight_count_candidate",0)
    stair=Stair(id=payload["group"],from_floor=a.from_floor,to_floor=a.to_floor,
        source="scoped_source_replay",scope_source=None,
        steps_material="masonry" if measurements.get("steps_material")=="brickwork" else "unknown",
        steps_material_source=where+"; note bậc xây" if measurements.get("steps_material")=="brickwork" else None,
        waist_thickness_mm=None if t is None else t*1000,waist_thickness_basis="normal",
        waist_thickness_source=where+"; DIM vuông góc bản nghiêng",
        flights=[StairFlight(id=f"candidate-flight-{i+1}") for i in range(count)],
        landings=[StairLanding(id="candidate-arrival",thickness_mm=None if top is None else top*1000,
            field_sources={"thickness_mm":where+"; chiếu tới, vị trí/diện tích/sở hữu chưa gán"})])
    req=RoughRequest(plans=[PlanInput(name=f"Thang {a.from_floor} → {a.to_floor}",height_mm=None,walls=[],stairs=[stair])])
    result=compute_rough(req,Catalog.from_csv())
    (a.out/"request.json").write_text(req.model_dump_json(indent=2),encoding="utf-8")
    (a.out/"result.json").write_text(result.model_dump_json(indent=2),encoding="utf-8")
    receipt=dict(mode="REPLAY_NGUON_SCOPED_KHONG_PHAI_KET_QUA_TU_NHAN_CAD",source=str(a.source),
        source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),source_human_approval=payload.get("human_approval"),
        source_approval_status=payload.get("approval_status"),candidate_flights=count,
        expected_output_not_loaded=True,steel_schedule_not_multiplied_or_bound=True,
        stair_works=[dict(code=w.code,quantity=w.quantity,status=w.status,missing=w.missing) for w in result.works
            if w.code in ("CAU_THANG","XAY") or w.formwork_of=="CAU_THANG"])
    (a.out/"receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=="__main__":main()
