"""Tiếp nhận hồ sơ CAD (S02): kiểm tra file tải lên, lưu theo hash kèm phiên bản, chuyển DWG sang DXF có ghi log,
rồi kiểm kê đối tượng CAD (layer, block, layout, đơn vị, khung bao, số entity) kèm nguồn từng đối tượng.

Bản kiểm kê chỉ mô tả bản vẽ. Không suy ra khối lượng từ khung bao: khung bao chỉ dùng để phát hiện sai đơn vị/tỷ lệ.
File DWG chuyển đổi thất bại cho status "failed", takeoff_allowed = False và không có entity nào, để không bao giờ
sinh kết quả bóc tách giả từ một bản vẽ không đọc được.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import ezdxf
from ezdxf import bbox, recover, units
from ezdxf.fonts import fonts as fonts_mod

from .. import config
from . import dwg_convert
from .dwg_convert import DrawingError
from .dxf_reader import declared_insunits
from .encoding import detect_encoding

ALLOWED_EXT = {".dxf", ".dwg"}
# Trình duyệt và hệ điều hành gửi MIME rất khác nhau cho file CAD: chỉ chặn MIME rõ ràng sai, nội dung mới là căn cứ chính.
ALLOWED_MIME = {"", "application/octet-stream", "application/acad", "application/x-acad", "application/autocad_dwg",
                "image/vnd.dwg", "image/x-dwg", "application/dwg", "application/x-dwg", "application/dxf",
                "application/x-dxf", "image/vnd.dxf", "image/x-dxf", "text/plain", "text/x-dxf"}
MAX_UPLOAD_MB = config.MAX_UPLOAD_MB
# Đối tượng S02 cam kết đọc; loại khác vẫn được đếm nhưng gắn cảnh báo "chưa hỗ trợ"
SUPPORTED = {"INSERT", "LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "HATCH", "TEXT", "MTEXT", "DIMENSION",
             "ATTDEF", "VIEWPORT"}
DWG_VERSIONS = {"AC1009": "R12", "AC1012": "R13", "AC1014": "R14", "AC1015": "2000", "AC1018": "2004",
                "AC1021": "2007", "AC1024": "2010", "AC1027": "2013", "AC1032": "2018"}
# Mặt bằng nhà ở thật (mm) nằm trong khoảng này; ngoài khoảng thường là vẽ sai đơn vị hoặc không theo tỷ lệ 1:1
PLAUSIBLE_EXTENT_MM = (1_000.0, 1_000_000.0)
BLOCKING = {"EMPTY_MODEL", "CONVERSION_FAILED", "INVALID_FILE"}


_MANIFEST_LOCK = threading.Lock()


class UploadRejected(DrawingError):
    """File tải lên sai đuôi, sai nội dung, rỗng hoặc quá lớn."""


def sniff(data: bytes) -> str | None:
    """Nhận dạng theo nội dung: 'dwg', 'dxf' hoặc None. Không tin đuôi file."""
    if re.match(rb"AC10\d\d", data[:6]) or data[:6] in (b"AC1.40", b"AC1.50", b"AC2.10"):
        return "dwg"
    if data.startswith(b"AutoCAD Binary DXF"):
        return "dxf"
    lines = data[:4096].decode("latin-1").lstrip("﻿\xef\xbb\xbf").split("\n")
    lines = [s.strip() for s in lines]
    while len(lines) >= 2 and lines[0] == "999":   # dòng chú thích ở đầu file
        lines = lines[2:]
    return "dxf" if len(lines) >= 2 and lines[0] == "0" and lines[1] == "SECTION" else None


def check_upload(name: str, data: bytes, mime: str | None = None, max_mb: float = MAX_UPLOAD_MB) -> dict:
    """Kiểm tra một file tải lên, trả về thông tin file (đuôi, hash, phiên bản định dạng). Sai thì UploadRejected."""
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise UploadRejected(f"{name}: định dạng {ext or '(không có đuôi)'} không được nhận. Chỉ nhận .dxf và .dwg.")
    mime = (mime or "").split(";")[0].strip().lower()
    if mime not in ALLOWED_MIME:
        raise UploadRejected(f"{name}: kiểu MIME {mime} không phải file CAD.")
    if not data:
        raise UploadRejected(f"{name}: file rỗng.")
    if len(data) > max_mb * 1024 * 1024:
        raise UploadRejected(f"{name}: dung lượng {len(data) / 1048576:.1f} MB vượt giới hạn {max_mb:g} MB.")
    kind = sniff(data)
    if kind != ext[1:]:
        raise UploadRejected(f"{name}: nội dung không phải file {ext} hợp lệ"
                             + (f" (nội dung là {kind.upper()})" if kind else "") + ".")
    code = data[:6].decode("latin-1") if kind == "dwg" else None
    return {"name": name, "ext": ext, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "dwg_version": code and DWG_VERSIONS.get(code, code)}


def store_upload(info: dict, data: bytes, store_dir: Path) -> dict:
    """Lưu file theo hash (trùng nội dung thì không lưu lại) và đánh số phiên bản theo tên file.

    Sổ ghi manifest.jsonl: mỗi dòng một lần tải lên có nội dung mới. Cùng tên, nội dung khác thì phiên bản tăng 1."""
    # shortcut: khóa chỉ có hiệu lực trong một tiến trình; chạy nhiều worker uvicorn thì chuyển manifest vào PostgreSQL
    with _MANIFEST_LOCK:   # đọc - cấp số - ghi phải liền một khối, không thì hai request cùng nhận một phiên bản
        store_dir.mkdir(parents=True, exist_ok=True)
        manifest = store_dir / "manifest.jsonl"
        rows = [json.loads(s) for s in manifest.read_text(encoding="utf-8").splitlines() if s] if manifest.exists() else []
        same = [r for r in rows if r["name"] == info["name"]]
        for r in same:
            if r["sha256"] == info["sha256"]:
                return {**info, "version": r["version"], "stored_as": r["stored_as"], "duplicate": True}
        stored = store_dir / f"{info['sha256']}{info['ext']}"
        if not stored.exists():
            stored.write_bytes(data)
        row = {"name": info["name"], "sha256": info["sha256"], "size": info["size"], "stored_as": stored.name,
               "version": max((r["version"] for r in same), default=0) + 1,
               "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with manifest.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {**info, "version": row["version"], "stored_as": stored.name, "duplicate": False}


def _warn(out: list, code: str, message: str) -> None:
    out.append({"code": code, "message": message})


def _converter_version(path: str | None) -> str | None:
    m = re.search(r"(\d+\.\d+(?:\.\d+)?)", str(Path(path).parent.name)) if path else None
    return m and m.group(1)


def convert_with_log(dwg_path: str, out_dir: str) -> tuple[str | None, dict]:
    """Chuyển DWG sang DXF, trả về (đường dẫn DXF hoặc None, log chuyển đổi). Không ném lỗi chuyển đổi."""
    converter = dwg_convert.find_converter()
    log = {"converter": converter, "converter_version": _converter_version(converter),
           "target_version": dwg_convert._OUTPUT_DXF_VERSION, "ok": False, "error": None, "seconds": None}
    t0 = time.perf_counter()
    try:
        dxf = dwg_convert.convert_dwg_to_dxf(dwg_path, out_dir)
        log["ok"] = True
        return dxf, log
    except DrawingError as exc:
        log["error"] = str(exc)
        return None, log
    finally:
        log["seconds"] = round(time.perf_counter() - t0, 2)


def _dim_mismatch(dims, scale: float) -> int:
    """Kích thước ghi đè chữ số khác giá trị đo thật (đã đổi mm) quá 2 %: dấu hiệu bản vẽ không theo tỷ lệ 1:1."""
    bad = 0
    for d in dims:
        txt, meas = d.dxf.get("text", ""), d.dxf.get("actual_measurement")
        if meas is None:
            try:
                meas = d.get_measurement()
            except Exception:                           # noqa: BLE001 - loại kích thước ezdxf không tự đo được
                continue
            meas = meas if isinstance(meas, (int, float)) else None
        m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*", txt or "")
        if m and meas:
            shown = float(m.group(1).replace(",", "."))
            if shown and abs(shown - meas * scale) > 0.02 * shown:
                bad += 1
    return bad


def inventory_dxf(path: str, source: dict | None = None) -> dict:
    """Kiểm kê một file DXF. source: thông tin file gốc (tên, hash, phiên bản) ghi vào từng entity làm nguồn."""
    source = source or {"name": Path(path).name}
    warnings: list[dict] = []
    try:
        doc = ezdxf.readfile(path)
        auditor = doc.audit()
    except ezdxf.DXFStructureError:
        try:   # file hỏng cấu trúc: đọc chậm hơn bằng chế độ phục hồi
            doc, auditor = recover.readfile(path)
            _warn(warnings, "RECOVERED", "File DXF hỏng cấu trúc, đã đọc bằng chế độ phục hồi; kết quả cần kiểm tra lại.")
        except (ezdxf.DXFStructureError, OSError) as exc:
            _warn(warnings, "INVALID_FILE", f"Không mở được file DXF: {exc}")
            return _result(source, "failed", warnings)
    except (OSError, UnicodeDecodeError) as exc:
        _warn(warnings, "INVALID_FILE", f"Không mở được file DXF: {exc}")
        return _result(source, "failed", warnings)
    for err in auditor.errors[:20]:
        _warn(warnings, "AUDIT_ERROR", f"Lỗi cấu trúc không tự sửa được: {err.message}")
    if auditor.fixes:
        _warn(warnings, "AUDIT_FIXED", f"ezdxf đã tự sửa {len(auditor.fixes)} lỗi cấu trúc khi đọc; nên kiểm tra lại.")

    insunits = declared_insunits(doc, path)
    try:
        scale = units.conversion_factor(insunits, units.MM) if insunits else 1.0
    except (TypeError, ValueError, KeyError):
        scale = 1.0
        _warn(warnings, "UNKNOWN_UNITS", f"Mã đơn vị $INSUNITS = {insunits} không xác định, đang coi là mm.")
    if insunits == 0:
        _warn(warnings, "NO_UNITS", "Bản vẽ không khai báo đơn vị ($INSUNITS = 0), đang coi là mm.")

    # entity theo layout, kèm nguồn: file, layout, handle, layer
    entities, layouts = [], []
    layer_count, type_count = Counter(), Counter()
    msp = doc.modelspace()
    for layout in doc.layouts:
        counts = Counter(e.dxftype() for e in layout)
        layouts.append({"name": layout.name, "is_model": layout.is_modelspace, "entities": sum(counts.values()),
                        "counts": dict(counts)})
        for e in layout:
            layer = e.dxf.get("layer", "0")
            entities.append({"file": source.get("name"), "sha256": source.get("sha256"), "layout": layout.name,
                             "handle": e.dxf.handle, "type": e.dxftype(), "layer": layer,
                             "block": e.dxf.name if e.dxftype() == "INSERT" else None})
            if layout.is_modelspace:
                layer_count[layer] += 1
                type_count[e.dxftype()] += 1
    paper = [lo for lo in layouts if not lo["is_model"] and lo["entities"] > lo["counts"].get("VIEWPORT", 0)]
    if not type_count:
        _warn(warnings, "EMPTY_MODEL", "Modelspace không có đối tượng nào"
              + (f"; nội dung nằm ở layout {', '.join(lo['name'] for lo in paper)}." if paper else "."))
    if paper:
        _warn(warnings, "MULTI_LAYOUT", f"Bản vẽ có {len(paper)} layout giấy có nội dung ("
              + ", ".join(lo["name"] for lo in paper) + "); chỉ modelspace được dùng để bóc tách.")

    unsupported = {t: n for t, n in type_count.items() if t not in SUPPORTED}
    if unsupported:
        _warn(warnings, "UNSUPPORTED_ENTITY", "Đối tượng chưa hỗ trợ (đã đếm, không đọc hình): "
              + ", ".join(f"{t} ×{n}" for t, n in sorted(unsupported.items())))

    # khung bao modelspace (mm); đối tượng nào làm hỏng phép tính khung bao thì báo không đọc được
    box, unreadable = bbox.BoundingBox(), Counter()
    cache = bbox.Cache()
    for e in msp:
        try:
            box.extend(bbox.extents([e], cache=cache))
        except Exception:                               # noqa: BLE001 - entity hỏng: đếm và báo, không dừng cả file
            unreadable[e.dxftype()] += 1
    if unreadable:
        _warn(warnings, "UNREADABLE_ENTITY", "Không đọc được hình học: "
              + ", ".join(f"{t} ×{n}" for t, n in unreadable.items()))
    bbox_mm = None
    if box.has_data:
        (x0, y0, _), (x1, y1, _) = box.extmin, box.extmax
        bbox_mm = {"min": [round(x0 * scale, 1), round(y0 * scale, 1)], "max": [round(x1 * scale, 1), round(y1 * scale, 1)],
                   "size": [round((x1 - x0) * scale, 1), round((y1 - y0) * scale, 1)]}
        big = max(bbox_mm["size"])
        if not PLAUSIBLE_EXTENT_MM[0] <= big <= PLAUSIBLE_EXTENT_MM[1]:
            _warn(warnings, "SCALE_SUSPECT", f"Khung bao modelspace {big / 1000:g} m là bất thường với nhà ở; "
                  "có thể sai đơn vị hoặc không vẽ theo tỷ lệ 1:1.")

    dims = msp.query("DIMENSION")
    used = {d.dxf.get("dimstyle", "Standard").lower() for d in dims}    # kiểu kích thước không dùng thì không cảnh báo
    dimlfac = {s.dxf.name: s.dxf.get("dimlfac", 1.0) for s in doc.dimstyles if s.dxf.name.lower() in used}
    off = {k: v for k, v in dimlfac.items() if abs(v - 1.0) > 1e-9}
    if off:
        _warn(warnings, "DIMLFAC", "Hệ số đo kích thước khác 1 (bản vẽ không theo tỷ lệ 1:1 trong modelspace): "
              + ", ".join(f"{k} = {v:g}" for k, v in off.items()))
    bad_dims = _dim_mismatch(dims, scale)
    if bad_dims:
        _warn(warnings, "DIM_TEXT_MISMATCH", f"{bad_dims} kích thước có chữ ghi đè khác số đo thật quá 2 %.")

    blocks = []
    inserts = Counter(e.dxf.name for e in doc.entitydb.values() if e.dxftype() == "INSERT" and e.is_alive)
    for blk in doc.blocks:
        if blk.name.startswith("*") and blk.name.upper().startswith(("*MODEL_SPACE", "*PAPER_SPACE")):
            continue
        head = blk.block
        is_xref = bool(head and (head.is_xref or head.is_xref_overlay))
        blocks.append({"name": blk.name, "inserts": inserts.get(blk.name, 0), "entities": len(blk),
                       "counts": dict(Counter(e.dxftype() for e in blk)), "is_xref": is_xref,
                       "xref_path": head.dxf.get("xref_path") if is_xref else None})
    xrefs = [b for b in blocks if b["is_xref"]]
    if xrefs:
        _warn(warnings, "XREF", "Bản vẽ tham chiếu ngoài (XREF), nội dung không có trong file: "
              + ", ".join(f"{b['name']} ({b['xref_path']})" for b in xrefs))

    fonts = []
    for st in doc.styles:
        font = st.dxf.get("font", "") or ""
        enc = detect_encoding(font)
        fonts.append({"style": st.dxf.name, "font": font, "bigfont": st.dxf.get("bigfont", "") or None, "encoding": enc,
                      "found": bool(font) and fonts_mod.font_manager.has_font(Path(font).name)})
    style_enc = {f["style"].lower(): f["encoding"] for f in fonts}
    used = Counter(e.dxf.get("style", "Standard").lower() for e in msp.query("TEXT MTEXT"))
    vni = {f["style"]: used[f["style"].lower()] for f in fonts if used[f["style"].lower()] and f["encoding"] == "vni"}
    if vni:
        _warn(warnings, "FONT_UNSUPPORTED", "Chữ dùng font VNI chưa chuyển mã được, nội dung ghi chú có thể sai: "
              + ", ".join(f"kiểu {s} ×{n}" for s, n in vni.items()))
    no_font = [f["style"] for f in fonts if not f["font"] and not _is_shape_style(doc, f["style"])]
    if no_font:
        _warn(warnings, "FONT_MISSING", "Kiểu chữ không khai báo font: " + ", ".join(no_font))
    # font có khai báo nhưng máy chủ không có: ezdxf vẽ bằng font thay thế, chữ có thể lệch hoặc mất dấu
    absent = sorted({f["font"] for f in fonts if f["font"] and not f["found"] and used[f["style"].lower()]})
    if absent:
        _warn(warnings, "FONT_NOT_FOUND", "Font không có trên máy chủ, hiển thị bằng font thay thế: " + ", ".join(absent))

    table = {ly.dxf.name for ly in doc.layers}
    layers = [{"name": n, "entities": layer_count.get(n, 0), "in_table": n in table,
               "off": n in table and doc.layers.get(n).is_off(), "frozen": n in table and doc.layers.get(n).is_frozen()}
              for n in sorted(table | set(layer_count))]

    status = "failed" if any(w["code"] in BLOCKING for w in warnings) else "ok"
    return _result(source, status, warnings, dxf_version=doc.dxfversion, acad_release=doc.acad_release,
                   units={"insunits": insunits, "name": units.unit_name(insunits),
                          "scale_to_mm": scale},
                   bbox_mm=bbox_mm, entity_total=sum(type_count.values()), entity_counts=dict(type_count),
                   layers=layers, layouts=layouts, blocks=blocks, fonts=fonts, entities=entities)


def _is_shape_style(doc, style: str) -> bool:
    """Kiểu chữ dùng cho ký hiệu dạng shape (cờ 1) không cần font chữ."""
    s = doc.styles.get(style)
    return bool(s and s.dxf.get("flags", 0) & 1)


def _result(source: dict, status: str, warnings: list, **data) -> dict:
    empty = {"dxf_version": None, "acad_release": None, "units": None, "bbox_mm": None, "entity_total": 0,
             "entity_counts": {}, "layers": [], "layouts": [], "blocks": [], "fonts": [], "entities": []}
    return {"file": source, "status": status, "takeoff_allowed": status == "ok", **empty, **data,
            "conversion": None, "warnings": warnings}


def ingest_file(name: str, data: bytes, mime: str | None = None, store_dir: Path | None = None) -> dict:
    """Toàn bộ luồng cho một file: kiểm tra, lưu (nếu có store_dir), chuyển DWG, kiểm kê. Không ném lỗi người dùng."""
    try:
        info = check_upload(name, data, mime)
    except UploadRejected as exc:
        return _result({"name": name, "size": len(data)}, "rejected", [{"code": "UPLOAD_REJECTED", "message": str(exc)}])
    if store_dir is not None:
        info = store_upload(info, data, store_dir)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{info['ext']}"
        path.write_bytes(data)
        if info["ext"] == ".dxf":
            return inventory_dxf(str(path), info)
        dxf, log = convert_with_log(str(path), tmp)
        if dxf is None:   # không có DXF thì không có entity nào: không bao giờ sinh bóc tách giả
            res = _result(info, "failed", [{"code": "CONVERSION_FAILED", "message": log["error"]}])
        else:
            res = inventory_dxf(dxf, info)
        res["conversion"] = log
        return res
