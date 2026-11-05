"""Chạy bù phiên bản 1 cho các tệp cũ chưa có dòng trong project_document_revisions (migration đợt 0).

    python scripts/backfill_document_revisions.py                      # chạy thử: chỉ đọc, ghi CSV đề xuất
    python scripts/backfill_document_revisions.py --apply duyet.csv    # ghi các dòng có duyet=1

Vai trò (KT, KC, HO_SO, TIEN_LUONG, THAM_KHAO) không tự quyết: script chỉ đề xuất theo tên tệp, ghi quy tắc đã
dùng, người kiểm sửa cột role và đặt duyet=1. Tệp không còn trên đĩa thì không có băm, không ghi được.
Cần chạy sau migration_dot0_20261104.sql (project_document_revisions có cột project_id).
"""
import argparse
import csv
import hashlib
import os
import re
import sys
import unicodedata
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"KT", "KC", "HO_SO", "TIEN_LUONG", "THAM_KHAO"}
# (mẫu trên tên đã bỏ dấu, viết hoa) -> vai trò đề xuất. Quy tắc đầu khớp thắng.
RULES = [
    (r"KET ?CAU|\bKC\b|MONG", "KC"),
    (r"KIEN ?TRUC|\bKT\b|THIET KE KIEN", "KT"),
    (r"DIEN|NUOC|BIEN PHAP|PCCC", "THAM_KHAO"),   # ngoài phạm vi phần thô
    (r"DU TOAN|TIEN LUONG|KHOI LUONG|BOQ", "TIEN_LUONG"),
]
FIELDS = ["file_id", "project_id", "filename", "file_type", "stored_path", "ton_tai", "sha256", "size_bytes", "role", "quy_tac", "duyet"]


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper()


def propose_role(filename: str) -> tuple[str, str]:
    name = _plain(filename)
    for pattern, role in RULES:
        if re.search(pattern, name):
            return role, pattern
    return "", "không khớp quy tắc nào"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _engine():
    url = os.environ.get("DATABASE_URL")
    if not url and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf8").splitlines():
            m = re.match(r'\s*DATABASE_URL\s*=\s*"?([^"\s#]+)', line)
            if m:
                url = m.group(1)
    if not url:
        sys.exit("Chưa có DATABASE_URL.")
    return create_engine(url)


def dry_run(out: Path) -> None:
    eng = _engine()
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        rows = c.execute(text("""SELECT f.file_id, f.project_id, f.filename, f.file_type, f.stored_path FROM project_files f
                                 WHERE NOT EXISTS (SELECT 1 FROM project_document_revisions r WHERE r.file_id = f.file_id)
                                 ORDER BY f.file_id""")).mappings().all()
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for r in rows:
            p = Path(r["stored_path"])
            p = p if p.is_absolute() else ROOT / p
            exists = p.is_file()
            role, rule = propose_role(r["filename"])
            w.writerow({**r, "ton_tai": int(exists), "sha256": _sha256(p) if exists else "",
                        "size_bytes": p.stat().st_size if exists else "", "role": role, "quy_tac": rule, "duyet": 0})
    missing = sum(1 for r in rows if not (Path(r["stored_path"]) if Path(r["stored_path"]).is_absolute() else ROOT / r["stored_path"]).is_file())
    print(f"{len(rows)} tệp chưa có phiên bản; {missing} tệp không còn trên đĩa. Đề xuất ghi tại {out}. "
          "Sửa cột role, đặt duyet=1 rồi chạy --apply.")


def apply(path: Path) -> None:
    with path.open(encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["duyet"].strip() == "1"]
    bad = [r["file_id"] for r in rows if r["role"] not in ROLES or len(r["sha256"]) != 64 or not r["size_bytes"]]
    if bad:
        sys.exit(f"Dòng duyệt thiếu vai trò hợp lệ hoặc băm/dung lượng: file_id {', '.join(bad)}. Không ghi gì.")
    eng = _engine()
    with eng.begin() as c:  # một giao dịch: lỗi một dòng thì không ghi dòng nào
        for r in rows:
            p = Path(r["stored_path"])
            p = p if p.is_absolute() else ROOT / p
            if not p.is_file() or _sha256(p) != r["sha256"]:
                raise SystemExit(f"Tệp {r['file_id']} đã đổi hoặc mất từ lúc chạy thử. Chạy thử lại.")
            c.execute(text("""INSERT INTO project_document_revisions (project_id, file_id, version, sha256, stored_path, size_bytes, format, role)
                              VALUES (:project_id, :file_id, 1, :sha256, :stored_path, :size_bytes, :file_type, :role)"""),
                      {k: r[k] for k in ("project_id", "file_id", "sha256", "stored_path", "size_bytes", "file_type", "role")})
    print(f"Đã ghi {len(rows)} phiên bản.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", type=Path, help="CSV đã duyệt")
    ap.add_argument("--out", type=Path, default=ROOT / "reports" / "backfill_revisions_de_xuat.csv")
    a = ap.parse_args()
    if a.apply:
        apply(a.apply)
    else:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        dry_run(a.out)
