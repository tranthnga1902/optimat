"""C01: báo cáo đường cơ sở phần thô trên hồ sơ BUILD (đối chứng phát triển, không phải chỉ tiêu nghiệm thu).

    python scripts/c01_duong_co_so.py [--cases data/ground_truth/du_toan/cases.csv] [--out reports/c01_duong_co_so_build.xlsx]

Hồ sơ chọn qua select_cases("phat_trien") (chỉ build). Mỗi hồ sơ cần bộ D02 (data/ground_truth/du_toan/d02/<ten>) không lỗi
validator; kết quả hệ thống lấy bằng evaluate_rough.rough_for_case (compute_rough). Đáp án D02 chưa có người kiểm: mọi sai lệch
là đối chứng với nguồn CHƯA XÁC NHẬN, mẫu số chỉ dự kiến. Quy tắc ánh xạ và các bảng: docs/C01_DUONG_CO_SO_BUILD.md.
File --out luôn bị ghi đè bởi lần chạy này (kể cả khi không có hồ sơ chạy được).
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_rough import rough_for_case, summarize  # noqa: E402
from report_labels import SHEETS, SCOPE, display  # noqa: E402
from optimat.data_check import (CASES_FILE, D02_DIR, EXACT_UNITS, _num_or_none, _rows, check_answer_set,  # noqa: E402
                                denominator_ids, select_cases)
from optimat.db.session import get_database_url  # noqa: E402
from optimat.rough.models import WORKS  # noqa: E402

LABEL = "PHÁT TRIỂN / ĐỐI CHỨNG BUILD — nguồn đối chứng chưa được người kiểm xác nhận, không phải độ chính xác nghiệm thu"
# Hạng mục M01 mà công tác hệ thống (WORKS) đang tính; lá đáp án có PT ngoài bảng này không cùng phạm vi với tổng hệ thống
PT_WORK = {"PT01": "DAO_DAT", "PT02": "DAP_DAT", "PT04": "BE_TONG_LOT", "PT05": "BE_TONG_LOT", "PT06": "MONG", "PT10": "DAM",
           "PT12": "COT", "PT13": "DAM", "PT14": "GIANG_TUONG", "PT16": "LANH_TO", "PT17": "SAN", "PT19": "CAU_THANG",
           "PT23": "MAI", "PT27": "SE_NO", "PT32": "XAY", "PT33": "TRAT", "PT35": "CAN_NEN", "PT36": "CHONG_THAM",
           "PT37": "CHONG_THAM"}
# nhóm mà số hệ thống dựa trên thông số nhập trong file thong_so của hồ sơ (không đọc từ bản vẽ)
PARAM_DEPENDS = {"MONG": "foundations", "COP_PHA/MONG": "foundations", "BE_TONG_LOT": "foundations", "COT_THEP": "steel_kg_per_m3"}


def _key(code: str, elem: str) -> str:
    return f"{code}/{elem}" if elem else code


def leaf_key(row: dict) -> tuple[str | None, str]:
    """Khóa công tác hệ thống của một lá đáp án IN, hoặc (None, lý do không cùng phạm vi)."""
    code, pt = row["ma_cong_tac"], row["ma_pt"]
    if not code:
        return None, "chưa ánh xạ mã công tác"
    if code == "COT_THEP":
        return (_key(code, row["cau_kien"]), "") if pt == "PT40" and row["cau_kien"] else (None, "thép không theo hàm lượng cấu kiện")
    if pt not in PT_WORK:
        return None, f"{pt or 'chưa có PTxx'}: hệ thống chưa có công tác cùng phạm vi"
    if code == "COP_PHA":
        return _key(code, PT_WORK[pt]), ""
    if code != PT_WORK[pt]:
        return None, f"cặp {pt}/{code} không tương thích"
    return code, ""


def system_totals(sys_works) -> dict[str, dict]:
    """Tổng hệ thống theo khóa: phần đã biết, đủ/không đủ, trạng thái xấu nhất, lý do thiếu."""
    from optimat.rough.models import worst_status
    out: dict[str, dict] = {}
    for w in sys_works:
        elem = w.formwork_of if w.code == "COP_PHA" else w.steel_element if w.code == "COT_THEP" else ""
        g = out.setdefault(_key(w.code, elem or ""), {"q": [], "status": [], "missing": [], "n": 0})
        g["n"] += 1
        g["q"].append(w.quantity)
        g["status"].append(w.status)
        g["missing"] += [m for m in w.missing if m not in g["missing"]]
    for g in out.values():
        known = [x for x in g["q"] if x is not None]
        g.update(known=round(sum(known), 3) if known else None, complete=len(known) == g["n"] and not g["missing"] and "D" not in g["status"], worst=worst_status(*g["status"]))
    return out


def build_report(works: list[dict], hm: list[dict], mats: list[dict], sys_works, sys_materials, case: dict,
                 param_keys: frozenset = frozenset()) -> dict[str, pd.DataFrame]:
    """Bảng đối chiếu một hồ sơ. works/hm/mats: CSV D02; sys_*: kết quả compute_rough. Không cộng cha với con: mỗi lá
    (dòng gốc không tách, hoặc dòng con `phan`) góp đúng một lần; so ở mức nhóm khóa công tác, không gán lại cho từng dòng."""
    kids: dict[str, list[dict]] = {}
    for r in works:
        if r["cha_id"]:
            kids.setdefault(r["cha_id"], []).append(r)
    roots = [r for r in works if not r["cha_id"]]
    sys_by = system_totals(sys_works)
    leaves, rows = [], []
    for r in roots:
        parts = [k for k in kids.get(r["id"], []) if k["quan_he_cha"] == "phan"]
        units = parts or [r]
        used, excluded = [], []
        for u in units:
            if u["pham_vi"] != "IN":
                excluded.append(f"{u['id']}: {SCOPE.get(u['pham_vi'], u['pham_vi'])}")
                continue
            key, why = leaf_key(u)
            q = _num_or_none(u["khoi_luong"])
            if key is None or q is None or u["don_vi"] != WORKS.get(key.split("/")[0], ("", ""))[1]:
                excluded.append(f"{u['id']}: {why or ('chưa có số' if q is None else 'khác đơn vị')}")
                continue
            used.append(u["id"])
            # dòng gốc đủ phần con thì dùng số gốc (nguồn), không thay bằng tổng con
            leaves.append({"key": key, "id": u["id"], "goc": r["id"], "q": q, "don_vi": u["don_vi"]})
        mine = [x for x in leaves if x["goc"] == r["id"]]
        if parts and not excluded and len({x["key"] for x in mine}) == 1 and _num_or_none(r["khoi_luong"]) is not None:
            # mọi phần cùng một nhóm: dùng số gốc của nguồn (không thay bằng tổng con khi nguồn tự lệch, vd. 46 dòng 28)
            leaves[-len(mine):] = [dict(mine[0], id=r["id"], q=_num_or_none(r["khoi_luong"]))]
        keys = sorted({lf["key"] for lf in leaves if lf["goc"] == r["id"]})
        if r["pham_vi"] == "OUT":
            state = "ngoai_pham_vi"
        elif r["dem_mau_so"] == "cho_phan_loai":
            state = "cho_phan_loai"
        elif not used:
            state = "chua_anh_xa" if not r["ma_cong_tac"] else "khong_cung_pham_vi_he_thong"
        else:
            sys_states = [sys_by.get(k) for k in keys]
            state = ("he_thong_khong_co_dong" if all(s is None for s in sys_states) else
                     "thieu_dau_vao" if all(s is None or s["known"] is None for s in sys_states) else
                     "mot_phan" if excluded or any(s is None or not s["complete"] for s in sys_states) else
                     "co_ket_qua_chua_xac_nhan")
        rows.append({"id": r["id"], "dong_goc": r["dong_goc"], "noi_dung": r["noi_dung"], "ma_pt": r["ma_pt"],
                     "pham_vi": r["pham_vi"], "dem_mau_so": r["dem_mau_so"], "ma_cong_tac": r["ma_cong_tac"],
                     "khoi_luong_doi_chung": _num_or_none(r["khoi_luong"]), "don_vi": r["don_vi"], "nhom_so_sanh": "; ".join(keys),
                     "phan_dua_vao_so": "; ".join(used), "phan_khong_so": "; ".join(excluded), "trang_thai_de_xuat": state,
                     "trang_thai_kiem": r["trang_thai_kiem"], "can_kiem": r["can_kiem"]})
    lines = pd.DataFrame(rows)

    groups = []
    ref_keys = {lf["key"] for lf in leaves}
    for key in sorted(ref_keys | set(sys_by)):
        mine = [lf for lf in leaves if lf["key"] == key]
        s = sys_by.get(key)
        ref = round(sum(lf["q"] for lf in mine if lf["q"] is not None), 3) if mine else None
        code = key.split("/")[0]
        dep = PARAM_DEPENDS.get(key) or PARAM_DEPENDS.get(code)
        why = ("hệ thống có, đối chứng không có dòng cùng phạm vi (thừa hoặc nguồn thiếu)" if not mine else
               "hệ thống không sinh dòng" if s is None else
               "hệ thống chưa có số" if s["known"] is None else
               "hệ thống chỉ tính một phần (" + "; ".join(s["missing"][:3]) + ")" if not s["complete"] else "")
        so = not why
        lech = None if not so else round(s["known"] - ref, 3)
        groups.append({"bo": case["ten"], "split": case["split"], "nhom": key, "ma_cong_tac": code, "ten": WORKS[code][0],
                       "don_vi": WORKS[code][1], "dong_doi_chung": "; ".join(sorted({lf["goc"] for lf in mine})),
                       "doi_chung": ref, "he_thong": s["known"] if s else None, "he_thong_du": s["complete"] if s else None,
                       "status": s["worst"] if s else None, "so_duoc": so, "ly_do_khong_so": why, "chenh": lech,
                       "lech_pct": round(lech / ref * 100, 1) if so and ref else None,
                       "ghi_chu": "; ".join(x for x in (
                           "đáp án 0: % không xác định" if so and not ref else "",
                           "thép theo hàm lượng: chỉ phản ánh thể tích bê tông" if code == "COT_THEP" else "",
                           f"số hệ thống dựa trên {dep} trong file thông số: nếu thông số lấy từ chính nguồn đối chứng thì khớp "
                           "không chứng minh độ chính xác" if dep in param_keys else "") if x)})
    grp = pd.DataFrame(groups)
    summary, by_status = summarize(grp.assign(lech_pct=grp.lech_pct.where(grp.so_duoc)))
    inventory = []
    for h in hm:
        linked = [r for r in works if r.get("hang_muc_id") == h["id"] or r.get("ma_pt") == h["ma_pt"]]
        inventory.append({**h, "dong_dap_an": "; ".join(r["id"] for r in linked),
                          "tinh_trang_doi_chieu": "chua_xac_dinh_ton_tai" if h["ton_tai"] == "chua_ro" else
                          "khong_ton_tai_theo_so" if h["ton_tai"] == "khong" else
                          "chua_co_dong_dap_an" if not linked else "co_dong_dap_an_chua_xac_nhan"})
    return {"So_hang_muc": pd.DataFrame(inventory), "Doi_chieu_cong_tac": lines, "So_sanh_nhom": grp, "Theo_trang_thai": by_status.assign(tong_nhom=summary.cong_tac.iloc[0]),
            "Vat_tu_nhom": material_table(mats, sys_materials, works)}


def material_table(mats: list[dict], sys_materials, works=()) -> pd.DataFrame:
    """Vật tư D02 cạnh vật tư hệ thống cùng mã. Chỉ so dòng mua dùng được làm đối chứng, cùng đại lượng sau đổi đơn vị
    chính xác, với lượng có hao hụt của hệ thống; lắp đặt, nhóm Ø chưa rõ, tổng lẫn hoàn thiện: giữ dòng, ghi lý do."""
    by_id = {m.material_id: m for m in sys_materials if m.material_id}
    out = []
    refs = {r["id"]: r for r in works}
    for r in mats:
        m = by_id.get(r["material_id"]) if r["material_id"] else None
        unit = (m.unit or "").replace("m3", "m³").replace("m2", "m²") if m else ""
        factor = 1.0 if m and unit == r["don_vi"] else EXACT_UNITS.get((unit, r["don_vi"])) if m else None
        sys_q = m.quantity_with_waste if m else None
        why = ("không dùng làm đáp án: " + r["thieu"] if r["dung_lam_dap_an"] == "khong" else
               "cơ sở lắp đặt: hệ thống không xuất lượng lắp đặt riêng theo quy cách" if r["co_so_luong"] == "lap_dat" else
               "chưa có mã danh mục để ghép" if not r["material_id"] else
               "hệ thống không có vật tư này" if m is None else
               f"khác đại lượng ({unit} ↔ {r['don_vi']})" if factor is None else
               "hệ thống chưa có lượng có hao hụt" if sys_q is None else
               "hệ thống chỉ tính một phần (" + ("; ".join(m.missing[:3]) or "có công tác chưa có khối lượng") + ")" if not m.complete else "")
        ids = [x.strip() for x in r.get("cong_tac_id", "").split(";") if x.strip()]
        linked = [refs[x] for x in ids if x in refs]
        ref_codes = {x["ma_cong_tac"] for x in linked}
        sys_codes = {u.work for u in m.uses} if m else set()
        if not why:
            if (not ids or len(linked) != len(ids) or any(x["pham_vi"] != "IN" for x in linked)
                    or not sys_codes or ref_codes != sys_codes):
                why = "chưa chứng minh cùng phạm vi công tác nguồn và uses hệ thống"
            else:
                why = "chưa có căn cứ đối chiếu lượng mua theo cùng chi tiết cấu kiện và hao hụt"
        ref = _num_or_none(r["luong"])
        so = not why and ref is not None
        val = round(sys_q * factor, 3) if sys_q is not None and factor is not None else None
        out.append({"id": r["id"], "material_id": r["material_id"], "quy_cach": r["quy_cach"], "don_vi": r["don_vi"],
                    "co_so_luong": r["co_so_luong"], "dung_lam_dap_an": r["dung_lam_dap_an"], "doi_chung": ref,
                    "he_thong_co_hao_hut": val, "he_thong_don_vi_goc": unit, "so_duoc": so, "ly_do_khong_so": why,
                    "chenh": round(val - ref, 3) if so else None,
                    "lech_pct": round((val - ref) / ref * 100, 1) if so and ref else None,
                    "nhan": "đối chứng tạm (chờ kiểm tra)" if so else ""})
    return pd.DataFrame(out)


def system_material_table(sys_materials, groups, classes) -> pd.DataFrame:
    rows = [{"loai_bang": "vat_tu", "ma": m.material_id or "", "ten": m.name, "don_vi": m.unit, "quantity": m.quantity,
             "quantity_with_waste": m.quantity_with_waste, "complete": m.complete, "status": m.status, "nhom": m.group_id,
             "loai": m.raw_class, "tu_cong_tac": ", ".join(sorted({u.work for u in m.uses})), "missing": "; ".join(m.missing)}
            for m in sys_materials]
    rows += [{"loai_bang": f"theo_{kind}", "ma": g.group_id, "ten": g.name, "don_vi": "kg", "quantity": g.weight_kg,
              "complete": g.weight_complete, "status": g.status, "missing": "" if g.weight_complete else "có dòng chưa có khối lượng riêng (kg)"}
             for kind, gs in (("nhom", groups), ("loai", classes)) for g in gs]
    return pd.DataFrame(rows)


def file_hashes(paths: list[Path]) -> pd.DataFrame:
    return pd.DataFrame([{"file": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "",
                          "co_file": p.is_file()} for p in paths])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cases", default=str(CASES_FILE))
    ap.add_argument("--out", default=str(ROOT / "reports/c01_duong_co_so_build.xlsx"))
    a = ap.parse_args()
    cases, skipped = select_cases("phat_trien", a.cases, ROOT)
    sheets: dict[str, list[pd.DataFrame]] = {}
    state, notes, hashes = [], [], []
    catalog = None
    for c in cases:
        folder = D02_DIR / c["ten"]
        if not folder.is_dir():
            skipped.append((c["ten"], "chưa có bộ đáp án D02"))
            continue
        found = check_answer_set(folder, a.cases, ROOT)
        if any(f.level == "error" for f in found):
            skipped.append((c["ten"], "bộ D02 có lỗi validator: " + "; ".join(f.message for f in found if f.level == "error")[:300]))
            continue
        hm, works, mats = (_rows(folder / n)[1] for n in ("so_hang_muc.csv", "dap_an_cong_tac.csv", "dap_an_vat_tu.csv"))
        try:
            if catalog is None:
                from optimat.catalog.repository import Catalog
                catalog = Catalog.load()
            res = rough_for_case(c, catalog)
        except Exception as exc:          # bản vẽ hỏng/không đọc được: báo thiếu, không giữ số cũ
            skipped.append((c["ten"], f"không tính được: {type(exc).__name__}: {exc}"))
            continue
        keys = frozenset(json.loads((ROOT / c["thong_so"]).read_text(encoding="utf-8"))) if c.get("thong_so") else frozenset()
        for name, t in build_report(works, hm, mats, res.works, res.materials, c, keys).items():
            sheets.setdefault(name, []).append(t.assign(bo=c["ten"]))
        sheets.setdefault("He_thong_vat_tu", []).append(system_material_table(res.materials, res.by_group, res.by_class).assign(bo=c["ten"]))
        roots = [r for r in works if not r["cha_id"]]
        lines = sheets["Doi_chieu_cong_tac"][-1]
        cov = {"bo": c["ten"], "dong_goc": len(roots), "dong_con": len(works) - len(roots),
               "mau_so_du_kien": len(denominator_ids(works)), "da_kiem": sum(r["trang_thai_kiem"] == "da_kiem" for r in works)}
        cov.update({f"pham_vi_{k}": int(v) for k, v in lines.pham_vi.value_counts().items()})
        cov.update({f"trang_thai_{k}": int(v) for k, v in lines.trang_thai_de_xuat.value_counts().items()})
        cov.update(hang_muc_chua_ro=sum(h["ton_tai"] == "chua_ro" for h in hm), nhom_so_duoc=int(sheets["So_sanh_nhom"][-1].so_duoc.sum()),
                   nhom_tong=len(sheets["So_sanh_nhom"][-1]))
        sheets.setdefault("Bao_phu", []).append(pd.DataFrame([cov]))
        notes += [{"bo": c["ten"], "nguon": "D02 cần kiểm tra", "id": r["id"], "noi_dung": r["can_kiem"]} for r in works if r["can_kiem"]]
        notes += [{"bo": c["ten"], "nguon": "validator D02", "id": f.item, "noi_dung": f.message} for f in found]
        notes += [{"bo": c["ten"], "nguon": "cảnh báo hệ thống", "id": "", "noi_dung": w} for w in res.warnings]
        state.append({"bo": c["ten"], "data_kind": c["data_kind"], "split": c["split"], "dap_an": "D02 nháp, 0 dòng đã kiểm tra" if not cov["da_kiem"] else f"{cov['da_kiem']} dòng đã kiểm tra",
                      "ket_qua": "có số đối chứng"})
        hashes += [ROOT / c[k] for k in ("du_toan", "kien_truc", "ket_cau", "thong_so") if c.get(k)] + sorted(folder.glob("*.csv"))
    code = [ROOT / "scripts/c01_duong_co_so.py", ROOT / "scripts/evaluate_rough.py", ROOT / "src/optimat/data_check.py",
            Path(a.cases)] + sorted((ROOT / "src/optimat/rough").glob("*.py")) + sorted((ROOT / "data/rules").glob("*.csv"))         + sorted((ROOT / "data/catalog").glob("*.csv"))
    head = pd.DataFrame([{"muc_dich": LABEL, "thoi_diem": datetime.now().isoformat(timespec="seconds"),
                          "nguon_danh_muc": "postgresql" if get_database_url() else "csv",
                          "ho_so_chay": len(state), "ho_so_bo_qua": len(skipped),
                          "ket_qua": "có số đối chứng build" if state else "không có hồ sơ chạy được"}])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(a.out) as xw:      # luôn ghi đè: không giữ số của lần trước
        display(head).to_excel(xw, sheet_name=SHEETS["Trang_thai"], index=False)
        display(pd.DataFrame(state)).to_excel(xw, sheet_name=SHEETS["Trang_thai"], index=False, startrow=3)
        for name in ("Bao_phu", "So_hang_muc", "Doi_chieu_cong_tac", "So_sanh_nhom", "Theo_trang_thai", "Vat_tu_nhom", "He_thong_vat_tu"):
            if name in sheets:
                display(pd.concat(sheets[name], ignore_index=True)).to_excel(xw, sheet_name=SHEETS[name], index=False)
        display(pd.DataFrame(notes, columns=["bo", "nguon", "id", "noi_dung"])).to_excel(xw, sheet_name=SHEETS["Can_kiem"], index=False)
        display(pd.DataFrame(skipped, columns=["bo", "ly_do"])).to_excel(xw, sheet_name=SHEETS["Bo_qua"], index=False)
        display(file_hashes(code + hashes)).to_excel(xw, sheet_name=SHEETS["Hash"], index=False)
    print(f"{LABEL}\nchạy {len(state)} hồ sơ, bỏ qua {len(skipped)}; đã ghi {a.out}")
    for ten, why in skipped:
        print(f"  bỏ qua {ten}: {why}")


if __name__ == "__main__":
    main()
