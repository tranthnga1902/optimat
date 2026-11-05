"""So câu trích bổ sung đơn vị với văn bản hoặc ô bảng gốc, kiểm tra hash nguồn."""
import argparse
import hashlib
import json
import unicodedata
from pathlib import Path


def clean(value):
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("pack", type=Path)
    args = ap.parse_args()
    root, pack = args.source, args.pack
    tables = {t["table_id"]: t for t in map(json.loads, (pack / "tables.jsonl").open(encoding="utf-8"))}
    native = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (root / "02-van-ban-trich-xuat").glob("*.json")}
    evidence = json.loads((pack / "basis_evidence.json").read_text(encoding="utf-8"))
    failures, counts = [], {}
    for row in evidence:
        e = row["evidence"]
        quote, method = clean(e["quote"]), e["method"]
        counts[method] = counts.get(method, 0) + 1
        ok = False
        if method in ("explicit_unit_caption", "same_code_continuation", "explicit_volume_in_recipe_title"):
            ok = quote in clean(tables[e["table_id"]]["context_before"])
        elif method in ("explicit_table_header", "explicit_work_row"):
            ok = quote in clean(tables[e["table_id"]]["grid"][e["grid_row"]][e["grid_column"]])
        elif method == "explicit_work_column":
            cell = clean(tables[e["table_id"]]["grid"][e["grid_row"]][e["grid_column"]])
            ok = quote == cell or (";" in quote and clean(quote.split(";")[-1]) == cell
                                  and clean(quote.split(";")[0]) in clean(tables[e["table_id"]]["context_before"]))
        elif method in ("heading_caption_before_page_break", "explicit_appendix_scope"):
            ok = quote in clean(native[e["source_id"]][e["pdf_page"] - 1]["text"])
        if not ok:
            failures.append({"record_id": row["record_id"], "method": method, "quote": e["quote"]})
    sources = json.loads((pack / "sources.json").read_text(encoding="utf-8"))
    for source in sources:
        if hashlib.sha256((root / source["local_file"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Hash tài liệu gốc không khớp: {source['source_id']}")
    report = {"status": "passed" if not failures else "failed", "checked": len(evidence), "matched": len(evidence) - len(failures),
              "methods": counts, "failures": failures, "source_hashes_checked": len(sources),
              "verification": "So câu trích với trang hoặc ô bảng gốc sau chuẩn hóa NFC và khoảng trắng; không xác nhận toàn bộ hệ số bằng đọc tay."}
    (pack / "evidence_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "verification"}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
