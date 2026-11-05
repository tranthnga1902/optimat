"""Phép kiểm cục bộ từ output bộ đọc KC. Không nối DB hoặc gọi trợ lý."""
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path

import ezdxf
from optimat.catalog.repository import Catalog
from optimat.db.session import get_database_url
from optimat.rough.takeoff import RoughRequest, compute_rough

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
if get_database_url() or not os.environ.get("OPTIMAT_NO_DOTENV"):
    raise RuntimeError("Chỉ chạy bằng CSV với OPTIMAT_NO_DOTENV=1, DATABASE_URL trống.")


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


source = ROOT/"data/drawings/build/nha_sang_hai_duong_4x15_ket_cau.dxf"
digest = hashlib.sha256(source.read_bytes()).hexdigest()
reader_dir = ROOT/"docs/review/data20_03/column_fix/reader_actual"
manifest = read(reader_dir/"ACTIVE.json")
reader = read(reader_dir/manifest["reader"])
assert digest == reader["source_sha256"]
request = RoughRequest(plans=[], structural_columns=reader["structural_columns"])
result = compute_rough(request, Catalog.from_csv())
rows = []
for axis in ("A", "B"):
    instance, = [c for c in request.structural_columns if (c.code.upper(), c.grid_x, c.grid_y, c.floor_key) == ("C-2", "4", axis, "T2")]
    bound = []
    for index, work in enumerate(result.works):
        if work.basis != "structural_instance" or f"[{instance.instance_id}]" not in (work.element or ""):
            continue
        uses = [{"name": m.name, "material_id": m.material_id, **u.model_dump()} for m in result.materials
                for u in m.uses if u.rowIndex == index]
        assert uses and all(u["work"] == work.code and u["plan"] == work.plan for u in uses)
        bound.append(dict(work_key=f"w:{index}", rowIndex=index, code=work.code, element=work.element,
                          raw=work.quantity_detail.total_raw if work.quantity_detail else None,
                          known=work.quantity_detail.known_part_raw if work.quantity_detail else None,
                          quantity=work.quantity, missing=work.missing, contributions=uses))
    assert {w["code"] for w in bound} == {"COT", "COP_PHA"}
    rows.append(dict(axis=f"4/{axis}", instance_id=instance.instance_id, works=bound))
assert not ({w["work_key"] for w in rows[0]["works"]} & {w["work_key"] for w in rows[1]["works"]})
for m in result.materials:
    for u in m.uses:
        assert u.rowIndex is not None
        w = result.works[u.rowIndex]
        assert u.work == w.code and u.plan == w.plan
save("production.json", dict(source_sha256=digest, reader_input=manifest["reader"], used="compute_rough; structural columns only",
    database=False, openai=False, browser=False, checked=False, catalog="CSV", works=len(result.works), column_segments=rows))
save("ui_input.json", {"request": {"structural_columns": reader["structural_columns"], "plans": []},
                        "result": {"works": [w.model_dump(exclude={"quantity_detail", "dimensions", "evidence", "inputs"}) | {
                            "quantity_detail": {"total_raw": w.quantity_detail.total_raw} if w.quantity_detail else None}
                            for w in result.works], "materials": [m.model_dump() for m in result.materials]}})

# Kiểm tọa độ và thuộc tính các locator đã nhận diện. Đây là đối chiếu nguồn, không phải parser gán đoạn.
doc = ezdxf.readfile(source)
def observe(handle):
    e = doc.entitydb[handle]
    p = e.dxf.insert
    return {"handle": handle, "type": e.dxftype(), "xy": [p.x, p.y],
            **({"text": e.dxf.text} if e.dxftype()=="TEXT" else
               {"block": e.dxf.name, "attrs": {a.dxf.tag:a.dxf.text for a in e.attribs}})}

groups = {}
for label, handles in (("C-1", ["118CD0D","118CD0E","118CCC5","118CCD1"]),
                       ("C-1A",["118CD8A","118CD8B","118CD2A","118CD36"]),
                       ("C-2", ["118CDEF","118CDF0","118CDA7","118CDB3","118CDD7"])):
    observations = [observe(h) for h in handles]
    assert observations[0]["text"] == label
    groups[label] = observations
main = [r["attrs"] for r in groups["C-2"][2:4]]
assert [r["SH"] for r in main] == ["3","4"] and all(r["DK"]=="20" for r in main)
length = sum(Decimal(r["DAI"]) * Decimal(r["SL1"]) / 1000 for r in main)
kg = length * Decimal("2.470")  # kiểm chéo kg/m do 00/07 đọc tại KC-00 bảng 3
printed_per_column = sum(Decimal(r["TL"]) * Decimal(r["SL1"]) / Decimal(r["SLA"]) for r in main)
assert (length, kg, printed_per_column) == (Decimal("17.2"), Decimal("42.484"), Decimal("42.4"))
save("schedule_source.json", dict(source_sha256=digest, groups=groups, source_context="PDF KC-02-04 trang 22; KC-00 bảng 3 trang 3",
     long_bar_marks=["3","4"],metres_per_member=str(length),kg_per_m="2.470",calculated_kg=str(kg),
     allocated_printed_kg=str(printed_per_column),difference_kg=str(kg-printed_per_column),
     stirrup_mark="7",stirrups_for_segment=None, reader_assignment_confirmed=False))
print("Two separate segments linked; source marks checked. No schedule or purchase amount allocated to the app.")
