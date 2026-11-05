"""Đối chiếu native entities theo locators04; locators không làm input reader production."""
import json
from pathlib import Path
from candidate import load_source, native_rows, read_region

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
packet = json.loads((ROOT/"docs/review/data20_04/column_material_binding/schedule_source.json").read_text(encoding="utf-8"))
file = ROOT/"data/drawings/build/nha_sang_hai_duong_4x15_ket_cau.dxf"
doc, source = load_source(file, packet["source_sha256"])
all_rows = native_rows(doc, source)
by_handle = {r["handlepath"][-1]: r for r in all_rows}
selected, anchors = [], []
for claimed_group, entities in packet["groups"].items():
    for ref in entities:
        e = doc.entitydb[ref["handle"]]
        assert e.dxftype() == ref["type"]
        if e.dxftype() == "INSERT":
            row = by_handle[ref["handle"]]
            assert all(row["raw"].get(k) == v for k, v in ref["attrs"].items())
            selected.append(row)
        else:
            assert e.dxf.text == ref["text"]
            anchors.append({**source,"handlepath":["modelspace",e.dxf.handle],"type":e.dxftype(),
                            "layer":e.dxf.layer,"text":e.dxf.text,
                            "xy":[e.dxf.insert.x,e.dxf.insert.y],
                            "group_claim_from_packet04":claimed_group,"binding_confirmed":False})
c2 = next(a for a in anchors if a["text"] == "C-2")
x,y = c2["xy"]
frames = []
for e in doc.modelspace().query("LWPOLYLINE"):
    if not e.closed:
        continue
    pts = list(e.get_points("xy"))
    if pts and min(p[0] for p in pts) <= x <= max(p[0] for p in pts) and min(p[1] for p in pts) <= y <= max(p[1] for p in pts):
        frames.append({"handle":e.dxf.handle,"layer":e.dxf.layer,"points":pts,
                       "is_group_boundary_confirmed":False})
result = {"kind":"ACTUAL_RAW_SOURCE_READ_NOT_APPROVED_TAKEOFF",**source,
          "split":"build","INSUNITS":doc.header.get("$INSUNITS"),
          "raw_rows":selected,"anchor_evidence":anchors,"closed_frames_containing_C2_anchor":frames,
          "accepted_group_rows":[],"segment_assignment":None,"axis_assignment":None,
          "pending":["Chưa có ranh giới hình học riêng cho nhóm/bảng C-2",
                     "INSUNITS=0; chưa chứng thực đơn vị DAI/DT/TL từ header/nguồn thiết kế trong lượt này",
                     "Chưa nối mark→chi tiết đoạn/tầng/trục; mark7 TK_14 không được phân vào đoạn",
                     "C-1/C-2 trùng số không là cùng instance; không dùng locators04 như oracle đầu vào sản phẩm"]}
(OUT/"actual_raw_receipt.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"native_rows_checked":len(selected),"anchors_checked":len(anchors),
                  "frame_candidates":len(frames),"accepted_group_rows":0,"source_sha256":source["sha256"]}))
